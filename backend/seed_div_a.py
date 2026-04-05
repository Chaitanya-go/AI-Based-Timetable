import os
from datetime import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import our models
from app.database import Base
from app.models import (
    Teacher, Subject, AcademicYear, Division, Batch, Classroom, Lab, Allocation, GlobalSettings, Schedule
)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not found in .env file.")
    exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def seed():
    print("--- Seeding Timetable Database with ACCURATE Division A Data ---")

    Base.metadata.create_all(bind=engine)

    # 1. Clear existing data
    print("Clearing old data...")
    db.query(Schedule).delete()
    db.query(Allocation).delete()
    db.query(Batch).delete()
    db.query(Division).delete()
    db.query(Subject).delete()
    db.query(AcademicYear).delete()
    db.query(Teacher).delete()
    db.query(Classroom).delete()
    db.query(Lab).delete()
    db.query(GlobalSettings).delete()
    db.commit()

    # 2. Global Settings (09:40 to 17:00)
    gs = GlobalSettings(
        college_start_time=time(9, 40),
        college_end_time=time(17, 0)
    )
    db.add(gs)

    # 3. Academic Year (TE Computer)
    te = AcademicYear(name="TE Computer")
    db.add(te)
    db.commit()

    # 4. Division A (Lunch 13:00 to 13:40)
    div_a = Division(
        name="A", 
        academic_year_id=te.id, 
        lunch_start_time=time(13, 0), 
        lunch_duration_mins=40
    )
    db.add(div_a)
    db.commit()

    # 5. Batches (TA1 to TA4)
    batches = {}
    for bname in ["TA1", "TA2", "TA3", "TA4"]:
        batch = Batch(name=bname, division_id=div_a.id)
        db.add(batch)
        db.commit()
        batches[bname] = batch

    # 6. Teachers
    teachers_data = [
        ("DPM", "Mrs. Deepa P. Mahajan"),
        ("DSC", "Mrs. Dipti S. Chaudhari"),
        ("TVK", "Mrs. Tejali V. Katkar"),
        ("VPL", "Dr. Vaishali P. Latke"),
        ("RSM", "Mrs. Rutuja S. Magar"),
        ("TGL", "Faculty TGL"), 
        ("NAJ", "Faculty NAJ")
    ]
    teachers = {}
    for tid, tname in teachers_data:
        teacher = Teacher(name=tname, email=f"{tid.lower()}@example.com")
        db.add(teacher)
        db.commit()
        teachers[tid] = teacher

    # 7. Rooms (from image)
    # Theory Room
    cr_503 = Classroom(name="503", capacity=60)
    db.add(cr_503)
    
    # Labs listed in rotational block
    labs_names = ["502", "512", "619", "624", "625", "626", "627"]
    labs = {}
    for lname in labs_names:
        lab = Lab(name=lname, capacity=30)
        db.add(lab)
        labs[lname] = lab
    db.commit()

    # 8. Subjects (Session counts adjusted based on image)
    subjects_data = [
        # Theory (50 mins)
        ("AI", "Artificial Intelligence", "theory", 50, 4),                     # Mon, Tue, Wed, Fri
        ("DSBDA", "Data Science & BDA", "theory", 50, 3),                      # Tue, Wed, Fri
        ("CC", "Cloud Computing (EL-II)", "theory", 50, 4),                    # Mon, Tue, Wed, Thu
        ("WT", "Web Technology", "theory", 50, 3),                             # Tue, Wed, Thu
        # Practical (100 mins)
        ("WTL", "Web Technology Lab", "practical", 100, 1),
        ("DSBDAL", "DS & BDA Lab", "practical", 100, 1),
        ("LP-II", "Laboratory Practice II", "practical", 100, 1),
        ("INTERNSHIP", "Internship", "practical", 100, 1)
    ]
    subjects = {}
    for sid, sname, stype, sdur, sper in subjects_data:
        subject = Subject(
            name=sname, 
            code=sid, 
            type=stype, 
            duration_mins=sdur, 
            sessions_per_week=sper, 
            academic_year_id=te.id
        )
        db.add(subject)
        db.commit()
        subjects[sid] = subject

    # 9. Workload Allocations
    # --- Theory Allocations ---
    for sid, tid in [("WT", "DPM"), ("DSBDA", "DSC"), ("AI", "TVK"), ("CC", "VPL")]:
        db.add(Allocation(
            teacher_id=teachers[tid].id, 
            subject_id=subjects[sid].id, 
            group_id=div_a.id, 
            group_type="division"
        ))

    # --- Practical Allocations (Teacher assignments from image) ---
    # WTL - Mrs. Deepa P. Mahajan
    for bname in ["TA1", "TA2", "TA3", "TA4"]:
        db.add(Allocation(teacher_id=teachers["DPM"].id, subject_id=subjects["WTL"].id, group_id=batches[bname].id, group_type="batch"))

    # DSBDAL - Shared DSC and RSM
    for bname, tid in [("TA1", "DSC"), ("TA2", "RSM"), ("TA3", "DSC"), ("TA4", "RSM")]:
        db.add(Allocation(teacher_id=teachers[tid].id, subject_id=subjects["DSBDAL"].id, group_id=batches[bname].id, group_type="batch"))

    # LP-II - Shared VPL and TGL
    for bname, tid in [("TA1", "VPL"), ("TA2", "VPL"), ("TA3", "TGL"), ("TA4", "VPL")]:
        # Based on image: TA2-VPL, TA3-TGL, TA1-VPL (Thu), TA4-VPL (Tue)
        # Note: TGL also appears for TA1 on Fri
        db.add(Allocation(teacher_id=teachers[tid].id, subject_id=subjects["LP-II"].id, group_id=batches[bname].id, group_type="batch"))

    # INTERNSHIP - Faculty NAJ
    for bname in ["TA1", "TA2", "TA3", "TA4"]:
        db.add(Allocation(teacher_id=teachers["NAJ"].id, subject_id=subjects["INTERNSHIP"].id, group_id=batches[bname].id, group_type="batch"))

    db.commit()

    print("--- Database successfully seeded with ACTUAL Division A data! ---")

if __name__ == "__main__":
    seed()
    db.close()
