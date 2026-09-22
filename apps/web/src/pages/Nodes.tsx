import { useState } from 'react'
import { useMesh } from '../contexts/MeshContext'
import {
  Server,
  Clock,
  MapPin,
  Search,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import clsx from 'clsx'

type StatusFilter = 'all' | 'online' | 'offline' | 'degraded'

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx(
      'badge',
      status === 'online' && 'badge-success',
      status === 'offline' && 'badge-danger',
      status === 'degraded' && 'badge-warning',
    )}>
      <span className={clsx(
        'w-1.5 h-1.5 rounded-full mr-1',
        status === 'online' && 'bg-emerald-500 animate-pulse',
        status === 'offline' && 'bg-red-500',
        status === 'degraded' && 'bg-amber-500',
      )} />
      {status}
    </span>
  )
}

function UsageBar({ value, label, color }: { value: number; label: string; color: string }) {
  const barColor = value > 90 ? 'bg-red-500' : value > 75 ? 'bg-amber-500' : value > 60 ? color : 'bg-emerald-500'
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-500 dark:text-slate-400">{label}</span>
        <span className="font-medium text-slate-700 dark:text-slate-300">{value}%</span>
      </div>
      <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all duration-700 ease-out', barColor)}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  )
}

interface NodeCardProps {
  node: any
}

function NodeCard({ node }: NodeCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="card-hover p-5 animate-fade-in">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={clsx(
            'w-12 h-12 rounded-xl flex items-center justify-center transition-colors',
            node.status === 'online' ? 'bg-emerald-100 dark:bg-emerald-900/30' :
            node.status === 'degraded' ? 'bg-amber-100 dark:bg-amber-900/30' :
            'bg-red-100 dark:bg-red-900/30'
          )}>
            <Server className={clsx(
              'w-6 h-6',
              node.status === 'online' ? 'text-emerald-600 dark:text-emerald-400' :
              node.status === 'degraded' ? 'text-amber-600 dark:text-amber-400' :
              'text-red-600 dark:text-red-400'
            )} />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white text-lg">{node.hostname}</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {node.ip_address}
            </p>
          </div>
        </div>
        <StatusBadge status={node.status} />
      </div>

      {/* Resource Bars */}
      <div className="space-y-3">
        <UsageBar value={node.cpu_usage} label="CPU" color="bg-mesh-primary" />
        <UsageBar value={node.memory_usage} label="Memory" color="bg-mesh-secondary" />
        <UsageBar value={node.disk_usage} label="Disk" color="bg-mesh-success" />
        {node.gpu_usage !== undefined && (
          <UsageBar value={node.gpu_usage} label="GPU" color="bg-mesh-accent" />
        )}
      </div>

      {/* Expand/Collapse */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-4 w-full flex items-center justify-center gap-2 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
      >
        {expanded ? (
          <>Less details <ChevronUp className="w-4 h-4" /></>
        ) : (
          <>More details <ChevronDown className="w-4 h-4" /></>
        )}
      </button>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700 space-y-3 animate-fade-in">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400">OS</p>
              <p className="text-sm font-medium text-slate-900 dark:text-white">{node.os || 'Unknown'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400">GPU Model</p>
              <p className="text-sm font-medium text-slate-900 dark:text-white">{node.gpu_model || 'None'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400">GPU Memory</p>
              <p className="text-sm font-medium text-slate-900 dark:text-white">{node.gpu_memory ? `${node.gpu_memory} MB` : 'N/A'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400">Uptime</p>
              <p className="text-sm font-medium text-slate-900 dark:text-white">{node.uptime}</p>
            </div>
          </div>

          {node.roles && node.roles.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Roles</p>
              <div className="flex flex-wrap gap-2">
                {(node.roles as string[]).map((role: string) => (
                  <span key={role} className="badge bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                    {role}
                  </span>
                ))}
              </div>
            </div>
          )}

          {node.labels && Object.keys(node.labels).length > 0 && (
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">Labels</p>
              <div className="flex flex-wrap gap-1">
                {Object.entries(node.labels).map(([key, val]) => (
                  <span key={key} className="badge bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                    {key}={String(val)}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 pt-2">
            <Clock className="w-3.5 h-3.5" />
            Last heartbeat: {new Date(node.last_heartbeat).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Nodes() {
  const { nodes } = useMesh()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')

  const filteredNodes = nodes.filter(node => {
    const matchesSearch = node.hostname.toLowerCase().includes(search.toLowerCase()) ||
      node.ip_address.toLowerCase().includes(search.toLowerCase())
    const matchesStatus = statusFilter === 'all' || node.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const onlineCount = nodes.filter(n => n.status === 'online').length
  const degradedCount = nodes.filter(n => n.status === 'degraded').length
  const offlineCount = nodes.filter(n => n.status === 'offline').length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Nodes</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Cluster node status and resource utilization
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4 text-center">
          <div className="flex items-center justify-center gap-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500" />
            <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{onlineCount}</p>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Online</p>
        </div>
        <div className="card p-4 text-center">
          <div className="flex items-center justify-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{degradedCount}</p>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Degraded</p>
        </div>
        <div className="card p-4 text-center">
          <div className="flex items-center justify-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{offlineCount}</p>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Offline</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search nodes by hostname or IP..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-10"
          />
        </div>
        <div className="flex gap-2">
          {(['all', 'online', 'degraded', 'offline'] as StatusFilter[]).map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                statusFilter === status
                  ? 'bg-mesh-primary text-white'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              )}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Node Grid */}
      {filteredNodes.length === 0 ? (
        <div className="card p-12 text-center">
          <Server className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">
            {nodes.length === 0
              ? 'No nodes registered. Waiting for nodes to connect...'
              : 'No nodes match your filters.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredNodes.map(node => (
            <NodeCard key={node.id} node={node} />
          ))}
        </div>
      )}
    </div>
  )
}
