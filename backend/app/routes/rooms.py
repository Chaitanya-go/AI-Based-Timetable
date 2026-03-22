"""Room listing routes (classrooms + labs)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Classroom, Lab
from ..schemas import RoomOut

router = APIRouter()


@router.get("/classrooms", response_model=list[RoomOut])
def list_classrooms(db: Session = Depends(get_db)):
    return db.query(Classroom).order_by(Classroom.name).all()


@router.get("/labs", response_model=list[RoomOut])
def list_labs(db: Session = Depends(get_db)):
    return db.query(Lab).order_by(Lab.name).all()
