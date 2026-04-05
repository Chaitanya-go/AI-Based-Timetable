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
    print("--- Seeding Timetable Database ---")

    # 0. Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # 1. Clear existing data in reverse dependency order
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

    # 2. Global Settings
    gs = GlobalSettings(
        college_start_time=time(9, 0),
        college_end_time=time(17, 0)
    )
    db.add(gs)

    # 3. Academic Years
    fe = AcademicYear(name="First Year")
    se = AcademicYear(name="Second Year")
    te = AcademicYear(name="Third Year")
    db.add_all([fe, se, te])
    db.commit()

    # 4. Divisions & Batches
    div_a = Division(name="A", academic_year_id=se.id, lunch_start_time=time(13, 0), lunch_duration_mins=60)
    div_b = Division(name="B", academic_year_id=te.id, lunch_start_time=time(12, 0), lunch_duration_mins=60)
    db.add_all([div_a, div_b])
    db.commit()

    b1 = Batch(name="A1", division_id=div_a.id)
    b2 = Batch(name="A2", division_id=div_a.id)
    b3 = Batch(name="B1", division_id=div_b.id)
    db.add_all([b1, b2, b3])
    db.commit()

    # 5. Teachers
    t1 = Teacher(name="Dr. Sharma", email="sharma@example.com")
    t2 = Teacher(name="Prof. Patel", email="patel@example.com")
    t3 = Teacher(name="Dr. Kulkarni", email="kulkarni@example.com")
    t4 = Teacher(name="Prof. Deshmukh", email="deshmukh@example.com")
    db.add_all([t1, t2, t3, t4])
    db.commit()

    # 6. Subjects (Adding required 'code' and 'academic_year_id')
    s1 = Subject(name="Data Structures", code="CS201", type="theory", duration_mins=60, sessions_per_week=3, academic_year_id=se.id)
    s2 = Subject(name="DBMS", code="CS202", type="theory", duration_mins=60, sessions_per_week=2, academic_year_id=se.id)
    s3 = Subject(name="Operating Systems", code="CS301", type="theory", duration_mins=60, sessions_per_week=3, academic_year_id=te.id)
    s4 = Subject(name="DS Lab", code="CS201L", type="practical", duration_mins=120, sessions_per_week=1, academic_year_id=se.id)
    s5 = Subject(name="DBMS Lab", code="CS202L", type="practical", duration_mins=120, sessions_per_week=1, academic_year_id=se.id)
    db.add_all([s1, s2, s3, s4, s5])
    db.commit()

    # 7. Rooms
    cr1 = Classroom(name="CR-101", capacity=60)
    cr2 = Classroom(name="CR-102", capacity=60)
    l1 = Lab(name="LAB-1", capacity=30)
    l2 = Lab(name="LAB-2", capacity=30)
    db.add_all([cr1, cr2, l1, l2])
    db.commit()

    # 8. Workload Allocations
    # Theory: Div A gets DS, DBMS
    db.add(Allocation(teacher_id=t1.id, subject_id=s1.id, group_id=div_a.id, group_type="division"))
    db.add(Allocation(teacher_id=t2.id, subject_id=s2.id, group_id=div_a.id, group_type="division"))
    
    # Theory: Div B gets OS
    db.add(Allocation(teacher_id=t3.id, subject_id=s3.id, group_id=div_b.id, group_type="division"))

    # Practicals: A1 gets DS Lab, A2 gets DS Lab
    db.add(Allocation(teacher_id=t1.id, subject_id=s4.id, group_id=b1.id, group_type="batch"))
    db.add(Allocation(teacher_id=t4.id, subject_id=s4.id, group_id=b2.id, group_type="batch"))
    
    # Practical: B1 gets DBMS Lab
    db.add(Allocation(teacher_id=t2.id, subject_id=s5.id, group_id=b3.id, group_type="batch"))
    
    db.commit()

    print("--- Database successfully seeded with sample data! ---")
    print("You can now refresh the app and click 'Generate Timetable'.")

if __name__ == "__main__":
    seed()
    db.close()
