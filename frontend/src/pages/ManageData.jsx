import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { HiOutlinePlusSmall, HiOutlineTrash, HiOutlineAcademicCap, HiOutlineBookOpen, HiOutlineUsers, HiOutlineBuildingOffice } from 'react-icons/hi2'
import * as api from '../services/api.js'

// ── Mini CRUD Section Component ──
function DataSection({ title, icon, columns, rows, renderRow, onAdd, addFields }) {
  const [formData, setFormData] = useState({})

  function handleAdd(e) {
    e.preventDefault()
    onAdd(formData)
    setFormData({})
  }

  return (
    <div className="data-section">
      <h3>{icon} {title}</h3>

      {/* Add form */}
      <form className="inline-form" onSubmit={handleAdd} style={{ marginBottom: 14 }}>
        {addFields.map(f => (
          <div className="form-group" key={f.key} style={{ flex: f.flex || 1 }}>
            <label>{f.label}</label>
            {f.type === 'select' ? (
              <select
                className="form-select"
                value={formData[f.key] || ''}
                onChange={e => setFormData(p => ({ ...p, [f.key]: e.target.value }))}
                required
              >
                <option value="">—</option>
                {(f.options || []).map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            ) : (
              <input
                className="form-input"
                type={f.type || 'text'}
                placeholder={f.placeholder || ''}
                value={formData[f.key] || ''}
                onChange={e => setFormData(p => ({ ...p, [f.key]: e.target.value }))}
                required
              />
            )}
          </div>
        ))}
        <button className="btn btn-primary btn-sm" type="submit" style={{ marginBottom: 0, alignSelf: 'end' }}>
          <HiOutlinePlusSmall /> Add
        </button>
      </form>

      {/* Table */}
      {rows.length > 0 ? (
        <table className="data-table">
          <thead>
            <tr>
              {columns.map(c => <th key={c}>{c}</th>)}
              <th style={{ width: 60 }}>Del</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(renderRow)}
          </tbody>
        </table>
      ) : (
        <div className="empty-state"><p>No data yet.</p></div>
      )}
    </div>
  )
}


export default function ManageData() {
  const [teachers, setTeachers]   = useState([])
  const [subjects, setSubjects]   = useState([])
  const [divisions, setDivisions] = useState([])
  const [batches, setBatches]     = useState([])
  const [years, setYears]         = useState([])
  const [globalSettings, setGlobalSettings] = useState({ college_start_time: '09:00', college_end_time: '17:00' })
  const [useMock, setUseMock]     = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const [t, s, d, b, y, gs] = await Promise.all([
          api.getTeachers(),
          api.getSubjects(),
          api.getDivisions(),
          api.getBatches(),
          api.getAcademicYears(),
          api.getGlobalSettings(),
        ])
        setTeachers(t); setSubjects(s); setDivisions(d); setBatches(b); setYears(y); setGlobalSettings(gs);
      } catch {
        setUseMock(true)
        setYears([
          { id: 1, name: '2nd Year' }, { id: 2, name: '3rd Year' }, { id: 3, name: 'Final Year' },
        ])
        setTeachers([
          { id: 1, name: 'Dr. Sharma', email: 'sharma@college.edu' },
          { id: 2, name: 'Prof. Patel', email: 'patel@college.edu' },
        ])
        setSubjects([
          { id: 1, name: 'Data Structures', code: 'DS201', type: 'theory', academic_year_id: 1, sessions_per_week: 3, duration_mins: 60 },
          { id: 2, name: 'DS Lab', code: 'DSL201', type: 'practical', academic_year_id: 1, sessions_per_week: 2, duration_mins: 120 },
        ])
        setDivisions([
          { id: 1, name: 'A', academic_year_id: 1, academic_year_name: '2nd Year', lunch_start_time: "13:00", lunch_duration_mins: 45 },
          { id: 2, name: 'B', academic_year_id: 1, academic_year_name: '2nd Year', lunch_start_time: "13:00", lunch_duration_mins: 45 },
        ])
        setBatches([
          { id: 1, name: 'A1', division_id: 1, division_name: 'A' },
          { id: 2, name: 'A2', division_id: 1, division_name: 'A' },
        ])
      }
    }
    load()
  }, [])

  // ── Handlers (mock-aware) ──
  async function addTeacher(data) {
    try {
      if (useMock) {
        setTeachers(p => [...p, { id: Date.now(), ...data }])
      } else {
        const t = await api.createTeacher(data)
        setTeachers(p => [...p, t])
      }
      toast.success('Teacher added')
    } catch (e) { toast.error(e.message) }
  }

  async function removeTeacher(id) {
    try {
      if (!useMock) await api.deleteTeacher(id)
      setTeachers(p => p.filter(t => t.id !== id))
      toast.success('Teacher removed')
    } catch (e) { toast.error(e.message) }
  }

  async function addSubject(data) {
    try {
      if (useMock) {
        setSubjects(p => [...p, { id: Date.now(), ...data }])
      } else {
        const s = await api.createSubject(data)
        setSubjects(p => [...p, s])
      }
      toast.success('Subject added')
    } catch (e) { toast.error(e.message) }
  }

  async function removeSubject(id) {
    try {
      if (!useMock) await api.deleteSubject(id)
      setSubjects(p => p.filter(s => s.id !== id))
      toast.success('Subject removed')
    } catch (e) { toast.error(e.message) }
  }

  async function addDivision(data) {
    try {
      if (useMock) {
        const yr = years.find(y => y.id === Number(data.academic_year_id))
        setDivisions(p => [...p, { id: Date.now(), ...data, academic_year_name: yr?.name }])
      } else {
        const d = await api.createDivision(data)
        setDivisions(p => [...p, d])
      }
      toast.success('Division added')
    } catch (e) { toast.error(e.message) }
  }

  async function addBatch(data) {
    try {
      if (useMock) {
        const div = divisions.find(d => d.id === Number(data.division_id))
        setBatches(p => [...p, { id: Date.now(), ...data, division_name: div?.name }])
      } else {
        const b = await api.createBatch(data)
        setBatches(p => [...p, b])
      }
      toast.success('Batch added')
    } catch (e) { toast.error(e.message) }
  }

  async function saveSettings(e) {
    e.preventDefault();
    try {
      if (!useMock) {
        const res = await api.updateGlobalSettings(globalSettings);
        setGlobalSettings(res);
      }
      toast.success('Settings saved');
    } catch (e) { toast.error(e.message); }
  }

  return (
    <>
      <div className="page-header">
        <h2>Manage Data</h2>
        <p>Add or remove teachers, subjects, divisions, and batches.</p>
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
          ⚠ Backend unavailable — changes are in-memory only.
        </div>
      )}

      {/* ── Settings ── */}
      <div className="data-section" style={{ marginBottom: 30 }}>
        <h3>College Operating Hours</h3>
        <form className="inline-form" onSubmit={saveSettings}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Start Time</label>
            <input className="form-input" type="time" required
              value={globalSettings.college_start_time}
              onChange={e => setGlobalSettings(p => ({ ...p, college_start_time: e.target.value }))}
            />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>End Time</label>
            <input className="form-input" type="time" required
              value={globalSettings.college_end_time}
              onChange={e => setGlobalSettings(p => ({ ...p, college_end_time: e.target.value }))}
            />
          </div>
          <button className="btn btn-primary btn-sm" type="submit" style={{ alignSelf: 'end' }}>Save Settings</button>
        </form>
      </div>

      {/* ── Teachers ── */}
      <DataSection
        title="Teachers"
        icon={<HiOutlineUsers />}
        columns={['Name', 'Email']}
        rows={teachers}
        addFields={[
          { key: 'name', label: 'Name', placeholder: 'Dr. Smith' },
          { key: 'email', label: 'Email', placeholder: 'smith@college.edu', type: 'email' },
        ]}
        onAdd={addTeacher}
        renderRow={t => (
          <tr key={t.id}>
            <td>{t.name}</td>
            <td>{t.email}</td>
            <td>
              <button className="btn btn-danger btn-sm" onClick={() => removeTeacher(t.id)}>
                <HiOutlineTrash />
              </button>
            </td>
          </tr>
        )}
      />

      {/* ── Subjects ── */}
      <DataSection
        title="Subjects"
        icon={<HiOutlineBookOpen />}
        columns={['Name', 'Code', 'Type', 'Year', 'Sessions/Wk', 'Duration (m)']}
        rows={subjects}
        addFields={[
          { key: 'name', label: 'Name', placeholder: 'Data Structures' },
          { key: 'code', label: 'Code', placeholder: 'DS201' },
          { key: 'type', label: 'Type', type: 'select', options: [
            { value: 'theory', label: 'Theory' },
            { value: 'practical', label: 'Practical' },
          ]},
          { key: 'academic_year_id', label: 'Year', type: 'select',
            options: years.map(y => ({ value: y.id, label: y.name })),
          },
          { key: 'sessions_per_week', label: 'Sessions/Wk', type: 'number', placeholder: '3' },
          { key: 'duration_mins', label: 'Duration (m)', type: 'number', placeholder: '60' },
        ]}
        onAdd={addSubject}
        renderRow={s => (
          <tr key={s.id}>
            <td>{s.name}</td>
            <td><code>{s.code}</code></td>
            <td><span className={`tag tag-${s.type}`}>{s.type}</span></td>
            <td>{years.find(y => y.id === Number(s.academic_year_id))?.name || s.academic_year_id}</td>
            <td>{s.sessions_per_week}</td>
            <td>{s.duration_mins}m</td>
            <td>
              <button className="btn btn-danger btn-sm" onClick={() => removeSubject(s.id)}>
                <HiOutlineTrash />
              </button>
            </td>
          </tr>
        )}
      />

      {/* ── Divisions ── */}
      <DataSection
        title="Divisions"
        icon={<HiOutlineAcademicCap />}
        columns={['Name', 'Academic Year', 'Lunch Time']}
        rows={divisions}
        addFields={[
          { key: 'name', label: 'Division', placeholder: 'A' },
          { key: 'academic_year_id', label: 'Year', type: 'select',
            options: years.map(y => ({ value: y.id, label: y.name })),
          },
          { key: 'lunch_start_time', label: 'Lunch Start', type: 'time', placeholder: '13:00' },
          { key: 'lunch_duration_mins', label: 'Lunch Dur (m)', type: 'number', placeholder: '45' },
        ]}
        onAdd={addDivision}
        renderRow={d => (
          <tr key={d.id}>
            <td>Div {d.name}</td>
            <td>{d.academic_year_name || years.find(y => y.id === Number(d.academic_year_id))?.name}</td>
            <td>{d.lunch_start_time ? `${d.lunch_start_time} (${d.lunch_duration_mins}m)` : '-'}</td>
            <td />
          </tr>
        )}
      />

      {/* ── Batches ── */}
      <DataSection
        title="Batches"
        icon={<HiOutlineBuildingOffice />}
        columns={['Name', 'Division']}
        rows={batches}
        addFields={[
          { key: 'name', label: 'Batch', placeholder: 'A1' },
          { key: 'division_id', label: 'Division', type: 'select',
            options: divisions.map(d => ({
              value: d.id,
              label: `Div ${d.name} (${d.academic_year_name || ''})`,
            })),
          },
        ]}
        onAdd={addBatch}
        renderRow={b => (
          <tr key={b.id}>
            <td>{b.name}</td>
            <td>{b.division_name || divisions.find(d => d.id === Number(b.division_id))?.name}</td>
            <td />
          </tr>
        )}
      />
    </>
  )
}
