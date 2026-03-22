"""CRUD routes for Teachers."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Teacher
from ..schemas import TeacherCreate, TeacherOut

router = APIRouter()


@router.get("/teachers", response_model=list[TeacherOut])
def list_teachers(db: Session = Depends(get_db)):
    return db.query(Teacher).order_by(Teacher.name).all()


@router.post("/teachers", response_model=TeacherOut, status_code=201)
def create_teacher(data: TeacherCreate, db: Session = Depends(get_db)):
    t = Teacher(name=data.name, email=data.email)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/teachers/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    t = db.query(Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Teacher not found")
    db.delete(t)
    db.commit()
    return {"ok": True}
