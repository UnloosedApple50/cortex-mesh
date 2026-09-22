import { useMesh } from '../contexts/MeshContext'
import {
  Server,
  ListTodo,
  HardDrive,
  Bell,
  Activity,
  Cpu,
  MemoryStick,
} from 'lucide-react'

function StatCard({ title, value, subtitle, icon: Icon, color }: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ComponentType<{ className?: string }>
  color: string
}) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400">{title}</p>
          <p className="text-2xl font-bold mt-1 text-slate-900 dark:text-white">{value}</p>
          {subtitle && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-2.5 rounded-lg ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { stats, nodes, tasks, events, connected } = useMesh()

  const onlineNodes = nodes.filter(n => n.status === 'online').length
  const runningTasks = tasks.filter(t => t.status === 'running').length
  const unreadEvents = events.filter(e => !e.acknowledged).length
  const avgCpu = nodes.length > 0
    ? Math.round(nodes.reduce((sum: number, n) => sum + n.cpu_usage, 0) / nodes.length)
    : 0
  const avgMemory = nodes.length > 0
    ? Math.round(nodes.reduce((sum: number, n) => sum + n.memory_usage, 0) / nodes.length)
    : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Dashboard</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Cluster overview and real-time metrics
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Nodes"
          value={`${onlineNodes}/${nodes.length}`}
          subtitle="Online"
          icon={Server}
          color="bg-mesh-primary"
        />
        <StatCard
          title="Tasks"
          value={runningTasks}
          subtitle="Running"
          icon={ListTodo}
          color="bg-mesh-accent"
        />
        <StatCard
          title="Storage"
          value={`${stats.storage_used_gb || 0} GB`}
          subtitle={`of ${stats.storage_total_gb || 0} GB used`}
          icon={HardDrive}
          color="bg-mesh-secondary"
        />
        <StatCard
          title="Events"
          value={unreadEvents}
          subtitle="Unread"
          icon={Bell}
          color="bg-mesh-warning"
        />
      </div>

      {/* Resource Usage */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-5 h-5 text-mesh-primary" />
            <h3 className="font-semibold text-slate-900 dark:text-white">Average CPU Usage</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500 dark:text-slate-400">CPU</span>
              <span className="font-medium text-slate-900 dark:text-white">{avgCpu}%</span>
            </div>
            <div className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-mesh-primary rounded-full transition-all duration-500"
                style={{ width: `${avgCpu}%` }}
              />
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <MemoryStick className="w-5 h-5 text-mesh-secondary" />
            <h3 className="font-semibold text-slate-900 dark:text-white">Average Memory Usage</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500 dark:text-slate-400">Memory</span>
              <span className="font-medium text-slate-900 dark:text-white">{avgMemory}%</span>
            </div>
            <div className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-mesh-secondary rounded-full transition-all duration-500"
                style={{ width: `${avgMemory}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Events */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-mesh-accent" />
          <h3 className="font-semibold text-slate-900 dark:text-white">Recent Events</h3>
        </div>
        {events.length === 0 ? (
          <p className="text-slate-500 dark:text-slate-400 text-sm py-4 text-center">
            No events yet. Waiting for real-time updates...
          </p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {events.slice(0, 10).map(event => (
              <div
                key={event.id}
                className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50"
              >
                <div className={`w-2 h-2 rounded-full mt-2 ${
                  event.type === 'error' ? 'bg-red-500' :
                  event.type === 'warning' ? 'bg-amber-500' :
                  event.type === 'success' ? 'bg-emerald-500' : 'bg-blue-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                    {event.title}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {event.message}
                  </p>
                </div>
                <span className="text-xs text-slate-400 dark:text-slate-500 whitespace-nowrap">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Connection Status */}
      {!connected && (
        <div className="card p-4 border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            <p className="text-sm text-amber-700 dark:text-amber-400">
              WebSocket disconnected. Attempting to reconnect...
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
