from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import TaskRecord
from .schemas import Task, TaskCreate, TaskUpdate


class TaskStore(Protocol):
    def list(self) -> list[Task]: ...

    def get(self, task_id: str) -> Task | None: ...

    def create(self, task_input: TaskCreate) -> Task: ...

    def update(self, task_id: str, changes: TaskUpdate) -> Task | None: ...

    def delete(self, task_id: str) -> bool: ...


class SqlAlchemyTaskStore:
    """SQLAlchemy-backed data-access layer for KinuFlow tasks."""

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _to_task(record: TaskRecord) -> Task:
        return Task.model_validate(record)

    def list(self) -> list[Task]:
        statement = select(TaskRecord).order_by(TaskRecord.created_at.desc())
        records = self.session.scalars(statement).all()
        return [self._to_task(record) for record in records]

    def get(self, task_id: str) -> Task | None:
        record = self.session.get(TaskRecord, task_id)
        return self._to_task(record) if record else None

    def create(self, task_input: TaskCreate) -> Task:
        timestamp = datetime.now(timezone.utc)
        record = TaskRecord(
            id=str(uuid4()),
            **task_input.model_dump(mode="json"),
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_task(record)

    def update(self, task_id: str, changes: TaskUpdate) -> Task | None:
        record = self.session.get(TaskRecord, task_id)
        if record is None:
            return None

        for field, value in changes.model_dump(
            mode="json", exclude_unset=True
        ).items():
            setattr(record, field, value)
        record.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(record)
        return self._to_task(record)

    def delete(self, task_id: str) -> bool:
        record = self.session.get(TaskRecord, task_id)
        if record is None:
            return False

        self.session.delete(record)
        self.session.commit()
        return True
