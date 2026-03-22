"""
FastAPI application entry-point.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .routes import teachers, subjects, academic, allocations, rooms, timetable  # noqa: E402

app = FastAPI(
    title="Timetable Generator API",
    version="1.0.0",
    description="AI-Powered Timetable Generation System — Computer Engineering Dept.",
)

# ── CORS ──
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──
app.include_router(teachers.router,    prefix="/api", tags=["Teachers"])
app.include_router(subjects.router,    prefix="/api", tags=["Subjects"])
app.include_router(academic.router,    prefix="/api", tags=["Academic Structure"])
app.include_router(allocations.router, prefix="/api", tags=["Allocations"])
app.include_router(rooms.router,       prefix="/api", tags=["Rooms"])
app.include_router(timetable.router,   prefix="/api", tags=["Timetable"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
