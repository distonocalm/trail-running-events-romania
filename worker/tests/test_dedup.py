import uuid
from datetime import date

from shared.models import Event, EventSource
from scrapers.base import RawEvent
from scrapers.dedup import find_or_create_event


def test_creates_new_event_when_no_match(db_session, sample_source):
    raw = RawEvent(
        name="Carpathia Trails 2026",
        date_start=date(2026, 7, 4),
        location="Brașov",
        county="Brașov",
        external_id="carpathia-2026",
    )
    event, created = find_or_create_event(db_session, raw, sample_source.id)
    assert created is True
    assert event.name == "Carpathia Trails 2026"
    assert event.year == 2026


def test_matches_existing_event_by_external_id(db_session, sample_source):
    raw = RawEvent(
        name="Carpathia Trails 2026",
        date_start=date(2026, 7, 4),
        location="Brașov",
        external_id="carpathia-2026",
    )
    event1, created1 = find_or_create_event(db_session, raw, sample_source.id)
    assert created1 is True

    raw2 = RawEvent(
        name="Carpathia Trails 2026 (updated)",
        date_start=date(2026, 7, 4),
        location="Brașov",
        external_id="carpathia-2026",
    )
    event2, created2 = find_or_create_event(db_session, raw2, sample_source.id)
    assert created2 is False
    assert event2.id == event1.id
    assert event2.name == "Carpathia Trails 2026 (updated)"


def test_matches_existing_event_by_fuzzy_name_and_date(db_session, sample_source):
    raw1 = RawEvent(
        name="Carpathia Trails 2026",
        date_start=date(2026, 7, 4),
        location="Brașov",
        external_id="ext-1",
    )
    event1, _ = find_or_create_event(db_session, raw1, sample_source.id)

    other_source_id = uuid.uuid4()
    from shared.models import Source

    other_source = Source(
        id=other_source_id,
        name="OtherSource",
        url="https://other.com",
        scraper_module="scrapers.sources.other",
    )
    db_session.add(other_source)
    db_session.commit()

    raw2 = RawEvent(
        name="Carpathia Trails",
        date_start=date(2026, 7, 4),
        location="Brașov",
        external_id="ext-other-1",
    )
    event2, created = find_or_create_event(db_session, raw2, other_source_id)
    assert created is False
    assert event2.id == event1.id


def test_does_not_match_different_events(db_session, sample_source):
    raw1 = RawEvent(
        name="Carpathia Trails 2026",
        date_start=date(2026, 7, 4),
        location="Brașov",
        external_id="ext-1",
    )
    find_or_create_event(db_session, raw1, sample_source.id)

    raw2 = RawEvent(
        name="Predeal Forest Run",
        date_start=date(2026, 7, 11),
        location="Predeal",
        external_id="ext-2",
    )
    event2, created = find_or_create_event(db_session, raw2, sample_source.id)
    assert created is True
