"""Routes for AcademicYears, Divisions, and Batches."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import AcademicYear, Division, Batch, GlobalSettings
from ..schemas import (
    AcademicYearOut, DivisionCreate, DivisionOut, BatchCreate, BatchOut,
    GlobalSettingsCreate, GlobalSettingsOut
)
from datetime import datetime

router = APIRouter()

# ── Global Settings ──
@router.get("/global-settings", response_model=GlobalSettingsOut)
def get_settings(db: Session = Depends(get_db)):
    gs = db.query(GlobalSettings).first()
    if not gs:
        # Auto-create default
        gs = GlobalSettings(college_start_time=datetime.strptime("09:00", "%H:%M").time(), college_end_time=datetime.strptime("17:00", "%H:%M").time())
        db.add(gs)
        db.commit()
        db.refresh(gs)
    return GlobalSettingsOut(
        id=gs.id,
        college_start_time=gs.college_start_time.strftime("%H:%M"),
        college_end_time=gs.college_end_time.strftime("%H:%M")
    )

@router.put("/global-settings", response_model=GlobalSettingsOut)
def update_settings(data: GlobalSettingsCreate, db: Session = Depends(get_db)):
    gs = db.query(GlobalSettings).first()
    if not gs:
        gs = GlobalSettings()
        db.add(gs)
    gs.college_start_time = datetime.strptime(data.college_start_time, "%H:%M").time()
    gs.college_end_time = datetime.strptime(data.college_end_time, "%H:%M").time()
    db.commit()
    db.refresh(gs)
    return GlobalSettingsOut(
        id=gs.id,
        college_start_time=gs.college_start_time.strftime("%H:%M"),
        college_end_time=gs.college_end_time.strftime("%H:%M")
    )

# ── Academic Years ──
@router.get("/academic-years", response_model=list[AcademicYearOut])
def list_years(db: Session = Depends(get_db)):
    return db.query(AcademicYear).order_by(AcademicYear.id).all()


# ── Divisions ──
@router.get("/divisions", response_model=list[DivisionOut])
def list_divisions(db: Session = Depends(get_db)):
    divs = (
        db.query(Division)
        .options(joinedload(Division.academic_year), joinedload(Division.batches))
        .order_by(Division.academic_year_id, Division.name)
        .all()
    )
    result = []
    for d in divs:
        result.append(DivisionOut(
            id=d.id,
            name=d.name,
            academic_year_id=d.academic_year_id,
            academic_year_name=d.academic_year.name if d.academic_year else None,
            lunch_start_time=d.lunch_start_time.strftime("%H:%M") if d.lunch_start_time else None,
            lunch_duration_mins=d.lunch_duration_mins,
            batches=[{"id": b.id, "name": b.name} for b in d.batches],
        ))
    return result


@router.post("/divisions", response_model=DivisionOut, status_code=201)
def create_division(data: DivisionCreate, db: Session = Depends(get_db)):
    l_start = datetime.strptime(data.lunch_start_time, "%H:%M").time() if data.lunch_start_time else None
    d = Division(
        name=data.name, 
        academic_year_id=data.academic_year_id,
        lunch_start_time=l_start,
        lunch_duration_mins=data.lunch_duration_mins
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    yr = db.query(AcademicYear).get(d.academic_year_id)
    return DivisionOut(
        id=d.id, name=d.name,
        academic_year_id=d.academic_year_id,
        academic_year_name=yr.name if yr else None,
        lunch_start_time=d.lunch_start_time.strftime("%H:%M") if d.lunch_start_time else None,
        lunch_duration_mins=d.lunch_duration_mins,
        batches=[],
    )


# ── Batches ──
@router.get("/batches", response_model=list[BatchOut])
def list_batches(db: Session = Depends(get_db)):
    batches = db.query(Batch).options(joinedload(Batch.division)).order_by(Batch.division_id, Batch.name).all()
    return [
        BatchOut(
            id=b.id, name=b.name,
            division_id=b.division_id,
            division_name=b.division.name if b.division else None,
        )
        for b in batches
    ]


@router.post("/batches", response_model=BatchOut, status_code=201)
def create_batch(data: BatchCreate, db: Session = Depends(get_db)):
    b = Batch(name=data.name, division_id=data.division_id)
    db.add(b)
    db.commit()
    db.refresh(b)
    div = db.query(Division).get(b.division_id)
    return BatchOut(
        id=b.id, name=b.name,
        division_id=b.division_id,
        division_name=div.name if div else None,
    )
