"""OpenTelemetry SDK with a small persistent SQLite inspection backend.

Only allowlisted metadata is stored, never bodies, SQL parameters, URLs, or headers.
"""
import json
import logging
import os
import sqlite3
import threading
import time
from contextvars import ContextVar
from pathlib import Path
from uuid import uuid4

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

logging.basicConfig(level=logging.INFO, format="%(message)s")

request_id_context = ContextVar("request_id", default="")

class TelemetryStore:
    def __init__(self, path):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, kind TEXT NOT NULL, ts REAL NOT NULL, data TEXT NOT NULL)")
        self.connection.commit()

    def add(self, kind, data):
        event = {"timestamp": time.time(), **data, "id": data.get("id", str(uuid4()))}
        with self.lock:
            self.connection.execute("INSERT INTO events VALUES (?, ?, ?, ?)", (str(uuid4()), kind, time.time(), json.dumps(event)))
            self.connection.commit()
        return event

    def rows(self, kind, limit=200):
        with self.lock:
            return [json.loads(row[0]) for row in self.connection.execute("SELECT data FROM events WHERE kind=? ORDER BY ts DESC LIMIT ?", (kind, limit))]

    def close(self):
        self.connection.close()

class PersistentSpanExporter(SpanExporter):
    def __init__(self, store):
        self.store = store

    def export(self, spans):
        for span in spans:
            self.store.add("trace", {
                "trace_id": format(span.context.trace_id, "032x"),
                "span_id": format(span.context.span_id, "016x"),
                "parent_span_id": format(span.parent.span_id, "016x") if span.parent else None,
                "name": span.name, "duration_ms": (span.end_time-span.start_time)/1e6,
                "status": span.status.status_code.name,
                "attributes": dict(span.attributes or {}),
            })
        return SpanExportResult.SUCCESS

class Observability:
    def __init__(self, path=None):
        self.store = TelemetryStore(path or os.getenv("TELEMETRY_DB", "telemetry.db"))
        self.provider = TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(PersistentSpanExporter(self.store)))
        self.tracer = self.provider.get_tracer("kinufaktur.operations", "1.0")

    def log(self, event, **fields):
        context = trace.get_current_span().get_span_context()
        record = self.store.add("log", {"event": event, "trace_id": format(context.trace_id, "032x"), "request_id": request_id_context.get(), **fields})
        logging.getLogger("operations").info(json.dumps(record))
        return record

    def metrics(self):
        with self.store.lock:
            rows = self.store.connection.execute("SELECT data FROM events WHERE kind='request'").fetchall()
            workflows = self.store.connection.execute("SELECT data FROM events WHERE kind='workflow'").fetchall()
        req = [json.loads(row[0]) for row in rows]
        flows = [json.loads(row[0]) for row in workflows]
        errors = sum(r["status_code"] >= 500 for r in req)
        return {"request_count": len(req), "error_count": errors, "error_rate": errors / len(req) if req else 0,
                "average_latency_ms": sum(r["duration_ms"] for r in req)/len(req) if req else 0,
                "workflow_count": len(flows), "failed_workflow_count": sum(r["status"] == "failed" for r in flows)}

# SQL instrumentation records operation category only, excluding statements/parameters.
from sqlalchemy import event
from sqlalchemy.engine import Engine
active_observability = ContextVar("active_observability", default=None)

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(connection, cursor, statement, parameters, context, executemany):
    telemetry = active_observability.get()
    if telemetry:
        operation = statement.lstrip().split(None, 1)[0].upper() if statement.strip() else "UNKNOWN"
        if operation not in {"SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "PRAGMA", "BEGIN", "COMMIT"}:
            operation = "OTHER"
        span = telemetry.tracer.start_span("database." + operation, attributes={"db.operation.name": operation})
        context._operations_span = span

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(connection, cursor, statement, parameters, context, executemany):
    span = getattr(context, "_operations_span", None)
    if span:
        span.end()
        context._operations_span = None

@event.listens_for(Engine, "handle_error")
def database_error(context):
    from opentelemetry.trace import Status, StatusCode
    execution = context.execution_context
    span = getattr(execution, "_operations_span", None)
    if span:
        span.set_status(Status(StatusCode.ERROR))
        span.end()
        execution._operations_span = None
