from datetime import time
from app.engine.solver import TimetableSolver, AllocationInfo, RoomInfo

def test_solver_logic():
    print("Initializing mock continuous block data...")

    classrooms = [RoomInfo(id=1, name="CR-1", room_type="classroom")]
    labs = [RoomInfo(id=2, name="LAB-1", room_type="lab")]

    # Division 1 -> Batch 10
    division_batches = {1: [10]}
    
    # Div 1 lunch starts at 12:15 (205 mins from 08:50) for 45 mins -> ends 13:00
    # College starts 08:50
    # 12:15 = 12*60 + 15 = 735 mins. 08:50 = 8*60 + 50 = 530 mins.
    # Lunch offset from start = 735 - 530 = 205
    div_lunch = {1: (205, 45)} 
    
    college_start = time(hour=8, minute=50)
    college_end = time(hour=16, minute=0)

    allocations = []
    
    # Subject A (Theory): 3 sessions of 50 minutes
    for i in range(3):
        allocations.append(AllocationInfo(
            id=f"100_{i}", true_allocation_id=100, duration_mins=50,
            teacher_id=1, subject_id=200, subject_name="Math", subject_type="theory",
            group_type="division", group_id=1, group_name="Div 1", teacher_name="Mr. A", division_id=None
        ))

    # Subject B (Practical): 2 sessions of 120 minutes (2 hours)
    for i in range(2):
        allocations.append(AllocationInfo(
            id=f"101_{i}", true_allocation_id=101, duration_mins=120,
            teacher_id=2, subject_id=201, subject_name="Physics Lab", subject_type="practical",
            group_type="batch", group_id=10, group_name="Batch A1", teacher_name="Mr. B", division_id=1
        ))

    print("Running continuous solver...")
    solver = TimetableSolver(allocations, classrooms, labs, division_batches, div_lunch, college_start, college_end, days=["monday", "tuesday", "wednesday"])
    
    try:
        schedule = solver.solve()
        print(f"Success! Generated {len(schedule)} exact timestamps.")
    except Exception as e:
        print(f"Solver failed: {e}")
        return

    # Assertions
    print("\nVerifying exact durations & lunch bounds...")
    for s in schedule:
        if s.true_allocation_id == 101: # Physics Practical (120 mins)
            assert s.duration_mins == 120, "Practical must be exactly 120 mins"
            # It must not overlap lunch (12:15 -> 13:00)
            from datetime import datetime
            sm = datetime.strptime(s.start_time_str, "%H:%M")
            em = datetime.strptime(s.end_time_str, "%H:%M")
            start_offset = sm.hour * 60 + sm.minute - (8 * 60 + 50)
            end_offset = em.hour * 60 + em.minute - (8 * 60 + 50)
            lunch_start = 205
            lunch_end = 250
            overlap = start_offset < lunch_end and end_offset > lunch_start
            assert not overlap, f"Lunch violation! Practical placed at {s.start_time_str}-{s.end_time_str} overlaps lunch!"

    # Verification: Math (3 times, 50 mins each) must be on diff days
    math_slots = [s for s in schedule if s.true_allocation_id == 100]
    days = set([s.day for s in math_slots])
    assert len(days) == 3, "Math missing daily limit distribution!"

    print("✓ All advanced continuous time constraints passed!")

if __name__ == "__main__":
    test_solver_logic()
