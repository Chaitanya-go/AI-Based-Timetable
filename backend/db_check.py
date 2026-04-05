import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    for table in ["teachers", "subjects", "classrooms", "labs", "divisions", "allocations"]:
        try:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = res.scalar()
            print(f"Table {table}: {count} records")
        except Exception as e:
            print(f"Error checking {table}: {e}")

    try:
        res = conn.execute(text("SELECT COUNT(*) FROM schedule"))
        count = res.scalar()
        print(f"Table schedule: {count} records")
    except Exception as e:
        print(f"Error checking schedule: {e}")
