import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# Default to a local SQLite file for development. In production (Render)
# a proper Postgres `DATABASE_URL` environment variable should be set.
DEFAULT_DATABASE_URL = "sqlite:///./operations.db"
# Prefer a standard `DATABASE_URL` (as provided by many PaaS providers);
# fall back to the project-specific `KINUFLOW_DATABASE_URL` and then to
# the local SQLite default.
_raw_db = os.getenv("DATABASE_URL", os.getenv("KINUFLOW_DATABASE_URL", DEFAULT_DATABASE_URL))

# Normalize common Postgres URL forms to use the modern psycopg 3 SQLAlchemy
# dialect when the URL comes from providers like Neon. Do not alter URLs that
# already specify a driver (contain a `+`), and preserve sqlite local dev.
def _normalize_database_url(raw: str) -> str:
    if not raw:
        return raw
    # If it's sqlite, leave as-is
    if raw.startswith("sqlite"):
        return raw
    # If a driver is already specified (postgresql+psycopg:// or similar), keep it
    if "+" in raw.split(":", 1)[0]:
        return raw
    # Handle the common provider prefixes
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+psycopg://", 1)
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+psycopg://", 1)
    return raw

DATABASE_URL = _normalize_database_url(_raw_db)


class Base(DeclarativeBase):
    pass


def create_database_engine(database_url: str) -> Engine:
    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    return create_engine(
        database_url,
        connect_args=connect_args,
        # Replace stale PostgreSQL connections before a request uses them.
        pool_pre_ping=database_url.startswith("postgresql"),
    )


engine = create_database_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def create_tables() -> None:
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
