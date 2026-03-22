import { useState } from 'react'
import { HiXMark } from 'react-icons/hi2'

/**
 * A single Subject Assignment card.
 * Props:
 *   assignment    – { id, subjectId, type, selectedGroups: [] }
 *   subjects      – full subject list from API
 *   divisions     – full division list (with nested batches)
 *   onChange(a)    – update this assignment
 *   onRemove()    – delete this assignment card
 */
export default function SubjectAssignment({ assignment, subjects, divisions, onChange, onRemove }) {
  const { subjectId, type, selectedGroups } = assignment

  // Filter subjects by the current type (or show all if none chosen)
  const filteredSubjects = subjects.filter(s =>
    type ? s.type === type : true
  )

  function setField(key, value) {
    const next = { ...assignment, [key]: value }
    // Clear selections when switching type
    if (key === 'type') next.selectedGroups = []
    if (key === 'subjectId') {
      // Auto-set type from the chosen subject
      const subj = subjects.find(s => s.id === Number(value))
      if (subj) {
        next.type = subj.type
        next.selectedGroups = []
      }
    }
    onChange(next)
  }

  function toggleGroup(groupId) {
    const gs = selectedGroups.includes(groupId)
      ? selectedGroups.filter(g => g !== groupId)
      : [...selectedGroups, groupId]
    onChange({ ...assignment, selectedGroups: gs })
  }

  // Build the group options based on type
  let groupOptions = []
  if (type === 'theory') {
    groupOptions = divisions.map(d => ({
      id: d.id,
      label: `Div ${d.name} (${d.academic_year_name})`,
    }))
  } else if (type === 'practical') {
    divisions.forEach(d => {
      (d.batches || []).forEach(b => {
        groupOptions.push({
          id: b.id,
          label: `${b.name} (${d.name} – ${d.academic_year_name})`,
        })
      })
    })
  }

  return (
    <div className="assignment-card">
      <button className="remove-btn" onClick={onRemove} title="Remove">
        <HiXMark />
      </button>

      {/* Subject select */}
      <div className="form-group">
        <label>Subject</label>
        <select
          className="form-select"
          value={subjectId || ''}
          onChange={e => setField('subjectId', e.target.value)}
        >
          <option value="">— Choose subject —</option>
          {subjects.map(s => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.code}) [{s.type}] — {s.sessions_per_week || 1}s/wk, {s.duration_mins || 60}m
            </option>
          ))}
        </select>
      </div>

      {/* Type toggle */}
      {subjectId && (
        <div className="form-group">
          <label>Type</label>
          <div className="toggle-group">
            <button
              className={`toggle-btn ${type === 'theory' ? 'active' : ''}`}
              onClick={() => setField('type', 'theory')}
            >
              Theory
            </button>
            <button
              className={`toggle-btn ${type === 'practical' ? 'active' : ''}`}
              onClick={() => setField('type', 'practical')}
            >
              Practical
            </button>
          </div>
        </div>
      )}

      {/* Group selection */}
      {type && (
        <div className="form-group">
          <label>{type === 'theory' ? 'Assign to Divisions' : 'Assign to Batches'}</label>
          {groupOptions.length === 0 ? (
            <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>
              No {type === 'theory' ? 'divisions' : 'batches'} available. Add them in Manage Data.
            </p>
          ) : (
            <div className="checkbox-grid">
              {groupOptions.map(g => (
                <label
                  key={g.id}
                  className={`checkbox-item ${selectedGroups.includes(g.id) ? 'checked' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedGroups.includes(g.id)}
                    onChange={() => toggleGroup(g.id)}
                  />
                  {g.label}
                </label>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
