import logging
from datetime import datetime, timezone

from celery_app import app
from shared.database import SessionLocal
from shared.models import Source
from scrapers.dedup import find_or_create_event

logger = logging.getLogger(__name__)

SCRAPER_REGISTRY = {
    "scrapers.sources.eliterunning": "scrapers.sources.eliterunning.EliteRunningScraper",
    "scrapers.sources.runmap": "scrapers.sources.runmap.RunMapScraper",
    "scrapers.sources.fisheye": "scrapers.sources.fisheye.FisheyeScraper",
    "scrapers.sources.vladcarbune": "scrapers.sources.vladcarbune.VladCarbuneScraper",
    "scrapers.sources.timeit": "scrapers.sources.timeit.TimeItScraper",
}


def _get_scraper_class(module_path: str):
    parts = SCRAPER_REGISTRY.get(module_path, module_path).rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid scraper module path: {module_path}")
    module_name, class_name = parts
    import importlib
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


@app.task(name="tasks.scrape_source")
def scrape_source(source_id: str) -> dict:
    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {"error": f"Source {source_id} not found"}

        if not source.enabled:
            return {"skipped": True, "reason": "Source is disabled"}

        scraper_class = _get_scraper_class(source.scraper_module)
        scraper = scraper_class()

        logger.info(f"Scraping {source.name} from {source.url}")
        raw_events = scraper.scrape()
        logger.info(f"Found {len(raw_events)} events from {source.name}")

        created_count = 0
        updated_count = 0

        for raw_event in raw_events:
            event, was_created = find_or_create_event(db, raw_event, source.id)
            if was_created:
                created_count += 1
            else:
                updated_count += 1

        source.last_scraped_at = datetime.now(timezone.utc)
        db.commit()

        result = {
            "source": source.name,
            "total": len(raw_events),
            "created": created_count,
            "updated": updated_count,
        }
        logger.info(f"Scrape complete: {result}")
        return result

    except Exception as e:
        logger.exception(f"Error scraping source {source_id}")
        db.rollback()
        raise
    finally:
        db.close()


@app.task(name="tasks.scrape_all_sources")
def scrape_all_sources() -> dict:
    db = SessionLocal()
    try:
        sources = db.query(Source).filter(Source.enabled.is_(True)).all()
        source_ids = [str(s.id) for s in sources]
    finally:
        db.close()

    results = []
    for source_id in source_ids:
        task = scrape_source.delay(source_id)
        results.append({"source_id": source_id, "task_id": task.id})

    return {"dispatched": len(results), "tasks": results}
