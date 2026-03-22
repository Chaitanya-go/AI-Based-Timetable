import { useState, useEffect } from 'react'
import { HiOutlineSparkles, HiOutlineArrowPath } from 'react-icons/hi2'
import toast from 'react-hot-toast'
import * as api from '../services/api.js'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

// ── Mock schedule for demo ──
const MOCK_SCHEDULE = [
  { day: 'Monday',    start_time: '09:00', end_time: '10:00', subject: 'Data Structures', teacher: 'Dr. Sharma',    room: 'CR-1', type: 'theory', group: 'Div A' },
  { day: 'Monday',    start_time: '10:00', end_time: '11:00', subject: 'DBMS',            teacher: 'Prof. Patel',    room: 'CR-2', type: 'theory', group: 'Div A' },
  { day: 'Monday',    start_time: '11:15', end_time: '13:15', subject: 'DS Lab',          teacher: 'Dr. Kulkarni',   room: 'LAB-1', type: 'practical', group: 'A1' },
  { day: 'Monday',    start_time: '11:15', end_time: '13:15', subject: 'DS Lab',          teacher: 'Prof. Deshmukh', room: 'LAB-2', type: 'practical', group: 'A2' },
  { day: 'Tuesday',   start_time: '09:00', end_time: '10:00', subject: 'Operating Systems', teacher: 'Dr. Sharma', room: 'CR-3', type: 'theory', group: 'Div B' },
  { day: 'Tuesday',   start_time: '10:00', end_time: '11:00', subject: 'Machine Learning',  teacher: 'Prof. Patel', room: 'CR-1', type: 'theory', group: 'Div A' },
  { day: 'Wednesday', start_time: '09:00', end_time: '10:00', subject: 'Data Structures',   teacher: 'Dr. Sharma',  room: 'CR-1', type: 'theory', group: 'Div A' },
  { day: 'Wednesday', start_time: '14:00', end_time: '16:00', subject: 'DBMS Lab',          teacher: 'Prof. Patel',  room: 'LAB-1', type: 'practical', group: 'B1' },
]

function parseTime(timeStr) {
  const [h, m] = timeStr.split(':').map(Number);
  return h * 60 + m;
}

export default function TimetableViewer() {
  const [schedule, setSchedule]     = useState([])
  const [filter, setFilter]         = useState('all')   // 'all', division id, or teacher name
  const [viewMode, setViewMode]     = useState('division') // 'division' | 'teacher'
  const [generating, setGenerating] = useState(false)
  const [useMock, setUseMock]       = useState(false)

  const [divisions, setDivisions]   = useState([])
  const [teachers, setTeachers]     = useState([])
  const [settings, setSettings]     = useState({ college_start_time: '09:00', college_end_time: '17:00' })

  useEffect(() => {
    async function load() {
      try {
        const [sched, divs, tchs, gs] = await Promise.all([
          api.getSchedule(),
          api.getDivisions(),
          api.getTeachers(),
          api.getGlobalSettings(),
        ])
        setSchedule(sched)
        setDivisions(divs)
        setTeachers(tchs)
        if (gs) setSettings(gs)
      } catch {
        setUseMock(true)
        setSchedule(MOCK_SCHEDULE)
        setDivisions([
          { id: 1, name: 'A', academic_year_name: '2nd Year' },
          { id: 2, name: 'B', academic_year_name: '2nd Year' },
          { id: 3, name: 'A', academic_year_name: '3rd Year' },
        ])
        setTeachers([
          { id: 1, name: 'Dr. Sharma' },
          { id: 2, name: 'Prof. Patel' },
          { id: 3, name: 'Dr. Kulkarni' },
          { id: 4, name: 'Prof. Deshmukh' },
        ])
      }
    }
    load()
  }, [])

  async function handleGenerate() {
    setGenerating(true)
    try {
      if (useMock) {
        await new Promise(r => setTimeout(r, 1500))
        toast.success('Demo schedule generated!')
      } else {
        const result = await api.generateTimetable()
        setSchedule(result.schedule || [])
        toast.success('Timetable generated successfully!')
      }
    } catch (err) {
      toast.error(err.message || 'Generation failed.')
    } finally {
      setGenerating(false)
    }
  }

  // ── Filter schedule ──
  const filteredSchedule = schedule.filter(entry => {
    if (filter === 'all') return true
    if (viewMode === 'teacher') return entry.teacher === filter
    return entry.group?.includes(filter)
  })

  // ── Timeline Geometry ──
  const startMins = parseTime(settings.college_start_time)
  const endMins = parseTime(settings.college_end_time)
  const totalMins = Math.max(endMins - startMins, 60) // avoid div by 0

  // generate hour ticks
  const ticks = []
  for (let m = startMins; m <= endMins; m += 60) {
    const h = Math.floor(m / 60)
    const lbl = `${h.toString().padStart(2, '0')}:00`
    const pct = ((m - startMins) / totalMins) * 100
    ticks.push({ label: lbl, left: pct })
  }

  // ── Render Day Track ──
  function renderDayTrack(day) {
    let entries = filteredSchedule.filter(e => e.day === day)
    
    // Convert string times to mins
    entries = entries.map(e => ({
      ...e,
      sm: parseTime(e.start_time),
      em: parseTime(e.end_time)
    })).filter(e => e.sm < endMins && e.em > startMins) // strictly within bounds

    // Sort
    entries.sort((a, b) => a.sm - b.sm)

    // Allocate Lanes to avoid overlap visually
    const lanes = []
    entries.forEach(e => {
      let placed = false
      for (let i = 0; i < lanes.length; i++) {
        const last = lanes[i][lanes[i].length - 1]
        // If end time of the last entry in this lane <= start time of current, we can place it here
        if (last.em <= e.sm) {
          lanes[i].push(e)
          e.lane = i
          placed = true
          break
        }
      }
      if (!placed) {
        e.lane = lanes.length
        lanes.push([e])
      }
    })

    const totalLanes = Math.max(lanes.length, 1)

    return (
      <div className="timeline-day-row" key={day}>
        <div className="timeline-day-label">{day}</div>
        <div className="timeline-track">
          {/* Hour grid lines */}
          {ticks.map((t, idx) => (
            <div key={idx} className="timeline-tick" style={{ left: `${t.left}%` }} />
          ))}

          {/* Entries */}
          {entries.map((e, idx) => {
            const leftPct = Math.max(0, ((e.sm - startMins) / totalMins) * 100)
            const widthPct = Math.min(100 - leftPct, ((e.em - e.sm) / totalMins) * 100)
            const topPct = (e.lane / totalLanes) * 100
            const heightPct = 100 / totalLanes

            const isPrac = e.type === 'practical'

            return (
              <div
                key={idx}
                className={`timeline-entry ${isPrac ? 'entry-practical' : 'entry-theory'}`}
                style={{
                  left: `${leftPct}%`,
                  width: `${widthPct}%`,
                  top: `calc(${topPct}% + 4px)`,
                  height: `calc(${heightPct}% - 8px)`
                }}
                title={`${e.subject}\n${e.teacher}\n${e.room} · ${e.group}\n${e.start_time} - ${e.end_time}`}
              >
                <div className="entry-time">{e.start_time}–{e.end_time}</div>
                <div className="subject-name">{e.subject}</div>
                <div className="teacher-name">{e.teacher}</div>
                <div className="room-name">{e.room} · {e.group}</div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="page-header">
        <h2>Generated Timetable</h2>
        <p>View and generate clash-free continuous schedules powered by the CSP engine.</p>
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
          ⚠ Backend unavailable — showing demo schedule data.
        </div>
      )}

      {/* ── Controls ── */}
      <div className="timetable-controls" style={{ display: 'flex', gap: 15, marginBottom: 20, alignItems: 'center' }}>
        <button
          id="generate-btn"
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? (
            <><HiOutlineArrowPath className="spin" /> Generating…</>
          ) : (
            <><HiOutlineSparkles /> Generate Timetable</>
          )}
        </button>

        <div className="toggle-group" style={{ width: 220 }}>
          <button
            className={`toggle-btn ${viewMode === 'division' ? 'active' : ''}`}
            onClick={() => { setViewMode('division'); setFilter('all') }}
          >
            By Division
          </button>
          <button
            className={`toggle-btn ${viewMode === 'teacher' ? 'active' : ''}`}
            onClick={() => { setViewMode('teacher'); setFilter('all') }}
          >
            By Teacher
          </button>
        </div>

        <select
          className="form-select"
          style={{ width: 200 }}
          value={filter}
          onChange={e => setFilter(e.target.value)}
        >
          <option value="all">All</option>
          {viewMode === 'division'
            ? divisions.map(d => (
                <option key={d.id} value={`Div ${d.name}`}>
                  Div {d.name} ({d.academic_year_name})
                </option>
              ))
            : teachers.map(t => (
                <option key={t.id} value={t.name}>{t.name}</option>
              ))
          }
        </select>
      </div>

      {/* ── Gantt/Timeline Viewer ── */}
      <div className="timeline-container">
        <div className="timeline-header">
          {ticks.map((t, idx) => (
            <div key={idx} className="timeline-header-tick" style={{ left: `${t.left}%` }}>
              {t.label}
            </div>
          ))}
        </div>
        
        {DAYS.map(day => renderDayTrack(day))}
      </div>

      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }

        .timeline-container {
          display: flex;
          flex-direction: column;
          gap: 15px;
          overflow-x: auto;
          padding-bottom: 20px;
          min-width: 800px;
        }
        .timeline-header {
          display: flex;
          position: relative;
          height: 30px;
          border-bottom: 2px solid var(--border);
          margin-left: 100px;
        }
        .timeline-header-tick {
          position: absolute;
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--text-dim);
          transform: translateX(-50%);
          bottom: 4px;
        }
        .timeline-day-row {
          display: flex;
          align-items: stretch;
          min-height: 100px;
        }
        .timeline-day-label {
          width: 100px;
          flex-shrink: 0;
          font-weight: 600;
          display: flex;
          align-items: center;
          padding-right: 15px;
          color: var(--text);
        }
        .timeline-track {
          flex: 1;
          position: relative;
          background: rgba(0,0,0,0.02);
          border-radius: 6px;
          border: 1px solid var(--border-light);
          min-height: 100px;
        }
        .timeline-tick {
          position: absolute;
          top: 0;
          bottom: 0;
          border-left: 1px dashed var(--border);
          opacity: 0.3;
        }
        .timeline-entry {
          position: absolute;
          border-radius: 6px;
          padding: 6px 8px;
          font-size: 0.75rem;
          overflow: hidden;
          box-shadow: 0 2px 5px rgba(0,0,0,0.05);
          display: flex;
          flex-direction: column;
          justify-content: center;
          border-left: 4px solid;
          white-space: nowrap;
          text-overflow: ellipsis;
          transition: transform 0.2s, box-shadow 0.2s, z-index 0.2s;
        }
        .timeline-entry:hover {
          transform: scale(1.02);
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
          z-index: 10;
        }
        .entry-theory { 
          background: #f0f9ff; 
          border-left-color: #0284c7; 
          color: #0c4a6e; 
          border-top: 1px solid #e0f2fe;
          border-right: 1px solid #e0f2fe;
          border-bottom: 1px solid #e0f2fe;
        }
        .entry-practical { 
          background: #f0fdf4; 
          border-left-color: #16a34a; 
          color: #14532d; 
          border-top: 1px solid #dcfce7;
          border-right: 1px solid #dcfce7;
          border-bottom: 1px solid #dcfce7;
        }
        .entry-time {
          font-weight: 700;
          font-size: 0.7rem;
          opacity: 0.8;
          margin-bottom: 2px;
        }
        .timeline-entry .subject-name { font-weight: 600; font-size: 0.85rem; }
        .timeline-entry .teacher-name { opacity: 0.9; }
        .timeline-entry .room-name { opacity: 0.8; font-size: 0.7rem; }
      `}</style>
    </>
  )
}
