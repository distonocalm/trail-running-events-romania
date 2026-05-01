import uuid
from datetime import date

from Levenshtein import ratio as levenshtein_ratio
from sqlalchemy.orm import Session

from shared.models import Event, EventSource
from scrapers.base import RawEvent

SIMILARITY_THRESHOLD = 0.75


def _normalize_name(name: str) -> str:
    return " ".join(name.lower().strip().split())


def _find_by_external_id(
    db: Session, source_id: uuid.UUID, external_id: str
) -> Event | None:
    result = (
        db.query(Event)
        .join(EventSource)
        .filter(
            EventSource.source_id == source_id,
            EventSource.external_id == external_id,
        )
        .first()
    )
    return result


def _find_by_fuzzy_match(
    db: Session, name: str, date_start: date, location: str | None
) -> Event | None:
    candidates = db.query(Event).filter(Event.date_start == date_start).all()
    normalized = _normalize_name(name)

    best_match = None
    best_score = 0.0

    for candidate in candidates:
        candidate_normalized = _normalize_name(candidate.name)
        score = levenshtein_ratio(normalized, candidate_normalized)
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_match and best_score >= SIMILARITY_THRESHOLD:
        return best_match

    return None


def _update_event(event: Event, raw: RawEvent) -> None:
    if raw.description and not event.description:
        event.description = raw.description
    if raw.distances and not event.distances:
        event.distances = raw.distances
    if raw.registration_status and event.registration_status == "unknown":
        event.registration_status = raw.registration_status
    if raw.registration_deadline and not event.registration_deadline:
        event.registration_deadline = raw.registration_deadline
    if raw.price and not event.price:
        event.price = raw.price
    if raw.image_url and not event.image_url:
        event.image_url = raw.image_url
    if raw.event_url and not event.event_url:
        event.event_url = raw.event_url
    if raw.county and not event.county:
        event.county = raw.county
    if raw.location and not event.location:
        event.location = raw.location
    if raw.name and len(raw.name) > len(event.name):
        event.name = raw.name


def _upsert_event_source(
    db: Session, event_id: uuid.UUID, source_id: uuid.UUID, raw: RawEvent
) -> None:
    existing = (
        db.query(EventSource)
        .filter(
            EventSource.event_id == event_id,
            EventSource.source_id == source_id,
        )
        .first()
    )
    if existing:
        existing.external_id = raw.external_id
        existing.raw_data = raw.raw_data
    else:
        es = EventSource(
            event_id=event_id,
            source_id=source_id,
            external_id=raw.external_id,
            raw_data=raw.raw_data,
        )
        db.add(es)


def find_or_create_event(
    db: Session, raw: RawEvent, source_id: uuid.UUID
) -> tuple[Event, bool]:
    if raw.external_id:
        existing = _find_by_external_id(db, source_id, raw.external_id)
        if existing:
            _update_event(existing, raw)
            _upsert_event_source(db, existing.id, source_id, raw)
            db.commit()
            return existing, False

    existing = _find_by_fuzzy_match(db, raw.name, raw.date_start, raw.location)
    if existing:
        _update_event(existing, raw)
        _upsert_event_source(db, existing.id, source_id, raw)
        db.commit()
        return existing, False

    event = Event(
        name=raw.name,
        date_start=raw.date_start,
        date_end=raw.date_end,
        location=raw.location,
        county=raw.county,
        distances=raw.distances,
        description=raw.description,
        registration_status=raw.registration_status or "unknown",
        registration_deadline=raw.registration_deadline,
        price=raw.price,
        event_url=raw.event_url,
        image_url=raw.image_url,
        year=raw.date_start.year,
    )
    db.add(event)
    db.flush()

    _upsert_event_source(db, event.id, source_id, raw)
    db.commit()
    return event, True
