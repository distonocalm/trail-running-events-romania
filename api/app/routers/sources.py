from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.models import Source
from app.schemas import SourceCreate, SourceRead, SourceUpdate

router = APIRouter()


@router.get("/sources", response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).order_by(Source.name).all()


@router.post("/sources", response_model=SourceRead, status_code=201)
def create_source(source: SourceCreate, db: Session = Depends(get_db)):
    db_source = Source(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@router.patch("/sources/{source_id}", response_model=SourceRead)
def update_source(
    source_id: UUID, source: SourceUpdate, db: Session = Depends(get_db)
):
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")

    for key, value in source.model_dump(exclude_unset=True).items():
        setattr(db_source, key, value)

    db.commit()
    db.refresh(db_source)
    return db_source


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: UUID, db: Session = Depends(get_db)):
    db_source = db.query(Source).filter(Source.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(db_source)
    db.commit()
    return Response(status_code=204)
