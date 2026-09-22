import { useState, useEffect, useRef } from 'react'
import { useMesh } from '../contexts/MeshContext'
import {
  Server,
  ListTodo,
  HardDrive,
  Bell,
  Activity,
  Cpu,
  MemoryStick,
  Monitor,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { StatCard, OfflineBanner } from '../components/ui/UIComponents'
import clsx from 'clsx'

interface ChartDataPoint {
  time: string
  cpu: number
  memory: number
  gpu: number
}

const COLORS = {
  cpu: '#6366f1',
  memory: '#8b5cf6',
  gpu: '#06b6d4',
  disk: '#10b981',
}

const STATUS_COLORS = ['#10b981', '#f59e0b', '#ef4444', '#6366f1']

export default function Dashboard() {
  const { stats, nodes, tasks, events, connected } = useMesh()
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const onlineNodes = nodes.filter(n => n.status === 'online').length
  const runningTasks = tasks.filter(t => t.status === 'running').length
  const unreadEvents = events.filter(e => !e.acknowledged).length
  const avgCpu = nodes.length > 0
    ? Math.round(nodes.reduce((sum: number, n) => sum + n.cpu_usage, 0) / nodes.length)
    : 0
  const avgMemory = nodes.length > 0
    ? Math.round(nodes.reduce((sum: number, n) => sum + n.memory_usage, 0) / nodes.length)
    : 0
  const avgGpu = nodes.length > 0
    ? Math.round(nodes.reduce((sum: number, n) => sum + (n.gpu_usage || 0), 0) / nodes.length)
    : 0

  // Simulate real-time chart data
  useEffect(() => {
    const updateChart = () => {
      const now = new Date()
      const timeStr = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
      
      setChartData(prev => {
        const newPoint: ChartDataPoint = {
          time: timeStr,
          cpu: avgCpu + Math.round((Math.random() - 0.5) * 10),
          memory: avgMemory + Math.round((Math.random() - 0.5) * 8),
          gpu: avgGpu + Math.round((Math.random() - 0.5) * 12),
        }
        const updated = [...prev, newPoint]
        return updated.slice(-30) // Keep last 30 data points
      })
    }

    // Initialize with some data
    if (chartData.length === 0) {
      const initial: ChartDataPoint[] = []
      for (let i = 30; i >= 0; i--) {
        const t = new Date(Date.now() - i * 2000)
        initial.push({
          time: t.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          cpu: Math.max(0, Math.min(100, avgCpu + Math.round((Math.random() - 0.5) * 20))),
          memory: Math.max(0, Math.min(100, avgMemory + Math.round((Math.random() - 0.5) * 15))),
          gpu: Math.max(0, Math.min(100, avgGpu + Math.round((Math.random() - 0.5) * 25))),
        })
      }
      setChartData(initial)
    }

    intervalRef.current = setInterval(updateChart, 2000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [avgCpu, avgMemory, avgGpu])

  // Node status distribution for pie chart
  const nodeStatusData = [
    { name: 'Online', value: nodes.filter(n => n.status === 'online').length },
    { name: 'Degraded', value: nodes.filter(n => n.status === 'degraded').length },
    { name: 'Offline', value: nodes.filter(n => n.status === 'offline').length },
  ].filter(d => d.value > 0)

  // Task status distribution
  const taskStatusData = [
    { name: 'Running', value: tasks.filter(t => t.status === 'running').length },
    { name: 'Pending', value: tasks.filter(t => t.status === 'pending').length },
    { name: 'Completed', value: tasks.filter(t => t.status === 'completed').length },
    { name: 'Failed', value: tasks.filter(t => t.status === 'failed').length },
  ].filter(d => d.value > 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Dashboard</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Cluster overview and real-time metrics
          </p>
        </div>
        <div className={clsx(
          'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium',
          connected ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
        )}>
          <div className={clsx('w-2 h-2 rounded-full', connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500')} />
          {connected ? 'Live' : 'Disconnected'}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Nodes"
          value={`${onlineNodes}/${nodes.length}`}
          subtitle="Online"
          icon={Server}
          color="bg-mesh-primary"
          delay={0}
        />
        <StatCard
          title="Tasks"
          value={runningTasks}
          subtitle="Running"
          icon={ListTodo}
          color="bg-mesh-accent"
          delay={100}
        />
        <StatCard
          title="Storage"
          value={`${stats.storage_used_gb || 0} GB`}
          subtitle={`of ${stats.storage_total_gb || 0} GB used`}
          icon={HardDrive}
          color="bg-mesh-secondary"
          delay={200}
        />
        <StatCard
          title="Events"
          value={unreadEvents}
          subtitle="Unread"
          icon={Bell}
          color="bg-mesh-warning"
          delay={300}
        />
      </div>

      {/* Real-time Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* CPU/Memory/GPU Over Time */}
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-mesh-primary" />
              <h3 className="font-semibold text-slate-900 dark:text-white">Resource Usage Over Time</h3>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1"><span className="w-3 h-1 bg-mesh-primary rounded-full" /> CPU</span>
              <span className="flex items-center gap-1"><span className="w-3 h-1 bg-mesh-secondary rounded-full" /> Memory</span>
              <span className="flex items-center gap-1"><span className="w-3 h-1 bg-mesh-accent rounded-full" /> GPU</span>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <defs>
                  <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.cpu} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={COLORS.cpu} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.memory} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={COLORS.memory} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gpuGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.gpu} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={COLORS.gpu} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.3} />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#f1f5f9',
                    fontSize: '12px',
                  }}
                />
                <Area type="monotone" dataKey="cpu" stroke={COLORS.cpu} fill="url(#cpuGradient)" strokeWidth={2} />
                <Area type="monotone" dataKey="memory" stroke={COLORS.memory} fill="url(#memoryGradient)" strokeWidth={2} />
                <Area type="monotone" dataKey="gpu" stroke={COLORS.gpu} fill="url(#gpuGradient)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Current Usage Gauges */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-5 h-5 text-mesh-primary" />
            <h3 className="font-semibold text-slate-900 dark:text-white">CPU Usage</h3>
          </div>
          <div className="flex items-center justify-center h-40">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={[{ value: avgCpu }, { value: 100 - avgCpu }]}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  startAngle={90}
                  endAngle={-270}
                  dataKey="value"
                >
                  <Cell fill={COLORS.cpu} />
                  <Cell fill="#e2e8f0" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center -mt-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">{avgCpu}%</span>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <MemoryStick className="w-5 h-5 text-mesh-secondary" />
            <h3 className="font-semibold text-slate-900 dark:text-white">Memory Usage</h3>
          </div>
          <div className="flex items-center justify-center h-40">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={[{ value: avgMemory }, { value: 100 - avgMemory }]}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  startAngle={90}
                  endAngle={-270}
                  dataKey="value"
                >
                  <Cell fill={COLORS.memory} />
                  <Cell fill="#e2e8f0" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center -mt-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">{avgMemory}%</span>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Monitor className="w-5 h-5 text-mesh-accent" />
            <h3 className="font-semibold text-slate-900 dark:text-white">GPU Usage</h3>
          </div>
          <div className="flex items-center justify-center h-40">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={[{ value: avgGpu }, { value: 100 - avgGpu }]}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  startAngle={90}
                  endAngle={-270}
                  dataKey="value"
                >
                  <Cell fill={COLORS.gpu} />
                  <Cell fill="#e2e8f0" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center -mt-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">{avgGpu}%</span>
          </div>
        </div>
      </div>

      {/* Node & Task Status Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card p-5">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Node Status</h3>
          {nodeStatusData.length > 0 ? (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={nodeStatusData}
                    cx="50%"
                    cy="50%"
                    outerRadius={70}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {nodeStatusData.map((_, index) => (
                      <Cell key={index} fill={STATUS_COLORS[index % STATUS_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-8">No nodes registered</p>
          )}
        </div>

        <div className="card p-5">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Task Status</h3>
          {taskStatusData.length > 0 ? (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={taskStatusData}
                    cx="50%"
                    cy="50%"
                    outerRadius={70}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {taskStatusData.map((_, index) => (
                      <Cell key={index} fill={STATUS_COLORS[index % STATUS_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-8">No tasks found</p>
          )}
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
                className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50 animate-fade-in"
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
      {!connected && <OfflineBanner />}
    </div>
  )
}
