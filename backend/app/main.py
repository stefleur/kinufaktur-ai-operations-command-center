from contextlib import asynccontextmanager
from typing import Annotated
import os
import re
import time
from uuid import uuid4

from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind, Status, StatusCode
from .observability import Observability, request_id_context, active_observability
from .operations import operations_router

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .database import create_tables, get_db
from .schemas import ErrorResponse, Task, TaskCreate, TaskDeleteResponse, TaskUpdate
from .store import SqlAlchemyTaskStore, TaskStore


DatabaseSession = Annotated[Session, Depends(get_db)]


def get_task_store(database: DatabaseSession) -> TaskStore:
    return SqlAlchemyTaskStore(database)


TaskStoreDependency = Annotated[TaskStore, Depends(get_task_store)]


def require_task(task_id: str, store: TaskStore) -> Task:
    task = store.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    return task


def create_app(*, initialize_database: bool = True, telemetry_path=None, dependency=None) -> FastAPI:
    telemetry = Observability(telemetry_path)
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            if initialize_database:
                create_tables()
            yield
        finally:
            telemetry.provider.shutdown()
            telemetry.store.close()

    application = FastAPI(
        title="Kinufaktur AI Operations Command Center API",
        version="1.0.0",
        description="Persistent tasks, workflows, telemetry, impact alerts and bounded on-call response.",
        lifespan=lifespan,
    )

    application.state.telemetry = telemetry
    application.include_router(operations_router(telemetry, dependency))

    @application.middleware("http")
    async def observe_request(request, call_next):
        supplied = request.headers.get("x-request-id", "")
        request_id = supplied if re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", supplied) else str(uuid4())
        token = request_id_context.set(request_id)
        observation_token = active_observability.set(telemetry)
        started = time.perf_counter()
        try:
            with telemetry.tracer.start_as_current_span("http.request", context=extract(dict(request.headers)), kind=SpanKind.SERVER, record_exception=False, set_status_on_exception=False) as span:
                try:
                    response = await call_next(request)
                except Exception:
                    response = JSONResponse(status_code=500, content={"detail": "Service unavailable; inspect operations telemetry."})
                route = getattr(request.scope.get("route"), "path", "unmatched")
                elapsed = (time.perf_counter()-started)*1000
                span.update_name(request.method + " " + route)
                span.set_attribute("http.request.method", request.method)
                span.set_attribute("http.route", route)
                span.set_attribute("http.response.status_code", response.status_code)
                span.set_attribute("request.id", request_id)
                if response.status_code >= 500:
                    span.set_status(Status(StatusCode.ERROR))
                telemetry.log("http_request", method=request.method, route=route, status_code=response.status_code, duration_ms=elapsed)
                context = span.get_span_context()
                telemetry.store.add("request", {"trace_id": format(context.trace_id, "032x"), "request_id": request_id, "route": route, "status_code": response.status_code, "duration_ms": elapsed})
                response.headers["x-request-id"] = request_id
                response.headers["x-trace-id"] = format(context.trace_id, "032x")
                response.headers["traceparent"] = f"00-{context.trace_id:032x}-{context.span_id:016x}-01"
                return response
        finally:
            active_observability.reset(observation_token)
            request_id_context.reset(token)

    # Configure CORS origins via environment variable for deployment.
    # Provide a sensible default for local dev.
    cors_env = os.getenv("KINUFLOW_CORS_ORIGINS")
    if cors_env:
        # Expect a comma-separated list of allowed origins.
        allow_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    else:
        allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["x-request-id", "x-trace-id", "traceparent"],
    )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(_request, _exception):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": "Invalid task data."},
        )

    application.add_api_route(
        "/tasks",
        list_tasks,
        methods=["GET"],
        response_model=list[Task],
        tags=["Tasks"],
        operation_id="listTasks",
    )
    application.add_api_route(
        "/tasks",
        create_task,
        methods=["POST"],
        response_model=Task,
        status_code=status.HTTP_201_CREATED,
        tags=["Tasks"],
        operation_id="createTask",
        responses={
            422: {"model": ErrorResponse, "description": "Invalid task data."},
        },
    )
    application.add_api_route(
        "/tasks/{task_id}",
        get_task,
        methods=["GET"],
        response_model=Task,
        tags=["Tasks"],
        operation_id="getTask",
        responses={
            404: {"model": ErrorResponse, "description": "Task not found."},
        },
    )
    application.add_api_route(
        "/tasks/{task_id}",
        update_task,
        methods=["PATCH"],
        response_model=Task,
        tags=["Tasks"],
        operation_id="updateTask",
        responses={
            404: {"model": ErrorResponse, "description": "Task not found."},
            422: {"model": ErrorResponse, "description": "Invalid task data."},
        },
    )
    application.add_api_route(
        "/tasks/{task_id}",
        delete_task,
        methods=["DELETE"],
        response_model=TaskDeleteResponse,
        tags=["Tasks"],
        operation_id="deleteTask",
        responses={
            404: {"model": ErrorResponse, "description": "Task not found."},
        },
    )
    return application


def list_tasks(store: TaskStoreDependency):
    return store.list()


def create_task(task_input: TaskCreate, store: TaskStoreDependency):
    return store.create(task_input)


def get_task(task_id: str, store: TaskStoreDependency):
    return require_task(task_id, store)


def update_task(task_id: str, changes: TaskUpdate, store: TaskStoreDependency):
    task = store.update(task_id, changes)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    return task


def delete_task(task_id: str, store: TaskStoreDependency):
    if not store.delete(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    return TaskDeleteResponse(id=task_id)


app = create_app()
