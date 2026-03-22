import { NavLink, Outlet } from 'react-router-dom'
import { HiOutlineUserGroup, HiOutlineCalendarDays, HiOutlineCog6Tooth } from 'react-icons/hi2'

const links = [
  { to: '/workload',  label: 'Teacher Workload', icon: <HiOutlineUserGroup /> },
  { to: '/timetable', label: 'Timetable',        icon: <HiOutlineCalendarDays /> },
  { to: '/manage',    label: 'Manage Data',       icon: <HiOutlineCog6Tooth /> },
]

export default function Layout() {
  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>Timetable AI</h1>
          <span>Computer Engineering Dept.</span>
        </div>
        <nav className="sidebar-nav">
          {links.map(l => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              {l.icon}
              {l.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* ── Page ── */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
