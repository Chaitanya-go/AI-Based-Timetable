from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")

try:
    print(f"Testing connection to: {url[:30]}...")
    engine = create_engine(url)
    with engine.connect() as conn:
        print("✅ Connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
