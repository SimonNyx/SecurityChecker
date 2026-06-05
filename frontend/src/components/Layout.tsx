import { useState, useRef, useEffect } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/assessments/new', label: 'New Assessment' },
  { to: '/methodology', label: 'Methodology' },
]

const adminItems = [
  { to: '/admin/users', label: 'Users' },
  { to: '/admin/ai-config', label: 'AI Config' },
]

export default function Layout() {
  const { logout, currentUser } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive ? 'bg-blue-700 text-white' : 'text-gray-600 hover:bg-gray-100'
    }`

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-4 py-5 border-b border-gray-200">
          <h1 className="text-lg font-bold text-blue-800">SecurityChecker</h1>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, end }) => (
            <NavLink key={to} to={to} end={end} className={linkClass}>
              {label}
            </NavLink>
          ))}
          {currentUser?.role === 'admin' && (
            <>
              <div className="pt-4 pb-1">
                <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">Admin</p>
              </div>
              {adminItems.map(({ to, label }) => (
                <NavLink key={to} to={to} className={linkClass}>
                  {label}
                </NavLink>
              ))}
            </>
          )}
        </nav>

        {/* User menu */}
        <div className="px-4 py-4 border-t border-gray-200" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(o => !o)}
            className="w-full flex items-center justify-between text-sm text-gray-700 hover:text-gray-900 rounded-lg px-2 py-1.5 hover:bg-gray-100"
          >
            <span className="font-medium truncate">{currentUser?.full_name ?? 'Account'}</span>
            <svg className="w-4 h-4 flex-shrink-0 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          {menuOpen && (
            <div className="mt-1 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
              <button
                onClick={() => { setMenuOpen(false); navigate('/profile') }}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Profile
              </button>
              <button
                onClick={() => { setMenuOpen(false); logout() }}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
