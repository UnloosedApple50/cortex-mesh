import { useState } from 'react'
import { useMesh } from '../contexts/MeshContext'
import {
  ListTodo,
  Clock,
  ArrowUpRight,
  Filter,
  Search,
  Play,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader,
} from 'lucide-react'
import clsx from 'clsx'

type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
type StatusFilter = 'all' | TaskStatus

function TaskStatusBadge({ status }: { status: TaskStatus }) {
  const config = {
    pending: { icon: Clock, classes: 'badge-warning', label: 'Pending' },
    running: { icon: Loader, classes: 'badge-info', label: 'Running' },
    completed: { icon: CheckCircle, classes: 'badge-success', label: 'Completed' },
    failed: { icon: XCircle, classes: 'badge-danger', label: 'Failed' },
    cancelled: { icon: AlertCircle, classes: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400', label: 'Cancelled' },
  }
  const { icon: Icon, classes, label } = config[status]
  return (
    <span className={clsx('badge', classes)}>
      <Icon className="w-3 h-3 mr-1" />
      {label}
    </span>
  )
}

function ProgressBar({ progress, status }: { progress: number; status: TaskStatus }) {
  const color = status === 'completed' ? 'bg-emerald-500' :
    status === 'failed' ? 'bg-red-500' :
    status === 'cancelled' ? 'bg-slate-400' :
    status === 'running' ? 'bg-blue-500' : 'bg-amber-500'
  
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className={clsx(
            'h-full rounded-full transition-all duration-700 ease-out',
            color,
            status === 'running' && 'animate-pulse'
          )}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
      <span className="text-xs font-medium text-slate-600 dark:text-slate-300 w-10 text-right">
        {progress}%
      </span>
    </div>
  )
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    low: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400',
    medium: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    high: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  }
  return (
    <span className={clsx('badge text-[10px] uppercase tracking-wide', colors[priority] || colors.low)}>
      {priority}
    </span>
  )
}

export default function Tasks() {
  const { tasks } = useMesh()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [sortBy, setSortBy] = useState<'created' | 'progress' | 'name'>('created')

  const filteredTasks = tasks
    .filter(task => {
      const matchesSearch = task.name.toLowerCase().includes(search.toLowerCase()) ||
        task.type.toLowerCase().includes(search.toLowerCase())
      const matchesStatus = statusFilter === 'all' || task.status === statusFilter
      return matchesSearch && matchesStatus
    })
    .sort((a, b) => {
      if (sortBy === 'created') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      if (sortBy === 'progress') return b.progress - a.progress
      return a.name.localeCompare(b.name)
    })

  const pendingTasks = tasks.filter(t => t.status === 'pending')
  const runningTasks = tasks.filter(t => t.status === 'running')
  const completedTasks = tasks.filter(t => t.status === 'completed')
  const failedTasks = tasks.filter(t => t.status === 'failed')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Tasks</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Monitor and manage cluster tasks
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <button
          onClick={() => setStatusFilter('pending')}
          className={clsx('card p-4 text-left transition-all hover:scale-[1.02]', statusFilter === 'pending' && 'ring-2 ring-amber-500')}
        >
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-500" />
            <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{pendingTasks.length}</p>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Pending</p>
        </button>
        <button
          onClick={() => setStatusFilter('running')}
          className={clsx('card p-4 text-left transition-all hover:scale-[1.02]', statusFilter === 'running' && 'ring-2 ring-blue-500')}
        >
          <div className="flex items-center gap-2">
            <Play className="w-4 h-4 text-blue-500" />
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{runningTasks.length}</p>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Running</p>
        </button>
        <button
          onClick={() => setStatusFilter('completed')}
          className={clsx('card p-4 text-left transition-all hover:scale-[1.02]', statusFilter === 'completed' && 'ring-2 ring-emerald-500')}
        >
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{completedTasks.length}</p>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Completed</p>
        </button>
        <button
          onClick={() => setStatusFilter('failed')}
          className={clsx('card p-4 text-left transition-all hover:scale-[1.02]', statusFilter === 'failed' && 'ring-2 ring-red-500')}
        >
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-red-500" />
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{failedTasks.length}</p>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Failed</p>
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search tasks..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-10"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as any)}
            className="input-field py-2 text-sm"
          >
            <option value="created">Newest First</option>
            <option value="progress">By Progress</option>
            <option value="name">By Name</option>
          </select>
        </div>
      </div>

      {/* Task List */}
      {filteredTasks.length === 0 ? (
        <div className="card p-12 text-center">
          <ListTodo className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">
            {tasks.length === 0
              ? 'No tasks found. Tasks will appear here when scheduled.'
              : 'No tasks match your filters.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredTasks.map((task, index) => (
            <div
              key={task.id}
              className="card p-4 hover:shadow-md transition-all duration-200 animate-fade-in"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <ArrowUpRight className={clsx(
                    'w-5 h-5',
                    task.status === 'running' ? 'text-blue-500 animate-pulse' :
                    task.status === 'completed' ? 'text-emerald-500' :
                    task.status === 'failed' ? 'text-red-500' : 'text-slate-400'
                  )} />
                  <div>
                    <h4 className="font-medium text-slate-900 dark:text-white">{task.name}</h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-slate-500 dark:text-slate-400">{task.type}</span>
                      <span className="text-slate-300 dark:text-slate-600">•</span>
                      <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">{task.node_id}</span>
                      {task.priority && (
                        <>
                          <span className="text-slate-300 dark:text-slate-600">•</span>
                          <PriorityBadge priority={task.priority} />
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <TaskStatusBadge status={task.status} />
              </div>

              <ProgressBar progress={task.progress} status={task.status} />

              <div className="flex items-center justify-between mt-3 text-xs text-slate-500 dark:text-slate-400">
                <div className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {new Date(task.created_at).toLocaleString()}
                </div>
                {task.duration && <span>Duration: {task.duration}</span>}
                {task.memory_mb && <span>{task.memory_mb} MB</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
