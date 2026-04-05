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
    print("--- Seeding Timetable Database with FULL TE Computer Data (Div A & Div B) ---")

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

    # 4. Divisions (A & B)
    div_a = Division(name="A", academic_year_id=te.id, lunch_start_time=time(13, 0), lunch_duration_mins=40)
    div_b = Division(name="B", academic_year_id=te.id, lunch_start_time=time(13, 0), lunch_duration_mins=40)
    db.add_all([div_a, div_b])
    db.commit()

    # 5. Batches
    batches_a = {}
    for bname in ["TA1", "TA2", "TA3", "TA4"]:
        batch = Batch(name=bname, division_id=div_a.id)
        db.add(batch)
        db.commit()
        batches_a[bname] = batch

    batches_b = {}
    for bname in ["TB1", "TB2", "TB3", "TB4"]:
        batch = Batch(name=bname, division_id=div_b.id)
        db.add(batch)
        db.commit()
        batches_b[bname] = batch

    # 6. Teachers
    teachers_data = [
        ("DPM", "Mrs. Deepa P. Mahajan"),
        ("DSC", "Mrs. Dipti S. Chaudhari"),
        ("TVK", "Mrs. Tejali V. Katkar"),
        ("VPL", "Dr. Vaishali P. Latke"),
        ("RSM", "Mrs. Rutuja S. Magar"),
        ("TGL", "Faculty TGL"), 
        ("NAJ", "Faculty NAJ"),
        ("SKR", "Mrs. Swati K. Rajput"),
        ("ADJ", "Dr. Abhijit D. Jadhav"),
        ("AK",  "Dr. Archana Kollu"),
        ("MMK", "Mrs. Madhavi Kapre"),
        ("TCK", "Faculty TCK")
    ]
    teachers = {}
    for tid, tname in teachers_data:
        teacher = Teacher(name=tname, email=f"{tid.lower()}@example.com")
        db.add(teacher)
        db.commit()
        teachers[tid] = teacher

    # 7. Rooms (Combined from both images)
    cr_503 = Classroom(name="503", capacity=60)
    cr_505 = Classroom(name="505", capacity=60)
    db.add_all([cr_503, cr_505])
    
    lab_names = ["502", "512", "516", "517", "524", "527", "618", "619", "624", "625", "626", "627"]
    labs = {}
    for lname in lab_names:
        lab = Lab(name=lname, capacity=30)
        db.add(lab)
        labs[lname] = lab
    db.commit()

    # 8. Subjects (Session counts adjusted based on both images)
    subjects_data_a = [
        ("AI_A", "Artificial Intelligence", "theory", 50, 4),
        ("DSBDA_A", "Data Science & BDA", "theory", 50, 3),
        ("CC_A", "Cloud Computing", "theory", 50, 4),
        ("WT_A", "Web Technology", "theory", 50, 3)
    ]
    subjects_data_b = [
        ("AI_B", "Artificial Intelligence", "theory", 50, 4),
        ("DSBDA_B", "Data Science & BDA", "theory", 50, 4),
        ("CC_B", "Cloud Computing", "theory", 50, 4),
        ("WT_B", "Web Technology", "theory", 50, 4)
    ]
    practicals_data = [
        ("WTL", "Web Technology Lab", "practical", 100, 1),
        ("DSBDAL", "DS & BDA Lab", "practical", 100, 1),
        ("LP-II", "Laboratory Practice II", "practical", 100, 1),
        ("INTERNSHIP", "Internship", "practical", 100, 1)
    ]

    subjects = {}
    for sid, sname, stype, sdur, sper in subjects_data_a + subjects_data_b + practicals_data:
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
    # --- Division A Theory ---
    for sid, tid in [("AI_A", "TVK"), ("DSBDA_A", "DSC"), ("CC_A", "VPL"), ("WT_A", "DPM")]:
        db.add(Allocation(teacher_id=teachers[tid].id, subject_id=subjects[sid].id, group_id=div_a.id, group_type="division"))

    # --- Division B Theory ---
    for sid, tid in [("AI_B", "AK"), ("DSBDA_B", "SKR"), ("CC_B", "MMK"), ("WT_B", "ADJ")]:
        db.add(Allocation(teacher_id=teachers[tid].id, subject_id=subjects[sid].id, group_id=div_b.id, group_type="division"))

    # --- Division A Practicals (Reference image 1) ---
    for b in batches_a.values():
        db.add(Allocation(teacher_id=teachers["DPM"].id, subject_id=subjects["WTL"].id, group_id=b.id, group_type="batch"))
        db.add(Allocation(teacher_id=teachers["NAJ"].id, subject_id=subjects["INTERNSHIP"].id, group_id=b.id, group_type="batch"))
    
    for b, tid in [("TA1", "DSC"), ("TA2", "RSM"), ("TA3", "DSC"), ("TA4", "RSM")]:
        db.add(Allocation(teacher_id=teachers[tid].id, subject_id=subjects["DSBDAL"].id, group_id=batches_a[b].id, group_type="batch"))
    
    for b, tid in [("TA1", "VPL"), ("TA2", "VPL"), ("TA3", "TGL"), ("TA4", "VPL")]:
        db.add(Allocation(teacher_id=teachers[tid].id, subject_id=subjects["LP-II"].id, group_id=batches_a[b].id, group_type="batch"))

    # --- Division B Practicals (Reference image 2) ---
    for b, tid in [("TB1", "ADJ"), ("TB2", "ADJ"), ("TB3", "ADJ"), ("TB4", "ADJ")]:
        db.add(Allocation(teacher_id=teachers[tid].id, subject_id=subjects["WTL"].id, group_id=batches_b[b].id, group_type="batch"))
    
    for b, tid in [("TB1", "SKR"), ("TB2", "SKR"), ("TB3", "SKR"), ("TB4", "RSM")]:
        db.add(Allocation(teacher_id=teachers[tid].id, subject_id=subjects["DSBDAL"].id, group_id=batches_b[b].id, group_type="batch"))
    
    for b, tid in [("TB1", "AK"), ("TB2", "AK"), ("TB3", "ADJ"), ("TB4", "MMK")]:
        db.add(Allocation(teacher_id=teachers[tid].id, subject_id=subjects["LP-II"].id, group_id=batches_b[b].id, group_type="batch"))
    
    for b in batches_b.values():
        db.add(Allocation(teacher_id=teachers["TCK"].id, subject_id=subjects["INTERNSHIP"].id, group_id=b.id, group_type="batch"))

    db.commit()

    print("--- Database successfully seeded with FULL Divisions A & B! ---")

if __name__ == "__main__":
    seed()
    db.close()
