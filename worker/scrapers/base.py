from dataclasses import dataclass, field
from datetime import date


@dataclass
class RawEvent:
    name: str
    date_start: date
    date_end: date | None = None
    location: str | None = None
    county: str | None = None
    distances: list[dict] | None = None
    description: str | None = None
    registration_status: str | None = None
    registration_deadline: date | None = None
    price: str | None = None
    event_url: str | None = None
    image_url: str | None = None
    external_id: str | None = None
    raw_data: dict | None = None


class BaseScraper:
    name: str = "base"
    base_url: str = ""

    def scrape(self) -> list[RawEvent]:
        raise NotImplementedError

    def parse_event(self, raw_data) -> RawEvent:
        raise NotImplementedError
