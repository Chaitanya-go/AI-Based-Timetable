import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("DATABASE_URL")
if not url:
    print("NO URL FOUND")
    exit(1)

print(f"Connecting to: {url[:30]}...")
engine = create_engine(url)

try:
    with engine.begin() as conn:
        print("Executing schema.sql...")
        with open("../schema.sql", "r", encoding="utf-8") as f:
            sql = f.read()
            
        # SQL execution requires split statements for some dialects, but postgres handles blocks usually
        # To be safe, we can let SQLAlchemy run the whole block as raw SQL
        conn.execute(text(sql))
    print("Database Initialized successfully!")
except Exception as e:
    print(f"Failed: {e}")
