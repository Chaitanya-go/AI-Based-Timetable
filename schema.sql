-- ============================================================
-- AI-Powered Timetable Generation System — PostgreSQL Schema
-- ============================================================

-- ── Enums ────────────────────────────────────────────────────
CREATE TYPE subject_type  AS ENUM ('theory', 'practical');
CREATE TYPE group_type    AS ENUM ('division', 'batch');
CREATE TYPE day_of_week   AS ENUM ('monday','tuesday','wednesday','thursday','friday','saturday');

-- ── Global Settings ──────────────────────────────────────────
CREATE TABLE global_settings (
    id SERIAL PRIMARY KEY,
    college_start_time TIME NOT NULL,
    college_end_time TIME NOT NULL
);

-- ── Academic Years ───────────────────────────────────────────
CREATE TABLE academic_years (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(20) NOT NULL UNIQUE   -- '2nd Year', '3rd Year', 'Final Year'
);

-- ── Divisions ────────────────────────────────────────────────
CREATE TABLE divisions (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(10) NOT NULL,          -- 'A', 'B', 'C'
    academic_year_id INTEGER NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    lunch_start_time TIME,
    lunch_duration_mins INTEGER DEFAULT 45,
    UNIQUE (name, academic_year_id)
);

-- ── Batches ──────────────────────────────────────────────────
CREATE TABLE batches (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(10) NOT NULL,               -- 'A1', 'A2', 'A3', 'A4'
    division_id INTEGER NOT NULL REFERENCES divisions(id) ON DELETE CASCADE,
    UNIQUE (name, division_id)
);

-- ── Subjects ─────────────────────────────────────────────────
CREATE TABLE subjects (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    code             VARCHAR(20)  NOT NULL UNIQUE,
    type             subject_type NOT NULL,          -- 'theory' or 'practical'
    sessions_per_week INTEGER DEFAULT 1 NOT NULL,
    duration_mins    INTEGER DEFAULT 60 NOT NULL,
    academic_year_id INTEGER NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE
);

-- ── Teachers ─────────────────────────────────────────────────
CREATE TABLE teachers (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE
);

-- ── Classrooms (Theory rooms) ────────────────────────────────
CREATE TABLE classrooms (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(20) NOT NULL UNIQUE,            -- 'CR-1' … 'CR-7'
    capacity INTEGER DEFAULT 60
);

-- ── Labs (Practical rooms) ───────────────────────────────────
CREATE TABLE labs (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(20) NOT NULL UNIQUE,            -- 'LAB-1' … 'LAB-5'
    capacity INTEGER DEFAULT 30
);

-- (Timeslots table removed in favor of dynamic continuous time calculations)

-- ── Allocations (Teacher × Subject × Group) ─────────────────
--    group_type + group_id form a polymorphic FK:
--      • group_type = 'division' → group_id references divisions.id
--      • group_type = 'batch'    → group_id references batches.id
CREATE TABLE allocations (
    id           SERIAL PRIMARY KEY,
    teacher_id   INTEGER    NOT NULL REFERENCES teachers(id)  ON DELETE CASCADE,
    subject_id   INTEGER    NOT NULL REFERENCES subjects(id)  ON DELETE CASCADE,
    group_type   group_type NOT NULL,
    group_id     INTEGER    NOT NULL,
    UNIQUE (teacher_id, subject_id, group_type, group_id)
);

-- ── Schedule (Generated timetable entries) ───────────────────
CREATE TABLE schedule (
    id            SERIAL PRIMARY KEY,
    allocation_id INTEGER NOT NULL REFERENCES allocations(id) ON DELETE CASCADE,
    day           day_of_week NOT NULL,
    start_time    TIME NOT NULL,
    end_time      TIME NOT NULL,
    room_type     group_type NOT NULL,                -- reuse enum: 'division'→classroom, 'batch'→lab
    room_id       INTEGER    NOT NULL,                -- references classrooms.id or labs.id
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast clash detection during scheduling
CREATE INDEX idx_schedule_time           ON schedule(day, start_time);
CREATE INDEX idx_schedule_room           ON schedule(room_type, room_id, day, start_time);
CREATE INDEX idx_allocations_teacher     ON allocations(teacher_id);
CREATE INDEX idx_allocations_group       ON allocations(group_type, group_id);

-- ── Seed: Infrastructure ─────────────────────────────────────
INSERT INTO academic_years (name) VALUES ('2nd Year'), ('3rd Year'), ('Final Year');

INSERT INTO classrooms (name) VALUES
    ('CR-1'),('CR-2'),('CR-3'),('CR-4'),('CR-5'),('CR-6'),('CR-7');

INSERT INTO labs (name) VALUES
    ('LAB-1'),('LAB-2'),('LAB-3'),('LAB-4'),('LAB-5');

-- Seed: Global Settings
INSERT INTO global_settings (college_start_time, college_end_time) VALUES ('09:00', '17:00');
