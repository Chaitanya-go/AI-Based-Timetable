"""CRUD routes for Subjects."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Subject
from ..schemas import SubjectCreate, SubjectOut

router = APIRouter()


@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).order_by(Subject.name).all()


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db)):
    s = Subject(
        name=data.name,
        code=data.code,
        type=data.type.value,
        sessions_per_week=data.sessions_per_week,
        duration_mins=data.duration_mins,
        academic_year_id=data.academic_year_id,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    s = db.query(Subject).get(subject_id)
    if not s:
        raise HTTPException(404, "Subject not found")
    db.delete(s)
    db.commit()
    return {"ok": True}
