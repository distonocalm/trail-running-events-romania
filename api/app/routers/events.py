from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.models import Event
from app.schemas import EventListResponse, EventRead, StatsResponse

router = APIRouter()


def _matches_distance_filter(
    distances: list[dict] | None, dmin: float | None, dmax: float | None
) -> bool:
    if not distances:
        return False
    for d in distances:
        km = d.get("km", 0)
        if (dmin is None or km >= dmin) and (dmax is None or km <= dmax):
            return True
    return False


@router.get("/events", response_model=EventListResponse)
def list_events(
    month: int | None = None,
    county: str | None = None,
    distance_min: float | None = None,
    distance_max: float | None = None,
    search: str | None = None,
    upcoming: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Event).order_by(Event.date_start)

    if month is not None:
        query = query.filter(extract("month", Event.date_start) == month)

    if county is not None:
        escaped = county.replace("%", r"\%").replace("_", r"\_")
        query = query.filter(Event.county.ilike(f"%{escaped}%"))

    if search is not None:
        escaped = search.replace("%", r"\%").replace("_", r"\_")
        pattern = f"%{escaped}%"
        query = query.filter(
            Event.name.ilike(pattern) | Event.location.ilike(pattern)
        )

    if upcoming:
        query = query.filter(Event.date_start >= date.today())

    if distance_min is not None or distance_max is not None:
        all_events = query.all()
        filtered_ids = [
            e.id
            for e in all_events
            if _matches_distance_filter(e.distances, distance_min, distance_max)
        ]
        query = (
            db.query(Event)
            .filter(Event.id.in_(filtered_ids))
            .order_by(Event.date_start)
        )

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return EventListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/events/{event_id}", response_model=EventRead)
def get_event(event_id: UUID, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    event_count = db.query(Event).count()
    from shared.models import Source
    source_count = db.query(Source).filter(Source.enabled.is_(True)).count()
    county_count = (
        db.query(Event.county).filter(Event.county.isnot(None)).distinct().count()
    )
    upcoming_count = db.query(Event).filter(Event.date_start >= date.today()).count()

    return StatsResponse(
        event_count=event_count,
        source_count=source_count,
        county_count=county_count,
        upcoming_count=upcoming_count,
    )
