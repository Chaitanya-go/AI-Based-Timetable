// ─── API Service Layer ────────────────────────────────────
// In dev, Vite proxies /api → localhost:8000
// In prod, set VITE_API_URL to your deployed backend URL
const BASE = import.meta.env.VITE_API_URL || '';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// ─── Teachers ──────────────────────────────────────────────
export const getTeachers       = ()    => request('/api/teachers');
export const createTeacher     = (d)   => request('/api/teachers', { method: 'POST', body: JSON.stringify(d) });
export const deleteTeacher     = (id)  => request(`/api/teachers/${id}`, { method: 'DELETE' });

// ─── Subjects ──────────────────────────────────────────────
export const getSubjects       = ()    => request('/api/subjects');
export const createSubject     = (d)   => request('/api/subjects', { method: 'POST', body: JSON.stringify(d) });
export const deleteSubject     = (id)  => request(`/api/subjects/${id}`, { method: 'DELETE' });

// ─── Global Settings ───────────────────────────────────────
export const getGlobalSettings = ()    => request('/api/global-settings');
export const updateGlobalSettings = (d)=> request('/api/global-settings', { method: 'PUT', body: JSON.stringify(d) });

// ─── Academic Structure ────────────────────────────────────
export const getAcademicYears  = ()    => request('/api/academic-years');
export const getDivisions      = ()    => request('/api/divisions');
export const createDivision    = (d)   => request('/api/divisions', { method: 'POST', body: JSON.stringify(d) });
export const getBatches        = ()    => request('/api/batches');
export const createBatch       = (d)   => request('/api/batches', { method: 'POST', body: JSON.stringify(d) });

// ─── Allocations ───────────────────────────────────────────
export const getAllocations     = ()    => request('/api/allocations');
export const saveAllocations   = (d)   => request('/api/allocations', { method: 'POST', body: JSON.stringify(d) });
export const deleteAllocation  = (id)  => request(`/api/allocations/${id}`, { method: 'DELETE' });

// ─── Rooms ─────────────────────────────────────────────────
export const getClassrooms     = ()    => request('/api/classrooms');
export const getLabs           = ()    => request('/api/labs');

// ─── Timetable ─────────────────────────────────────────────
export const generateTimetable = ()    => request('/api/timetable/generate', { method: 'POST' });
export const getSchedule       = ()    => request('/api/timetable');
