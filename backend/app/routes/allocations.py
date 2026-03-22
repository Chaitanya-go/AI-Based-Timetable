"""Allocation routes — bulk create from the Teacher Workload UI."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Allocation
from ..schemas import AllocationsBulk, AllocationOut

router = APIRouter()


@router.get("/allocations", response_model=list[AllocationOut])
def list_allocations(db: Session = Depends(get_db)):
    return db.query(Allocation).order_by(Allocation.teacher_id).all()


@router.get("/allocations/teacher/{teacher_id}", response_model=list[AllocationOut])
def list_teacher_allocations(teacher_id: int, db: Session = Depends(get_db)):
    return db.query(Allocation).filter(Allocation.teacher_id == teacher_id).all()


@router.post("/allocations", response_model=list[AllocationOut], status_code=201)
def create_allocations(data: AllocationsBulk, db: Session = Depends(get_db)):
    """Bulk insert allocation rows parsed by the frontend, ignoring duplicates."""
    created = []
    for item in data.allocations:
        existing = db.query(Allocation).filter(
            Allocation.teacher_id == item.teacher_id,
            Allocation.subject_id == item.subject_id,
            Allocation.group_type == item.group_type.value,
            Allocation.group_id == item.group_id
        ).first()
        
        if existing:
            continue

        alloc = Allocation(
            teacher_id=item.teacher_id,
            subject_id=item.subject_id,
            group_type=item.group_type.value,
            group_id=item.group_id,
        )
        db.add(alloc)
        created.append(alloc)
    db.commit()
    for a in created:
        db.refresh(a)
    return created


@router.delete("/allocations/{alloc_id}")
def delete_allocation(alloc_id: int, db: Session = Depends(get_db)):
    a = db.query(Allocation).get(alloc_id)
    if not a:
        raise HTTPException(404, "Allocation not found")
    db.delete(a)
    db.commit()
    return {"ok": True}
