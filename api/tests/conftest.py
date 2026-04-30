import uuid
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, String, create_engine, types
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared.database import Base, get_db
from shared.models import Event, Source
from app.main import app


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
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_events(db_session):
    events = [
        Event(
            id=uuid.uuid4(),
            name="Carpathia Trails 2026",
            date_start=date(2026, 7, 4),
            location="Brașov",
            county="Brașov",
            distances=[{"name": "Ultra", "km": 102, "elevation_gain": 3200}],
            year=2026,
            registration_status="open",
            event_url="https://carpathiatrails.com",
            image_url="https://example.com/img.jpg",
        ),
        Event(
            id=uuid.uuid4(),
            name="Predeal Forest Run",
            date_start=date(2026, 7, 11),
            location="Predeal",
            county="Brașov",
            distances=[
                {"name": "Half", "km": 21},
                {"name": "Marathon", "km": 42},
            ],
            year=2026,
            registration_status="open",
        ),
        Event(
            id=uuid.uuid4(),
            name="Baneasa Forest Run",
            date_start=date(2026, 4, 5),
            location="Bucharest",
            county="București",
            distances=[{"km": 7}, {"km": 14}, {"km": 21}],
            year=2026,
            registration_status="closed",
        ),
    ]
    db_session.add_all(events)
    db_session.commit()
    return events
