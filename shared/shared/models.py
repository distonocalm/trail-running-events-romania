import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from shared.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(500))
    date_start: Mapped[date] = mapped_column(Date)
    date_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    county: Mapped[str | None] = mapped_column(String(100), nullable=True)
    distances: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    registration_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default="unknown"
    )
    registration_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    price: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    event_sources: Mapped[list["EventSource"]] = relationship(back_populates="event")

    __table_args__ = (Index("ix_events_year_date", "year", "date_start"),)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(1000))
    scraper_module: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scrape_interval_hours: Mapped[int] = mapped_column(Integer, default=24)

    event_sources: Mapped[list["EventSource"]] = relationship(back_populates="source")


class EventSource(Base):
    __tablename__ = "event_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE")
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE")
    )
    external_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    event: Mapped["Event"] = relationship(back_populates="event_sources")
    source: Mapped["Source"] = relationship(back_populates="event_sources")

    __table_args__ = (
        UniqueConstraint("event_id", "source_id", name="uq_event_source"),
    )
