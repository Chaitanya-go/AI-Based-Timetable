"""
SQLAlchemy ORM models — mirrors schema.sql
"""
from sqlalchemy import (
    Column, Integer, String, Enum, Time, ForeignKey, UniqueConstraint, DateTime, func
)
from sqlalchemy.orm import relationship
from .database import Base
import enum


# ── Python Enums ──────────────────────────────────
class SubjectType(str, enum.Enum):
    theory = "theory"
    practical = "practical"


class GroupType(str, enum.Enum):
    division = "division"
    batch = "batch"


class DayOfWeek(str, enum.Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"


# ── Models ────────────────────────────────────────

class AcademicYear(Base):
    __tablename__ = "academic_years"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), unique=True, nullable=False)
    divisions = relationship("Division", back_populates="academic_year", cascade="all,delete")
    subjects = relationship("Subject", back_populates="academic_year", cascade="all,delete")


class GlobalSettings(Base):
    __tablename__ = "global_settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    college_start_time = Column(Time, nullable=False)
    college_end_time = Column(Time, nullable=False)


class Division(Base):
    __tablename__ = "divisions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(10), nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False)
    lunch_start_time = Column(Time, nullable=True)
    lunch_duration_mins = Column(Integer, nullable=True)
    academic_year = relationship("AcademicYear", back_populates="divisions")
    batches = relationship("Batch", back_populates="division", cascade="all,delete")
    __table_args__ = (UniqueConstraint("name", "academic_year_id"),)


class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(10), nullable=False)
    division_id = Column(Integer, ForeignKey("divisions.id", ondelete="CASCADE"), nullable=False)
    division = relationship("Division", back_populates="batches")
    __table_args__ = (UniqueConstraint("name", "division_id"),)


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    type = Column(Enum(SubjectType, name="subject_type", create_type=False), nullable=False)
    sessions_per_week = Column(Integer, default=1, nullable=False)
    duration_mins = Column(Integer, default=60, nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False)
    academic_year = relationship("AcademicYear", back_populates="subjects")


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True)


class Classroom(Base):
    __tablename__ = "classrooms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), unique=True, nullable=False)
    capacity = Column(Integer, default=60)


class Lab(Base):
    __tablename__ = "labs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), unique=True, nullable=False)
    capacity = Column(Integer, default=30)


class Timeslot(Base):
    __tablename__ = "timeslots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    day = Column(Enum(DayOfWeek, name="day_of_week", create_type=False), nullable=False)
    period = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    __table_args__ = (UniqueConstraint("day", "period"),)


class Allocation(Base):
    __tablename__ = "allocations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    group_type = Column(Enum(GroupType, name="group_type", create_type=False), nullable=False)
    group_id = Column(Integer, nullable=False)

    teacher = relationship("Teacher")
    subject = relationship("Subject")

    __table_args__ = (UniqueConstraint("teacher_id", "subject_id", "group_type", "group_id"),)


class Schedule(Base):
    __tablename__ = "schedule"
    id = Column(Integer, primary_key=True, autoincrement=True)
    allocation_id = Column(Integer, ForeignKey("allocations.id", ondelete="CASCADE"), nullable=False)
    day = Column(Enum(DayOfWeek, name="day_of_week", create_type=False), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    room_type = Column(Enum(GroupType, name="group_type", create_type=False), nullable=False)
    room_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    allocation = relationship("Allocation")
