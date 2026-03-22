import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import TeacherWorkload from './pages/TeacherWorkload.jsx'
import TimetableViewer from './pages/TimetableViewer.jsx'
import ManageData from './pages/ManageData.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/workload" replace />} />
        <Route path="/workload" element={<TeacherWorkload />} />
        <Route path="/timetable" element={<TimetableViewer />} />
        <Route path="/manage" element={<ManageData />} />
      </Route>
    </Routes>
  )
}
