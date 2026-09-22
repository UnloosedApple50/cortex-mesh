import { useMesh } from '../contexts/MeshContext'
import { Server, Clock } from 'lucide-react'
import clsx from 'clsx'

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx(
      'badge',
      status === 'online' && 'badge-success',
      status === 'offline' && 'badge-danger',
      status === 'degraded' && 'badge-warning',
    )}>
      {status}
    </span>
  )
}

function UsageBar({ value, label }: { value: number; label: string }) {
  const color = value > 80 ? 'bg-red-500' : value > 60 ? 'bg-amber-500' : 'bg-emerald-500'
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-500 dark:text-slate-400">{label}</span>
        <span className="font-medium text-slate-700 dark:text-slate-300">{value}%</span>
      </div>
      <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all duration-500', color)}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}

export default function Nodes() {
  const { nodes } = useMesh()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Nodes</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Cluster node status and resource utilization
        </p>
      </div>

      {nodes.length === 0 ? (
        <div className="card p-12 text-center">
          <Server className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">
            No nodes registered. Waiting for nodes to connect...
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {nodes.map(node => (
            <div key={node.id} className="card-hover p-5">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={clsx(
                    'w-10 h-10 rounded-lg flex items-center justify-center',
                    node.status === 'online' ? 'bg-emerald-100 dark:bg-emerald-900/30' :
                    node.status === 'degraded' ? 'bg-amber-100 dark:bg-amber-900/30' :
                    'bg-red-100 dark:bg-red-900/30'
                  )}>
                    <Server className={clsx(
                      'w-5 h-5',
                      node.status === 'online' ? 'text-emerald-600 dark:text-emerald-400' :
                      node.status === 'degraded' ? 'text-amber-600 dark:text-amber-400' :
                      'text-red-600 dark:text-red-400'
                    )} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">{node.hostname}</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{node.ip_address}</p>
                  </div>
                </div>
                <StatusBadge status={node.status} />
              </div>

              <div className="space-y-3">
                <UsageBar value={node.cpu_usage} label="CPU" />
                <UsageBar value={node.memory_usage} label="Memory" />
                <UsageBar value={node.disk_usage} label="Disk" />
              </div>

              <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
                <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Uptime: {node.uptime}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-1">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Last heartbeat: {new Date(node.last_heartbeat).toLocaleString()}</span>
                </div>
              </div>

              {node.labels && Object.keys(node.labels).length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {Object.entries(node.labels).map(([key, value]) => (
                    <span key={key} className="badge bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                      {key}={value}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
