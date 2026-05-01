from uuid import UUID

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from shared.config import REDIS_URL
from shared.database import get_db
from shared.models import Source
from app.schemas import ScrapeStatusResponse

router = APIRouter()


def get_celery_app() -> Celery:
    return Celery("worker", broker=REDIS_URL, backend=REDIS_URL)


@router.post("/scrape", status_code=202)
def trigger_scrape_all():
    celery_app = get_celery_app()
    task = celery_app.send_task("tasks.scrape_all_sources")
    return {"task_id": task.id, "status": "dispatched"}


@router.post("/scrape/{source_id}", status_code=202)
def trigger_scrape_source(source_id: UUID, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    celery_app = get_celery_app()
    task = celery_app.send_task("tasks.scrape_source", args=[str(source_id)])
    return {"task_id": task.id, "status": "dispatched"}


@router.get("/scrape/status", response_model=ScrapeStatusResponse)
def scrape_status(task_id: str = Query(...)):
    celery_app = get_celery_app()
    result = celery_app.AsyncResult(task_id)
    return ScrapeStatusResponse(
        task_id=task_id,
        status=result.status,
        result=str(result.result) if result.result else None,
    )
