"""
Constraint-Satisfaction Timetable Solver
─────────────────────────────────────────
Generates a clash-free schedule using `python-constraint` with continuous-time blocks.
"""

from __future__ import annotations
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional
from datetime import time

from constraint import Problem

# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class AllocationInfo:
    id: str
    true_allocation_id: int
    duration_mins: int
    teacher_id: int
    subject_id: int
    subject_name: str
    subject_type: str        # 'theory' | 'practical'
    group_type: str          # 'division' | 'batch'
    group_id: int
    group_name: str
    teacher_name: str
    division_id: Optional[int] = None

@dataclass
class RoomInfo:
    id: int
    name: str
    room_type: str           # 'classroom' | 'lab'

@dataclass
class ScheduleSlot:
    allocation_id: str
    true_allocation_id: int
    room_type: str           # 'division' (→ classroom) | 'batch' (→ lab)
    room_id: int
    duration_mins: int
    day: str = ""
    start_time_str: str = ""
    end_time_str: str = ""
    subject_name: str = ""
    teacher_name: str = ""
    room_name: str = ""
    group_name: str = ""
    subject_type: str = ""

# ─── Solver ───────────────────────────────────────────────────────────────────

class TimetableSolver:
    def __init__(
        self,
        allocations: list[AllocationInfo],
        classrooms: list[RoomInfo],
        labs: list[RoomInfo],
        division_batches: dict[int, list[int]],
        div_lunch: dict[int, tuple[int, int]],    # div_id -> (lunch_start_min_offset, lunch_duration_mins)
        college_start: time,
        college_end: time,
        days: list[str] = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    ):
        self.allocations = allocations
        self.classrooms = classrooms
        self.labs = labs
        self.division_batches = division_batches
        self.div_lunch = div_lunch
        self.college_start = college_start
        self.college_end = college_end
        self.days = days
        
        self.college_start_mins = college_start.hour * 60 + college_start.minute
        self.college_end_mins = college_end.hour * 60 + college_end.minute
        self.total_college_mins = self.college_end_mins - self.college_start_mins

    def _mins_to_time_str(self, offset_mins: int) -> str:
        total = self.college_start_mins + offset_mins
        h = total // 60
        m = total % 60
        return f"{h:02d}:{m:02d}"

    def solve(self) -> list[ScheduleSlot]:
        problem = Problem()

        cr_by_id = {cr.id: cr for cr in self.classrooms}
        lab_by_id = {lab.id: lab for lab in self.labs}

        alloc_by_id = {a.id: a for a in self.allocations}
        theory_aids = []
        prac_aids = []

        # Generate base domains. Domain represents (day_name, start_min_offset, room_id)
        # We step by 5 minutes.
        def get_valid_domain(duration, rooms, div_id):
            dom = []
            for day in self.days:
                for rm in rooms:
                    for start in range(0, self.total_college_mins - duration + 1, 5):
                        end = start + duration
                        # Pre-filter lunch breaks completely to reduce domain size natively
                        valid = True
                        if div_id and div_id in self.div_lunch:
                            l_start, l_dur = self.div_lunch[div_id]
                            l_end = l_start + l_dur
                            # Overlap check
                            if start < l_end and end > l_start:
                                valid = False
                        
                        if valid:
                            dom.append((day, start, rm.id))
            return dom

        for a in self.allocations:
            div_id = a.group_id if a.group_type == "division" else a.division_id
            if a.subject_type == "theory":
                dom = get_valid_domain(a.duration_mins, self.classrooms, div_id)
                problem.addVariable(a.id, dom)
                theory_aids.append(a.id)
            else:
                dom = get_valid_domain(a.duration_mins, self.labs, div_id)
                problem.addVariable(a.id, dom)
                prac_aids.append(a.id)

        # ─── 2. Constraints ───
        
        def no_overlap(v1, v2, dur1, dur2):
            # v = (day, start, room_id)
            if v1[0] != v2[0]: return True  # Diff day
            # Same day, check time overlap
            return (v1[1] >= v2[1] + dur2) or (v2[1] >= v1[1] + dur1)

        def room_no_overlap(a1, a2):
            dur1 = a1.duration_mins
            dur2 = a2.duration_mins
            def check(v1, v2):
                if v1[2] != v2[2]: return True  # Diff room
                return no_overlap(v1, v2, dur1, dur2)
            return check

        def time_no_overlap(a1, a2):
            dur1 = a1.duration_mins
            dur2 = a2.duration_mins
            def check(v1, v2):
                return no_overlap(v1, v2, dur1, dur2)
            return check

        # Room Overlap
        for i in range(len(theory_aids)):
            for j in range(i + 1, len(theory_aids)):
                a1, a2 = alloc_by_id[theory_aids[i]], alloc_by_id[theory_aids[j]]
                problem.addConstraint(room_no_overlap(a1, a2), (a1.id, a2.id))

        for i in range(len(prac_aids)):
            for j in range(i + 1, len(prac_aids)):
                a1, a2 = alloc_by_id[prac_aids[i]], alloc_by_id[prac_aids[j]]
                problem.addConstraint(room_no_overlap(a1, a2), (a1.id, a2.id))

        # Teacher Overlap
        teacher_allocs = defaultdict(list)
        for a in self.allocations:
            teacher_allocs[a.teacher_id].append(a.id)

        for aids in teacher_allocs.values():
            for i in range(len(aids)):
                for j in range(i + 1, len(aids)):
                    a1, a2 = alloc_by_id[aids[i]], alloc_by_id[aids[j]]
                    problem.addConstraint(time_no_overlap(a1, a2), (a1.id, a2.id))

        # Division & Batch Group Constraints
        div_theory = defaultdict(list)
        div_prac = defaultdict(list)
        batch_prac = defaultdict(list)

        for a in self.allocations:
            if a.group_type == "division":
                div_theory[a.group_id].append(a.id)
            elif a.group_type == "batch":
                if a.division_id is not None:
                    div_prac[a.division_id].append(a.id)
                batch_prac[a.group_id].append(a.id)

        # Batch internal overlap
        for aids in batch_prac.values():
            for i in range(len(aids)):
                for j in range(i + 1, len(aids)):
                    a1, a2 = alloc_by_id[aids[i]], alloc_by_id[aids[j]]
                    problem.addConstraint(time_no_overlap(a1, a2), (a1.id, a2.id))

        def exact_same_start_time(v1, v2):
            return v1[0] == v2[0] and v1[1] == v2[1]

        for div_id in set(div_theory.keys()).union(div_prac.keys()):
            t_aids = div_theory.get(div_id, [])
            p_aids = div_prac.get(div_id, [])

            # Theory vs Theory
            for i in range(len(t_aids)):
                for j in range(i + 1, len(t_aids)):
                    a1, a2 = alloc_by_id[t_aids[i]], alloc_by_id[t_aids[j]]
                    problem.addConstraint(time_no_overlap(a1, a2), (a1.id, a2.id))

            # Theory vs Practical
            for t_id in t_aids:
                for p_id in p_aids:
                    a1, a2 = alloc_by_id[t_id], alloc_by_id[p_id]
                    problem.addConstraint(time_no_overlap(a1, a2), (a1.id, a2.id))

            # Batch Concurrency: All practicals for a division must be at the SAME time
            for i in range(len(p_aids) - 1):
                problem.addConstraint(exact_same_start_time, (p_aids[i], p_aids[i + 1]))

        # Daily Limits for duplicate allocations
        true_alloc_map = defaultdict(list)
        for a in self.allocations:
            true_alloc_map[a.true_allocation_id].append(a.id)

        def diff_day(v1, v2):
            return v1[0] != v2[0]

        for aids in true_alloc_map.values():
            if len(aids) > 1:
                for i in range(len(aids)):
                    for j in range(i + 1, len(aids)):
                        problem.addConstraint(diff_day, (aids[i], aids[j]))

        # ─── 3. Solve ───
        solution = problem.getSolution()

        if not solution:
            raise RuntimeError("Constraint satisfaction failed. No feasible timetable found.")

        # ─── 4. Map Back ───
        schedule = []
        for alloc_id, value in solution.items():
            day, start_min, room_id = value
            alloc = alloc_by_id[alloc_id]

            if alloc.subject_type == "theory":
                room_type = "division"
                room = cr_by_id[room_id]
            else:
                room_type = "batch"
                room = lab_by_id[room_id]

            schedule.append(
                ScheduleSlot(
                    allocation_id=alloc.id,
                    true_allocation_id=alloc.true_allocation_id,
                    room_type=room_type,
                    room_id=room.id,
                    duration_mins=alloc.duration_mins,
                    day=day,
                    start_time_str=self._mins_to_time_str(start_min),
                    end_time_str=self._mins_to_time_str(start_min + alloc.duration_mins),
                    subject_name=alloc.subject_name,
                    teacher_name=alloc.teacher_name,
                    room_name=room.name,
                    group_name=alloc.group_name,
                    subject_type=alloc.subject_type,
                )
            )

        return schedule
