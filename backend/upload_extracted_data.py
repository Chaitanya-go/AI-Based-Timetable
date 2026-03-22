import urllib.request
import json

base_url = "http://localhost:8000/api"
teachers_url = f"{base_url}/teachers"
divisions_url = f"{base_url}/divisions"
subjects_url = f"{base_url}/subjects"
allocations_url = f"{base_url}/allocations"
settings_url = f"{base_url}/global-settings"

def __request(method, url, data=None):
    req = urllib.request.Request(url, method=method)
    if data is not None:
        req.add_header('Content-Type', 'application/json')
        data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req, data=data) as response:
            return json.loads(response.read().decode()) if response.status in [200, 201] else {}
    except Exception as e:
        print(f"Error {method} {url}: {e}")
        return {}

# Configure College Global Operating Hours
__request("PUT", f"{base_url}/global-settings", {"college_start_time": "08:40", "college_end_time": "17:00"})
print("Updated Global Operating Hours")

teachers = [
    "Dr. Shivganga V. Gavhane", "Mrs. Rachana R. Mudholkar", "Mrs. Shailaja N. Lohar", 
    "Dr. Minal R. Bodke", "Mrs. Shrutika Menkudale", "Mrs. Tejali V. Katkar", 
    "Mrs. Priyadarshini N. Doke", "Mrs. Swati K. Rajput", "Mrs. Deepa P. Mahajan", 
    "Dr. Archana Kolin", "Mrs. Madhavi Kapru", "Mrs. Rutuja S. Magar", 
    "Dr. Govind R. Suryawanshi", "Dr. Yogeshwari Y. Mahajan", "Mrs. Ketaki S. Chinchane", 
    "Mrs. Dipti S. Chaudhari", "Dr. Vaishali P. Latke", "Mrs. Trupti G. Lonkar", 
    "Mrs. Sonali S. Lunawat", "NAJ" # Placeholder for missing internship guide
]

for t in teachers:
    __request("POST", teachers_url, {"name": t, "email": f"{t.split()[-1].lower()}@college.edu"})

print("Inserted Teachers")

divisions = [
    {"name": "A", "academic_year_name": "TE 2025-26", "batches": [{"name": f"TA{i}"} for i in range(1,5)], "lunch_start_time": "13:00", "lunch_duration_mins": 40},
    {"name": "B", "academic_year_name": "TE 2025-26", "batches": [{"name": f"TB{i}"} for i in range(1,5)], "lunch_start_time": "13:00", "lunch_duration_mins": 40},
    {"name": "C", "academic_year_name": "TE 2025-26", "batches": [{"name": f"TC{i}"} for i in range(1,5)], "lunch_start_time": "13:00", "lunch_duration_mins": 40},
    {"name": "D", "academic_year_name": "TE 2025-26", "batches": [{"name": f"TD{i}"} for i in range(1,5)], "lunch_start_time": "13:00", "lunch_duration_mins": 40}
]

for div in divisions:
    __request("POST", divisions_url, div)
    
print("Inserted Divisions and Batches")

subjects = [
    {"name": "DSBDA", "type": "theory", "duration_mins": 50, "sessions_per_week": 3, "room_req": "Classroom"},
    {"name": "WT", "type": "theory", "duration_mins": 50, "sessions_per_week": 3, "room_req": "Classroom"},
    {"name": "AI", "type": "theory", "duration_mins": 50, "sessions_per_week": 3, "room_req": "Classroom"},
    {"name": "CC", "type": "theory", "duration_mins": 50, "sessions_per_week": 3, "room_req": "Classroom"},
    {"name": "AIML-HONOR", "type": "theory", "duration_mins": 60, "sessions_per_week": 4, "room_req": "Classroom"},
    {"name": "DSBDAL", "type": "practical", "duration_mins": 100, "sessions_per_week": 1, "room_req": "Lab 527"},
    {"name": "WTL", "type": "practical", "duration_mins": 100, "sessions_per_week": 1, "room_req": "Lab 512"},
    {"name": "LP-II", "type": "practical", "duration_mins": 100, "sessions_per_week": 1, "room_req": "Lab 517"},
    {"name": "INTERNSHIP", "type": "practical", "duration_mins": 100, "sessions_per_week": 1, "room_req": "Seminar Hall"}
]

for s in subjects:
    __request("POST", f"{base_url}/subjects", s)

print("Inserted Subjects")

# Get IDs for allocations mappings
t_map = {t['name']: t['id'] for t in __request("GET", teachers_url) or []}
d_map = {d['name']: d['id'] for d in __request("GET", divisions_url) or []}
s_map = {s['name']: s['id'] for s in __request("GET", subjects_url) or []}
b_map = {}
for d in __request("GET", divisions_url) or []:
    if 'batches' in d:
        for b in d['batches']:
            b_map[b['name']] = b['id']

allocations = [
    # ---- DIV A (Theory) ----
    ("Mrs. Dipti S. Chaudhari", "DSBDA", "A", None),
    ("Mrs. Deepa P. Mahajan", "WT", "A", None),
    ("Mrs. Tejali V. Katkar", "AI", "A", None),
    ("Dr. Vaishali P. Latke", "CC", "A", None),
    ("Mrs. Tejali V. Katkar", "AIML-HONOR", "A", None),
    # ---- DIV A (Practical) ----
    ("Mrs. Dipti S. Chaudhari", "DSBDAL", "A", "TA1"),
    ("Dr. Vaishali P. Latke", "LP-II", "A", "TA2"),
    ("Mrs. Trupti G. Lonkar", "LP-II", "A", "TA3"),
    ("Mrs. Rutuja S. Magar", "DSBDAL", "A", "TA4"),
    ("Mrs. Deepa P. Mahajan", "WTL", "A", "TA1"),
    ("Mrs. Deepa P. Mahajan", "WTL", "A", "TA2"),
    ("Mrs. Deepa P. Mahajan", "WTL", "A", "TA3"),
    ("Mrs. Deepa P. Mahajan", "WTL", "A", "TA4"),
    ("NAJ", "INTERNSHIP", "A", "TA1"),
    ("NAJ", "INTERNSHIP", "A", "TA2"),
    
    # ---- DIV B (Theory) ----
    ("Mrs. Swati K. Rajput", "DSBDA", "B", None),
    ("Mrs. Deepa P. Mahajan", "WT", "B", None),
    ("Dr. Archana Kolin", "AI", "B", None),
    ("Mrs. Madhavi Kapru", "CC", "B", None),
    ("Mrs. Tejali V. Katkar", "AIML-HONOR", "B", None),
    # ---- DIV B (Practical) ----
    ("Mrs. Swati K. Rajput", "DSBDAL", "B", "TB1"),
    ("Mrs. Rutuja S. Magar", "DSBDAL", "B", "TB2"),
    ("Mrs. Swati K. Rajput", "DSBDAL", "B", "TB4"),
    ("Dr. Archana Kolin", "LP-II", "B", "TB1"),
    ("Mrs. Madhavi Kapru", "LP-II", "B", "TB2"),
    ("Dr. Archana Kolin", "LP-II", "B", "TB3"),
    ("Mrs. Madhavi Kapru", "LP-II", "B", "TB4"),
    
    # ---- DIV C (Theory) ----
    ("Dr. Yogeshwari Y. Mahajan", "DSBDA", "C", None),
    ("Mrs. Shrutika Menkudale", "WT", "C", None),
    ("Mrs. Shailaja N. Lohar", "AI", "C", None),
    ("Mrs. Ketaki S. Chinchane", "CC", "C", None),
    ("Mrs. Tejali V. Katkar", "AIML-HONOR", "C", None),
    # ---- DIV C (Practical) ----
    ("Dr. Yogeshwari Y. Mahajan", "DSBDAL", "C", "TC1"),
    ("Mrs. Shrutika Menkudale", "WTL", "C", "TC2"),
    ("Mrs. Shailaja N. Lohar", "LP-II", "C", "TC3"),
    ("Mrs. Ketaki S. Chinchane", "CC", "C", "TC4"),

    # ---- DIV D (Theory) ----
    ("Dr. Shivganga V. Gavhane", "DSBDA", "D", None),
    ("Mrs. Rachana R. Mudholkar", "WT", "D", None),
    ("Mrs. Shailaja N. Lohar", "AI", "D", None),
    ("Dr. Minal R. Bodke", "CC", "D", None),
    ("Mrs. Tejali V. Katkar", "AIML-HONOR", "D", None),
    # ---- DIV D (Practical) ----
    ("Dr. Shivganga V. Gavhane", "DSBDAL", "D", "TD1"),
    ("Mrs. Rachana R. Mudholkar", "WTL", "D", "TD2"),
    ("Mrs. Shailaja N. Lohar", "LP-II", "D", "TD3"),
    ("Dr. Minal R. Bodke", "CC", "D", "TD4"),
]

for t_name, s_name, d_name, b_name in allocations:
    if t_name not in t_map or s_name not in s_map or d_name not in d_map:
        continue
    
    payload = {
        "teacher_id": t_map[t_name],
        "subject_id": s_map[s_name],
        "division_id": d_map[d_name],
        "batch_id": b_map[b_name] if b_name else None
    }
    __request("POST", allocations_url, payload)

print("Inserted All Extracted Workload Allocations")
