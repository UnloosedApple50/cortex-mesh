import { useMesh } from '../contexts/MeshContext'
import { HardDrive, Folder } from 'lucide-react'
import clsx from 'clsx'

function StorageStatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx(
      'badge',
      status === 'healthy' && 'badge-success',
      status === 'warning' && 'badge-warning',
      status === 'critical' && 'badge-danger',
    )}>
      {status}
    </span>
  )
}

function StorageTypeIcon({ type }: { type: string }) {
  const colors: Record<string, string> = {
    local: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    nfs: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
    s3: 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
    ceph: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-600 dark:text-cyan-400',
  }
  return (
    <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center', colors[type] || 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400')}>
      <HardDrive className="w-5 h-5" />
    </div>
  )
}

export default function Storage() {
  const { storage } = useMesh()

  const totalUsed = storage.reduce((sum: number, s) => sum + s.used_gb, 0)
  const totalCapacity = storage.reduce((sum: number, s) => sum + s.total_gb, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Storage</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Storage volumes and capacity monitoring
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-5">
          <p className="text-sm text-slate-500 dark:text-slate-400">Total Volumes</p>
          <p className="text-2xl font-bold mt-1 text-slate-900 dark:text-white">{storage.length}</p>
        </div>
        <div className="card p-5">
          <p className="text-sm text-slate-500 dark:text-slate-400">Used Capacity</p>
          <p className="text-2xl font-bold mt-1 text-slate-900 dark:text-white">{totalUsed.toFixed(1)} GB</p>
        </div>
        <div className="card p-5">
          <p className="text-sm text-slate-500 dark:text-slate-400">Total Capacity</p>
          <p className="text-2xl font-bold mt-1 text-slate-900 dark:text-white">{totalCapacity.toFixed(1)} GB</p>
        </div>
      </div>

      {storage.length === 0 ? (
        <div className="card p-12 text-center">
          <HardDrive className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">
            No storage volumes configured. Add volumes to monitor capacity.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {storage.map(vol => {
            const usagePercent = vol.total_gb > 0 ? Math.round((vol.used_gb / vol.total_gb) * 100) : 0
            return (
              <div key={vol.id} className="card-hover p-5">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <StorageTypeIcon type={vol.type} />
                    <div>
                      <h3 className="font-semibold text-slate-900 dark:text-white">{vol.name}</h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 uppercase">{vol.type}</p>
                    </div>
                  </div>
                  <StorageStatusBadge status={vol.status} />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                    <Folder className="w-4 h-4 text-slate-400" />
                    <span className="font-mono text-xs">{vol.mount_point}</span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500 dark:text-slate-400">Usage</span>
                      <span className="font-medium text-slate-700 dark:text-slate-300">
                        {vol.used_gb.toFixed(1)} / {vol.total_gb.toFixed(1)} GB ({usagePercent}%)
                      </span>
                    </div>
                    <div className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={clsx(
                          'h-full rounded-full transition-all duration-500',
                          usagePercent > 80 ? 'bg-red-500' :
                          usagePercent > 60 ? 'bg-amber-500' : 'bg-emerald-500'
                        )}
                        style={{ width: `${usagePercent}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
