import { Outlet } from 'react-router-dom'
import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTheme } from '../../contexts/ThemeContext'
import { useMesh } from '../../contexts/MeshContext'
import {
  LayoutDashboard,
  Server,
  ListTodo,
  HardDrive,
  Cloud,
  Bell,
  Settings,
  Menu,
  X,
  Sun,
  Moon,
  Wifi,
  WifiOff,
  MessageSquare,
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/nodes', label: 'Nodes', icon: Server },
  { path: '/tasks', label: 'Tasks', icon: ListTodo },
  { path: '/storage', label: 'Storage', icon: HardDrive },
  { path: '/providers', label: 'Providers', icon: Cloud },
  { path: '/events', label: 'Events', icon: Bell },
  { path: '/chat', label: 'AI Chat', icon: MessageSquare },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function AppLayout() {
  const { theme, toggleTheme } = useTheme()
  const { connected } = useMesh()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed top-0 left-0 z-50 h-full w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transform transition-transform duration-200 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-mesh-primary to-mesh-secondary flex items-center justify-center">
              <Server className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900 dark:text-white">CortexMesh</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        <nav className="p-3 space-y-1">
          {navItems.map(item => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-mesh-primary/10 text-mesh-primary dark:bg-mesh-primary/20'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white'
                )}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            {connected ? (
              <>
                <Wifi className="w-4 h-4 text-emerald-500" />
                <span>Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-red-500" />
                <span>Disconnected</span>
              </>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-16 bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between h-full px-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              <Menu className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            </button>

            <div className="flex items-center gap-3">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              >
                {theme === 'dark' ? (
                  <Sun className="w-5 h-5 text-amber-400" />
                ) : (
                  <Moon className="w-5 h-5 text-slate-600" />
                )}
              </button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
