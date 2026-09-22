import { useMesh } from '../contexts/MeshContext'
import { ListTodo, Clock, ArrowUpRight } from 'lucide-react'
import clsx from 'clsx'

function TaskStatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx(
      'badge',
      status === 'completed' && 'badge-success',
      status === 'running' && 'badge-info',
      status === 'pending' && 'badge-warning',
      status === 'failed' && 'badge-danger',
    )}>
      {status}
    </span>
  )
}

export default function Tasks() {
  const { tasks } = useMesh()

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
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{pendingTasks.length}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Pending</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{runningTasks.length}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Running</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{completedTasks.length}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Completed</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-2xl font-bold text-red-600 dark:text-red-400">{failedTasks.length}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Failed</p>
        </div>
      </div>

      {tasks.length === 0 ? (
        <div className="card p-12 text-center">
          <ListTodo className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">
            No tasks found. Tasks will appear here when scheduled.
          </p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Task</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Type</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Progress</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Node</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {tasks.map(task => (
                  <tr key={task.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <ArrowUpRight className="w-4 h-4 text-slate-400" />
                        <span className="text-sm font-medium text-slate-900 dark:text-white">{task.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-600 dark:text-slate-300">{task.type}</span>
                    </td>
                    <td className="px-4 py-3">
                      <TaskStatusBadge status={task.status} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={clsx(
                              'h-full rounded-full transition-all',
                              task.status === 'completed' ? 'bg-emerald-500' :
                              task.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'
                            )}
                            style={{ width: `${task.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-500 dark:text-slate-400">{task.progress}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-600 dark:text-slate-300 font-mono">{task.node_id}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                        <Clock className="w-3.5 h-3.5" />
                        {new Date(task.created_at).toLocaleString()}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
