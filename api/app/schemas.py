from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class DistanceItem(BaseModel):
    name: str | None = None
    km: float
    elevation_gain: int | None = None


class EventBase(BaseModel):
    name: str
    date_start: date
    date_end: date | None = None
    location: str | None = None
    county: str | None = None
    distances: list[DistanceItem] | None = None
    description: str | None = None
    registration_status: str | None = "unknown"
    registration_deadline: date | None = None
    price: str | None = None
    event_url: str | None = None
    image_url: str | None = None
    year: int


class EventRead(EventBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    items: list[EventRead]
    total: int
    page: int
    per_page: int


class SourceBase(BaseModel):
    name: str
    url: str
    scraper_module: str
    enabled: bool = True
    scrape_interval_hours: int = 24


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    scraper_module: str | None = None
    enabled: bool | None = None
    scrape_interval_hours: int | None = None


class SourceRead(SourceBase):
    id: UUID
    last_scraped_at: datetime | None = None

    model_config = {"from_attributes": True}


class ScrapeStatusResponse(BaseModel):
    task_id: str
    status: str
    result: str | None = None


class StatsResponse(BaseModel):
    event_count: int
    source_count: int
    county_count: int
    upcoming_count: int
