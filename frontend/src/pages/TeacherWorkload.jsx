import { useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { HiOutlinePlusCircle, HiOutlineCheckCircle } from 'react-icons/hi2'
import SubjectAssignment from '../components/SubjectAssignment.jsx'
import * as api from '../services/api.js'

let nextId = 1

// ── Mock data for standalone mode (no backend) ──
const MOCK_TEACHERS = [
  { id: 1, name: 'Dr. Sharma', email: 'sharma@college.edu' },
  { id: 2, name: 'Prof. Patel', email: 'patel@college.edu' },
  { id: 3, name: 'Dr. Kulkarni', email: 'kulkarni@college.edu' },
  { id: 4, name: 'Prof. Deshmukh', email: 'deshmukh@college.edu' },
  { id: 5, name: 'Dr. Joshi', email: 'joshi@college.edu' },
  { id: 6, name: 'Prof. Gupta', email: 'gupta@college.edu' },
]

const MOCK_SUBJECTS = [
  { id: 1, name: 'Data Structures', code: 'DS201', type: 'theory', academic_year_id: 1, sessions_per_week: 3, duration_mins: 60 },
  { id: 2, name: 'DS Lab', code: 'DSL201', type: 'practical', academic_year_id: 1, sessions_per_week: 2, duration_mins: 120 },
  { id: 3, name: 'Database Management', code: 'DBMS301', type: 'theory', academic_year_id: 2, sessions_per_week: 3, duration_mins: 60 },
  { id: 4, name: 'DBMS Lab', code: 'DBMSL301', type: 'practical', academic_year_id: 2, sessions_per_week: 2, duration_mins: 120 },
  { id: 5, name: 'Machine Learning', code: 'ML401', type: 'theory', academic_year_id: 3, sessions_per_week: 3, duration_mins: 60 },
  { id: 6, name: 'ML Lab', code: 'MLL401', type: 'practical', academic_year_id: 3, sessions_per_week: 2, duration_mins: 120 },
  { id: 7, name: 'Operating Systems', code: 'OS301', type: 'theory', academic_year_id: 2, sessions_per_week: 3, duration_mins: 60 },
  { id: 8, name: 'OS Lab', code: 'OSL301', type: 'practical', academic_year_id: 2, sessions_per_week: 2, duration_mins: 120 },
]

const MOCK_DIVISIONS = [
  {
    id: 1, name: 'A', academic_year_id: 1, academic_year_name: '2nd Year', lunch_start_time: '12:15', lunch_duration_mins: 60,
    batches: [
      { id: 1, name: 'A1' }, { id: 2, name: 'A2' },
      { id: 3, name: 'A3' }, { id: 4, name: 'A4' },
    ],
  },
  {
    id: 2, name: 'B', academic_year_id: 1, academic_year_name: '2nd Year', lunch_start_time: '12:15', lunch_duration_mins: 60,
    batches: [
      { id: 5, name: 'B1' }, { id: 6, name: 'B2' },
      { id: 7, name: 'B3' }, { id: 8, name: 'B4' },
    ],
  },
  {
    id: 3, name: 'A', academic_year_id: 2, academic_year_name: '3rd Year', lunch_start_time: '12:15', lunch_duration_mins: 60,
    batches: [
      { id: 9, name: 'A1' }, { id: 10, name: 'A2' },
      { id: 11, name: 'A3' }, { id: 12, name: 'A4' },
    ],
  },
  {
    id: 4, name: 'B', academic_year_id: 2, academic_year_name: '3rd Year', lunch_start_time: '12:15', lunch_duration_mins: 60,
    batches: [
      { id: 13, name: 'B1' }, { id: 14, name: 'B2' },
      { id: 15, name: 'B3' }, { id: 16, name: 'B4' },
    ],
  },
  {
    id: 5, name: 'A', academic_year_id: 3, academic_year_name: 'Final Year', lunch_start_time: '12:15', lunch_duration_mins: 60,
    batches: [
      { id: 17, name: 'A1' }, { id: 18, name: 'A2' },
      { id: 19, name: 'A3' }, { id: 20, name: 'A4' },
    ],
  },
]

export default function TeacherWorkload() {
  const [teachers, setTeachers]     = useState([])
  const [subjects, setSubjects]     = useState([])
  const [divisions, setDivisions]   = useState([])
  const [selectedTeacher, setSelectedTeacher] = useState('')
  const [assignments, setAssignments] = useState([])
  const [saving, setSaving]         = useState(false)
  const [useMock, setUseMock]       = useState(false)

  // Load data (fallback to mock if backend unavailable)
  useEffect(() => {
    async function load() {
      try {
        const [t, s, d] = await Promise.all([
          api.getTeachers(),
          api.getSubjects(),
          api.getDivisions(),
        ])
        setTeachers(t)
        setSubjects(s)
        setDivisions(d)
      } catch {
        // Backend not available — use mock data
        setUseMock(true)
        setTeachers(MOCK_TEACHERS)
        setSubjects(MOCK_SUBJECTS)
        setDivisions(MOCK_DIVISIONS)
      }
    }
    load()
  }, [])

  // ── Assignment CRUD ──
  function addAssignment() {
    setAssignments(prev => [
      ...prev,
      { id: nextId++, subjectId: '', type: '', selectedGroups: [] },
    ])
  }

  function updateAssignment(updated) {
    setAssignments(prev => prev.map(a => (a.id === updated.id ? updated : a)))
  }

  function removeAssignment(id) {
    setAssignments(prev => prev.filter(a => a.id !== id))
  }

  // ── Parse into allocation rows ──
  function buildAllocationRows() {
    const rows = []
    for (const a of assignments) {
      if (!a.subjectId || !a.type || a.selectedGroups.length === 0) continue
      for (const groupId of a.selectedGroups) {
        rows.push({
          teacher_id: Number(selectedTeacher),
          subject_id: Number(a.subjectId),
          group_type: a.type === 'theory' ? 'division' : 'batch',
          group_id: groupId,
        })
      }
    }
    return rows
  }

  // ── Save ──
  async function handleSave() {
    const rows = buildAllocationRows()
    if (rows.length === 0) {
      toast.error('No valid assignments to save.')
      return
    }

    setSaving(true)
    try {
      if (useMock) {
        // Simulate save
        await new Promise(r => setTimeout(r, 600))
        console.log('Mock Save — allocation rows:', rows)
      } else {
        await api.saveAllocations({ allocations: rows })
      }
      toast.success(`Saved ${rows.length} allocation(s) successfully!`)
      setAssignments([])
      setSelectedTeacher('')
    } catch (err) {
      toast.error(err.message || 'Failed to save allocations.')
    } finally {
      setSaving(false)
    }
  }

  const allocationRows = buildAllocationRows()

  // Helper: resolve names for preview
  function resolveNames(row) {
    const teacher = teachers.find(t => t.id === row.teacher_id)
    const subject = subjects.find(s => s.id === row.subject_id)
    let groupName = ''
    if (row.group_type === 'division') {
      const div = divisions.find(d => d.id === row.group_id)
      groupName = div ? `Div ${div.name} (${div.academic_year_name})` : `Div #${row.group_id}`
    } else {
      for (const d of divisions) {
        const batch = (d.batches || []).find(b => b.id === row.group_id)
        if (batch) { groupName = `${batch.name} (${d.name} – ${d.academic_year_name})`; break }
      }
      if (!groupName) groupName = `Batch #${row.group_id}`
    }
    return {
      teacher: teacher?.name || '',
      subject: subject?.name || '',
      subjectCode: subject?.code || '',
      group: groupName,
      groupType: row.group_type,
    }
  }

  return (
    <>
      <div className="page-header">
        <h2>Teacher Workload Dashboard</h2>
        <p>Assign subjects and groups to teachers. Each assignment is parsed into individual allocation rows.</p>
      </div>

      {useMock && (
        <div style={{
          padding: '10px 16px',
          background: 'var(--yellow-dim)',
          border: '1px solid var(--yellow)',
          borderRadius: 'var(--radius-sm)',
          marginBottom: 20,
          fontSize: '0.85rem',
          color: 'var(--yellow)',
        }}>
          ⚠ Backend unavailable — running with demo data. Saves are logged to console.
        </div>
      )}

      {/* ── Stats ── */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-label">Teachers</div>
          <div className="stat-value">{teachers.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Subjects</div>
          <div className="stat-value">{subjects.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Divisions</div>
          <div className="stat-value">{divisions.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Allocations</div>
          <div className="stat-value">{allocationRows.length}</div>
        </div>
      </div>

      {/* ── Teacher Select ── */}
      <div className="card">
        <div className="form-group">
          <label>Select Teacher</label>
          <select
            id="teacher-select"
            className="form-select"
            value={selectedTeacher}
            onChange={e => {
              setSelectedTeacher(e.target.value)
              setAssignments([])
            }}
          >
            <option value="">— Choose a teacher —</option>
            {teachers.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>

        {/* ── Assignment Cards ── */}
        {selectedTeacher && (
          <>
            {assignments.length === 0 && (
              <div className="empty-state">
                <p>No subject assignments yet. Click the button below to add one.</p>
              </div>
            )}

            {assignments.map(a => (
              <SubjectAssignment
                key={a.id}
                assignment={a}
                subjects={subjects}
                divisions={divisions}
                onChange={updateAssignment}
                onRemove={() => removeAssignment(a.id)}
              />
            ))}

            <button
              id="add-subject-btn"
              className="btn btn-ghost btn-block"
              style={{ marginTop: 16 }}
              onClick={addAssignment}
            >
              <HiOutlinePlusCircle /> Add Another Subject
            </button>
          </>
        )}
      </div>

      {/* ── Allocation Preview ── */}
      {allocationRows.length > 0 && (
        <div className="allocation-preview" style={{ marginTop: 20 }}>
          <h4>Allocation Preview ({allocationRows.length} rows)</h4>
          {allocationRows.map((row, i) => {
            const n = resolveNames(row)
            return (
              <div className="allocation-row" key={i}>
                <span style={{ fontWeight: 600, color: 'var(--text)' }}>{n.teacher}</span>
                <span>→</span>
                <span>{n.subject}</span>
                <span className="tag" style={{ marginLeft: 4 }}>
                  <span className={`tag tag-${n.groupType === 'division' ? 'theory' : 'practical'}`}>
                    {n.groupType}
                  </span>
                </span>
                <span className={`tag tag-${n.groupType}`}>{n.group}</span>
              </div>
            )
          })}
        </div>
      )}

      {/* ── Save ── */}
      {allocationRows.length > 0 && (
        <button
          id="save-workload-btn"
          className="btn btn-success btn-block"
          style={{ marginTop: 20 }}
          onClick={handleSave}
          disabled={saving}
        >
          <HiOutlineCheckCircle />
          {saving ? 'Saving…' : `Save ${allocationRows.length} Allocation(s)`}
        </button>
      )}
    </>
  )
}
