"""
Timetable generation & retrieval routes.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import (
    Allocation, Classroom, Lab, Division, Batch, Schedule,
    Teacher, Subject, GlobalSettings
)
from ..schemas import ScheduleEntry
from ..engine.solver import TimetableSolver, AllocationInfo, RoomInfo

router = APIRouter()


@router.post("/timetable/generate")
def generate_timetable(db: Session = Depends(get_db)):
    """Run the continuous-time CSP solver and persist the result."""

    # ── Load data ──
    allocs = (
        db.query(Allocation)
        .options(joinedload(Allocation.teacher), joinedload(Allocation.subject))
        .all()
    )
    if not allocs:
        raise HTTPException(400, "No allocations found. Add workload first.")

    gs = db.query(GlobalSettings).first()
    if not gs:
        gs = GlobalSettings(
            college_start_time=datetime.strptime("09:00", "%H:%M").time(),
            college_end_time=datetime.strptime("17:00", "%H:%M").time()
        )

    classrooms_db = db.query(Classroom).all()
    labs_db = db.query(Lab).all()
    divisions_db = db.query(Division).options(joinedload(Division.batches)).all()

    # Build lookup maps
    div_batches: dict[int, list[int]] = {}
    batch_to_div: dict[int, int] = {}
    div_names: dict[int, str] = {}
    batch_names: dict[int, str] = {}

    for d in divisions_db:
        div_batches[d.id] = [b.id for b in d.batches]
        div_names[d.id] = d.name
        for b in d.batches:
            batch_to_div[b.id] = d.id
            batch_names[b.id] = b.name

    # Build solver inputs
    alloc_infos = []
    for a in allocs:
        group_name = ""
        division_id = None
        if a.group_type == "division" or getattr(a.group_type, "value", None) == "division":
            group_name = f"Div {div_names.get(a.group_id, a.group_id)}"
        else:
            group_name = batch_names.get(a.group_id, str(a.group_id))
            division_id = batch_to_div.get(a.group_id)

        dur = getattr(a.subject, "duration_mins", 60)
        sessions = getattr(a.subject, "sessions_per_week", 1)

        for i in range(sessions):
            alloc_infos.append(AllocationInfo(
                id=f"{a.id}_{i}",
                true_allocation_id=a.id,
                duration_mins=dur,
                teacher_id=a.teacher_id,
                subject_id=a.subject_id,
                subject_name=a.subject.name,
                subject_type=a.subject.type if isinstance(a.subject.type, str) else a.subject.type.value,
                group_type=a.group_type if isinstance(a.group_type, str) else a.group_type.value,
                group_id=a.group_id,
                group_name=group_name,
                teacher_name=a.teacher.name,
                division_id=division_id,
            ))

    div_lunch = {}
    # college start offset helper
    c_start_mins = gs.college_start_time.hour * 60 + gs.college_start_time.minute
    for d in divisions_db:
        if d.lunch_start_time and d.lunch_duration_mins:
            l_mins = d.lunch_start_time.hour * 60 + d.lunch_start_time.minute
            l_offset = l_mins - c_start_mins
            div_lunch[d.id] = (l_offset, d.lunch_duration_mins)

    room_infos_cr = [RoomInfo(id=c.id, name=c.name, room_type="classroom") for c in classrooms_db]
    room_infos_lab = [RoomInfo(id=l.id, name=l.name, room_type="lab") for l in labs_db]

    # ── Solve ──
    solver = TimetableSolver(
        allocations=alloc_infos,
        classrooms=room_infos_cr,
        labs=room_infos_lab,
        division_batches=div_batches,
        div_lunch=div_lunch,
        college_start=gs.college_start_time,
        college_end=gs.college_end_time,
    )

    try:
        result = solver.solve()
    except RuntimeError as e:
        raise HTTPException(409, str(e))

    # ── Persist ──
    db.query(Schedule).delete()
    for slot in result:
        db.add(Schedule(
            allocation_id=slot.true_allocation_id,
            day=slot.day,
            start_time=datetime.strptime(slot.start_time_str, "%H:%M").time(),
            end_time=datetime.strptime(slot.end_time_str, "%H:%M").time(),
            room_type=slot.room_type,
            room_id=slot.room_id,
        ))
    db.commit()

    # ── Return ──
    return {
        "message": f"Generated {len(result)} schedule entries.",
        "schedule": [
            ScheduleEntry(
                day=s.day.capitalize(),
                start_time=s.start_time_str,
                end_time=s.end_time_str,
                subject=s.subject_name,
                teacher=s.teacher_name,
                room=s.room_name,
                type=s.subject_type,
                group=s.group_name,
            )
            for s in result
        ],
    }


@router.get("/timetable", response_model=list[ScheduleEntry])
def get_schedule(db: Session = Depends(get_db)):
    """Fetch the most recently generated schedule."""
    entries = (
        db.query(Schedule)
        .options(
            joinedload(Schedule.allocation).joinedload(Allocation.teacher),
            joinedload(Schedule.allocation).joinedload(Allocation.subject),
        )
        .all()
    )

    # Build lookup maps for names
    divisions_db = db.query(Division).all()
    batches_db = db.query(Batch).all()
    classrooms_db = db.query(Classroom).all()
    labs_db = db.query(Lab).all()

    div_names = {d.id: d.name for d in divisions_db}
    batch_names = {b.id: b.name for b in batches_db}
    cr_names = {c.id: c.name for c in classrooms_db}
    lab_names = {l.id: l.name for l in labs_db}

    result = []
    for e in entries:
        a = e.allocation
        group_name = ""
        if a.group_type in ("division", "division"):
            group_name = f"Div {div_names.get(a.group_id, a.group_id)}"
        else:
            group_name = batch_names.get(a.group_id, str(a.group_id))

        room_name = ""
        if e.room_type in ("division",):
            room_name = cr_names.get(e.room_id, str(e.room_id))
        else:
            room_name = lab_names.get(e.room_id, str(e.room_id))

        day_str = e.day if isinstance(e.day, str) else e.day.value
        sub_type = a.subject.type if isinstance(a.subject.type, str) else a.subject.type.value

        result.append(ScheduleEntry(
            day=day_str.capitalize(),
            start_time=e.start_time.strftime("%H:%M"),
            end_time=e.end_time.strftime("%H:%M"),
            subject=a.subject.name,
            teacher=a.teacher.name,
            room=room_name,
            type=sub_type,
            group=group_name,
        ))

    return result
