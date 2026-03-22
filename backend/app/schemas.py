"""
Pydantic models for request / response validation.
"""
from pydantic import BaseModel
from typing import Optional
from enum import Enum


class SubjectTypeEnum(str, Enum):
    theory = "theory"
    practical = "practical"


class GroupTypeEnum(str, Enum):
    division = "division"
    batch = "batch"


# ── Global Settings ──
class GlobalSettingsCreate(BaseModel):
    college_start_time: str
    college_end_time: str

class GlobalSettingsOut(BaseModel):
    id: int
    college_start_time: str
    college_end_time: str
    class Config:
        from_attributes = True


# ── Teachers ──
class TeacherCreate(BaseModel):
    name: str
    email: Optional[str] = None

class TeacherOut(BaseModel):
    id: int
    name: str
    email: Optional[str]
    class Config:
        from_attributes = True


# ── Academic Years ──
class AcademicYearOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True


# ── Divisions ──
class DivisionCreate(BaseModel):
    name: str
    academic_year_id: int
    lunch_start_time: Optional[str] = None
    lunch_duration_mins: Optional[int] = None

class BatchNested(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class DivisionOut(BaseModel):
    id: int
    name: str
    academic_year_id: int
    academic_year_name: Optional[str] = None
    lunch_start_time: Optional[str] = None
    lunch_duration_mins: Optional[int] = None
    batches: list[BatchNested] = []
    class Config:
        from_attributes = True


# ── Batches ──
class BatchCreate(BaseModel):
    name: str
    division_id: int

class BatchOut(BaseModel):
    id: int
    name: str
    division_id: int
    division_name: Optional[str] = None
    class Config:
        from_attributes = True


# ── Subjects ──
class SubjectCreate(BaseModel):
    name: str
    code: str
    type: SubjectTypeEnum
    sessions_per_week: int = 1
    duration_mins: int = 60
    academic_year_id: int

class SubjectOut(BaseModel):
    id: int
    name: str
    code: str
    type: SubjectTypeEnum
    sessions_per_week: int
    duration_mins: int
    academic_year_id: int
    class Config:
        from_attributes = True


# ── Allocations ──
class AllocationItem(BaseModel):
    teacher_id: int
    subject_id: int
    group_type: GroupTypeEnum
    group_id: int

class AllocationsBulk(BaseModel):
    allocations: list[AllocationItem]

class AllocationOut(BaseModel):
    id: int
    teacher_id: int
    subject_id: int
    group_type: GroupTypeEnum
    group_id: int
    class Config:
        from_attributes = True


# ── Rooms ──
class RoomOut(BaseModel):
    id: int
    name: str
    capacity: Optional[int] = None
    class Config:
        from_attributes = True


# ── Schedule ──
class ScheduleEntry(BaseModel):
    day: str
    start_time: str
    end_time: str
    subject: str
    teacher: str
    room: str
    type: str
    group: str
