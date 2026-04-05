import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(db_url)
try:
    with engine.connect() as conn:
        print("Successfully connected to Supabase!")
        tables = ['teachers', 'subjects', 'divisions', 'allocations']
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"{table}: {result} records")
            except Exception as e:
                print(f"Error counting {table}: {e}")
except Exception as e:
    print(f"Failed to connect: {e}")
