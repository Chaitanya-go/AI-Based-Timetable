"""
OR-Tools CP-SAT Timetable Solver
─────────────────────────────────────────────────────────────────────────────
Drop-in replacement for the python-constraint version.

Key differences:
  • Variables are integers (day index, scaled start time, room index),
    not giant tuple domains.
  • Constraints are native C++ propagators via AddBoolOr / OnlyEnforceIf.
  • CDCL search with clause learning + parallel threads.
  • STEP=5 scaling: all time values are divided by 5 to shrink domains.

Install:  pip install ortools
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import time
import time as pytime
from typing import DefaultDict, Dict, List, Optional, Tuple

from ortools.sat.python import cp_model


# ─── Data Structures (identical to original) ──────────────────────────────────

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
    room_type: str
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
    division_id: Optional[int] = None


# ─── Solver ───────────────────────────────────────────────────────────────────

class TimetableSolver:
    """
    Timetable solver using OR-Tools CP-SAT.

    Workflow
    ────────
    1. For every allocation create three integer variables:
         day_var    ∈ [0, num_days − 1]
         start_var  ∈ [0, (total_mins − duration) / STEP]   (scaled)
         room_var   ∈ [0, num_rooms − 1]
    2. Express every constraint as a disjunction of boolean implications
       (AddBoolOr pattern) so the C++ solver propagates them natively.
    3. Solve with the CP-SAT CDCL engine (parallel, clause-learning).
    4. Read back integer values and translate to ScheduleSlot objects.
    """

    # ── Time-scaling constant ─────────────────────────────────────────────────
    # All start-time domains are divided by STEP (minutes).
    # Since every lecture / practical duration (50/100 mins) and lunch (40 mins)
    # is a multiple of 10, this is lossless and speeds up the search 2×.
    STEP = 10

    def __init__(
        self,
        allocations: list[AllocationInfo],
        classrooms: list[RoomInfo],
        labs: list[RoomInfo],
        division_batches: dict[int, list[int]],
        div_lunch: dict[int, tuple[int, int]],
        college_start: time,
        college_end: time,
        days: list[str] | None = None,
        max_solve_seconds: float = 60.0,
        num_workers: int = 8,
    ):
        self.allocations = allocations
        self.classrooms = classrooms
        self.labs = labs
        self.division_batches = division_batches
        self.div_lunch = div_lunch           # div_id → (lunch_start_offset_mins, lunch_duration_mins)
        self.college_start = college_start
        self.college_end = college_end
        self.days = days or ["monday", "tuesday", "wednesday", "thursday", "friday"]
        self.max_solve_seconds = max_solve_seconds
        self.num_workers = num_workers

        self._college_start_mins = college_start.hour * 60 + college_start.minute
        self._college_end_mins   = college_end.hour   * 60 + college_end.minute
        self._total_college_mins = self._college_end_mins - self._college_start_mins

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _mins_to_time_str(self, offset_mins: int) -> str:
        total = self._college_start_mins + offset_mins
        return f"{total // 60:02d}:{total % 60:02d}"

    def _scaled(self, minutes: int) -> int:
        """Convert real minutes to STEP-scaled units."""
        return minutes // self.STEP

    # ── Main solve ────────────────────────────────────────────────────────────

    def solve(self) -> list[ScheduleSlot]:
        model  = cp_model.CpModel()
        S      = self.STEP                                # shorthand
        T      = self._scaled(self._total_college_mins)  # scaled total mins
        N_days = len(self.days)

        alloc_by_id: Dict[str, AllocationInfo] = {a.id: a for a in self.allocations}

        # ── Step 1 : Create integer variables ─────────────────────────────────
        #
        # For each allocation we create exactly THREE integer variables instead
        # of one variable whose domain is a huge list of (day, start, room)
        # tuples. This gives the solver much finer-grained propagation.
        #
        # day_var  : which weekday (index into self.days)
        # start_var: start time in STEP-scaled minutes from college_start
        # room_var : index into self.classrooms (theory) or self.labs (practical)

        day_vars:      Dict[str, cp_model.IntVar] = {}
        start_vars:    Dict[str, cp_model.IntVar] = {}
        room_idx_vars: Dict[str, cp_model.IntVar] = {}

        for a in self.allocations:
            dur_s     = self._scaled(a.duration_mins)   # duration in scaled units
            max_start = T - dur_s                        # latest valid start

            day_vars[a.id]   = model.NewIntVar(0, N_days - 1, f"day_{a.id}")
            start_vars[a.id] = model.NewIntVar(0, max_start,   f"start_{a.id}")

            n_rooms = len(self.classrooms) if a.subject_type == "theory" else len(self.labs)
            room_idx_vars[a.id] = model.NewIntVar(0, n_rooms - 1, f"room_{a.id}")

        # ── Step 2 : Lunch-break constraints ──────────────────────────────────
        #
        # Instead of filtering lunch slots from the domain upfront (as the
        # original does), we add a simple binary constraint per allocation:
        #
        #   end_before_lunch  →  start + duration ≤ lunch_start
        #   start_after_lunch →  start ≥ lunch_end
        #
        # AddBoolOr([end_before_lunch, start_after_lunch]) means
        # "at least one of these must be true", i.e. no overlap with lunch.
        # The solver picks whichever satisfies the rest of the schedule.

        for a in self.allocations:
            div_id = a.group_id if a.group_type == "division" else a.division_id
            if div_id is None or div_id not in self.div_lunch:
                continue

            l_start_min, l_dur = self.div_lunch[div_id]
            ls  = self._scaled(l_start_min)               # lunch start (scaled)
            le  = self._scaled(l_start_min + l_dur)       # lunch end   (scaled)
            dur = self._scaled(a.duration_mins)

            before = model.NewBoolVar(f"lunch_before_{a.id}")
            after  = model.NewBoolVar(f"lunch_after_{a.id}")

            # If before=True  → class must end by lunch start
            model.Add(start_vars[a.id] + dur <= ls).OnlyEnforceIf(before)
            # If after=True   → class must start after lunch ends
            model.Add(start_vars[a.id] >= le).OnlyEnforceIf(after)
            # At least one must hold
            model.AddBoolOr([before, after])

        # ── Step 3 : Constraint helpers ───────────────────────────────────────
        #
        # Both helpers use the "disjunctive encoding" pattern:
        #
        #   AddBoolOr([cond1, cond2, cond3, ...])
        #
        # which says "at least one condition must be true".
        # OnlyEnforceIf(b) means "this Add(...) is active ONLY when b=True".
        # If b is False, the constraint is simply ignored — the solver decides
        # which b to set to True to make the BoolOr satisfied.
        #
        # This is the standard CP-SAT pattern for "if A then B" logic and is
        # compiled to C++ bitmask operations internally — no Python overhead.

        def no_time_overlap(aid1: str, aid2: str) -> None:
            """
            Two allocations must not overlap in time on the same day.
            Disjunction: different_day  OR  a1_ends_before_a2  OR  a2_ends_before_a1
            """
            dur1 = self._scaled(alloc_by_id[aid1].duration_mins)
            dur2 = self._scaled(alloc_by_id[aid2].duration_mins)

            # Bool: "they are on different days"
            diff_day = model.NewBoolVar(f"td_{aid1}_{aid2}")
            model.Add(day_vars[aid1] != day_vars[aid2]).OnlyEnforceIf(diff_day)

            # Bool: "a1 finishes before a2 starts"
            a1_first = model.NewBoolVar(f"t1_{aid1}_{aid2}")
            model.Add(start_vars[aid1] + dur1 <= start_vars[aid2]).OnlyEnforceIf(a1_first)

            # Bool: "a2 finishes before a1 starts"
            a2_first = model.NewBoolVar(f"t2_{aid1}_{aid2}")
            model.Add(start_vars[aid2] + dur2 <= start_vars[aid1]).OnlyEnforceIf(a2_first)

            # At least one of the three must be true
            model.AddBoolOr([diff_day, a1_first, a2_first])

        def no_room_overlap(aid1: str, aid2: str) -> None:
            """
            Two allocations in the same room pool must not overlap.
            Disjunction: diff_day  OR  diff_room  OR  a1_first  OR  a2_first
            """
            dur1 = self._scaled(alloc_by_id[aid1].duration_mins)
            dur2 = self._scaled(alloc_by_id[aid2].duration_mins)

            diff_day  = model.NewBoolVar(f"rd_{aid1}_{aid2}")
            diff_room = model.NewBoolVar(f"rr_{aid1}_{aid2}")
            a1_first  = model.NewBoolVar(f"r1_{aid1}_{aid2}")
            a2_first  = model.NewBoolVar(f"r2_{aid1}_{aid2}")

            model.Add(day_vars[aid1]      != day_vars[aid2]).OnlyEnforceIf(diff_day)
            model.Add(room_idx_vars[aid1] != room_idx_vars[aid2]).OnlyEnforceIf(diff_room)
            model.Add(start_vars[aid1] + dur1 <= start_vars[aid2]).OnlyEnforceIf(a1_first)
            model.Add(start_vars[aid2] + dur2 <= start_vars[aid1]).OnlyEnforceIf(a2_first)

            model.AddBoolOr([diff_day, diff_room, a1_first, a2_first])

        # ── Step 4 : Apply all constraints ───────────────────────────────────
        # The structure here is identical to the original code so it's easy
        # to audit. Only the constraint API has changed.

        theory_aids: List[str] = [a.id for a in self.allocations if a.subject_type == "theory"]
        prac_aids:   List[str] = [a.id for a in self.allocations if a.subject_type != "theory"]

        # ── 4a. Room clashes ──────────────────────────────────────────────────
        # Two theory classes can't share a classroom at the same time.
        # Two practicals can't share a lab at the same time.
        # (Theory vs practical never compete for the same room pool.)
        for i in range(len(theory_aids)):
            for j in range(i + 1, len(theory_aids)):
                no_room_overlap(theory_aids[i], theory_aids[j])

        for i in range(len(prac_aids)):
            for j in range(i + 1, len(prac_aids)):
                no_room_overlap(prac_aids[i], prac_aids[j])

        # ── 4b. Teacher clashes ───────────────────────────────────────────────
        # A teacher cannot be in two places at the same time.
        teacher_allocs: DefaultDict[int, List[str]] = defaultdict(list)
        for a in self.allocations:
            teacher_allocs[a.teacher_id].append(a.id)

        for aids in teacher_allocs.values():
            for i in range(len(aids)):
                for j in range(i + 1, len(aids)):
                    no_time_overlap(aids[i], aids[j])

        # ── Step 4c. Division / batch group clashes ────────────────────────────────────
        div_theory: DefaultDict[int, List[str]] = defaultdict(list)
        div_prac:   DefaultDict[int, List[str]] = defaultdict(list)
        batch_prac: DefaultDict[int, List[str]] = defaultdict(list)

        for a in self.allocations:
            if a.group_type == "division":
                div_theory[a.group_id].append(a.id)
            elif a.group_type == "batch":
                if a.division_id is not None:
                    div_prac[a.division_id].append(a.id)
                batch_prac[a.group_id].append(a.id)

        # Batch-internal: no two sessions for the same batch overlap in time
        for aids in batch_prac.values():
            for i in range(len(aids)):
                for j in range(i + 1, len(aids)):
                    no_time_overlap(aids[i], aids[j])

        for div_id in set(div_theory.keys()) | set(div_prac.keys()):
            t_aids = div_theory.get(div_id, [])
            p_aids = div_prac.get(div_id, [])

            # Theory vs Theory for same division
            for i in range(len(t_aids)):
                for j in range(i + 1, len(t_aids)):
                    no_time_overlap(t_aids[i], t_aids[j])

            # Theory vs Practical for same division
            for t_id in t_aids:
                for p_id in p_aids:
                    no_time_overlap(t_id, p_id)

        # ── 4d. Daily spread (no duplicate subject on the same day) ───────────
        # Each true_allocation_id may correspond to several weekly sessions.
        # They must land on different days.
        true_alloc_map: DefaultDict[int, List[str]] = defaultdict(list)
        for a in self.allocations:
            true_alloc_map[a.true_allocation_id].append(a.id)

        for aids in true_alloc_map.values():
            if len(aids) > 1:
                for i in range(len(aids)):
                    for j in range(i + 1, len(aids)):
                        model.Add(day_vars[aids[i]] != day_vars[aids[j]])

        # ── Step 5 : Solve ────────────────────────────────────────────────────
        #
        # CP-SAT uses a CDCL (Conflict-Driven Clause Learning) engine:
        #   • When a conflict is found, it derives a "no-good" clause that
        #     prunes the same conflict from appearing again.
        #   • num_search_workers runs independent searches in parallel,
        #     each with different heuristics — first to find a solution wins.
        #   • max_time_in_seconds acts as a safety valve; if a feasible
        #     solution has been found by then it is returned, otherwise
        #     we raise an error.

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.max_solve_seconds
        solver.parameters.num_search_workers  = self.num_workers

        t0 = pytime.time()
        status = solver.Solve(model)
        t1 = pytime.time()
        print(f"DEBUG: Solver finished in {t1 - t0:.2f}s with status {status}")

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError(
                "CP-SAT could not find a feasible timetable. "
                "Check that your constraints are not over-constrained."
            )

        # ── Step 6 : Extract results ──────────────────────────────────────────
        # solver.Value(var) returns the integer the solver assigned to each var.
        # We unscale start times (multiply by STEP) before converting to strings.

        cr_by_idx  = {i: cr  for i, cr  in enumerate(self.classrooms)}
        lab_by_idx = {i: lab for i, lab in enumerate(self.labs)}

        schedule: list[ScheduleSlot] = []
        for a in self.allocations:
            day_idx     = solver.Value(day_vars[a.id])
            start_s     = solver.Value(start_vars[a.id])   # scaled
            room_idx    = solver.Value(room_idx_vars[a.id])
            start_min   = start_s * self.STEP               # real minutes

            if a.subject_type == "theory":
                room      = cr_by_idx[room_idx]
                room_type = "division"
            else:
                room      = lab_by_idx[room_idx]
                room_type = "batch"

            schedule.append(
                ScheduleSlot(
                    allocation_id      = a.id,
                    true_allocation_id = a.true_allocation_id,
                    room_type          = room_type,
                    room_id            = room.id,
                    duration_mins      = a.duration_mins,
                    day                = self.days[day_idx],
                    start_time_str     = self._mins_to_time_str(start_min),
                    end_time_str       = self._mins_to_time_str(start_min + a.duration_mins),
                    subject_name       = a.subject_name,
                    teacher_name       = a.teacher_name,
                    room_name          = room.name,
                    group_name         = a.group_name,
                    subject_type       = a.subject_type,
                    division_id        = a.division_id,
                )
            )

        return schedule
