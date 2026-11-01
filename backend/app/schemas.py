from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TaskCategory(str, Enum):
    AI_AUTOMATION = "AI Automation"
    DATA = "Data"
    INTERNAL_OPERATIONS = "Internal Operations"
    OTHER = "Other"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class TaskStatus(str, Enum):
    INCOMING = "incoming"
    ANALYZING = "analyzing"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    category: TaskCategory
    priority: TaskPriority
    status: TaskStatus


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    category: TaskCategory | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None

    @model_validator(mode="after")
    def require_at_least_one_value(self):
        if not self.model_fields_set:
            raise ValueError("At least one field is required.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Task fields cannot be null.")
        return self


class Task(TaskCreate):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def ensure_utc_timezone(cls, value):
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class TaskDeleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str
