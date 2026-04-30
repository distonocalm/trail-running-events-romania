import uuid
from datetime import date

import pytest
from sqlalchemy import JSON, create_engine, types
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared.database import Base
from shared.models import Event, Source, EventSource


class _SQLiteUUID(types.TypeDecorator):
    """Store UUIDs as strings in SQLite."""

    impl = types.String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(value)


def _patch_postgres_types():
    """Replace PostgreSQL-specific column types with SQLite-compatible ones.

    Mutates Base.metadata in-place; called once before create_all.
    """
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID

    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()
            elif isinstance(column.type, PG_UUID):
                column.type = _SQLiteUUID()


# Patch once at import time so every fixture gets the same metadata
_patch_postgres_types()


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def sample_source(db_session):
    source = Source(
        id=uuid.uuid4(),
        name="TestSource",
        url="https://test.com",
        scraper_module="scrapers.sources.test",
        enabled=True,
    )
    db_session.add(source)
    db_session.commit()
    return source
