import { useMesh } from '../contexts/MeshContext'
import { Cloud, Globe, Clock } from 'lucide-react'
import clsx from 'clsx'

function ProviderStatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx(
      'badge',
      status === 'active' && 'badge-success',
      status === 'inactive' && 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400',
      status === 'error' && 'badge-danger',
    )}>
      {status}
    </span>
  )
}

export default function Providers() {
  const { providers } = useMesh()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Providers</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          External service providers and integrations
        </p>
      </div>

      {providers.length === 0 ? (
        <div className="card p-12 text-center">
          <Cloud className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">
            No providers configured. Add providers to manage integrations.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {providers.map(provider => (
            <div key={provider.id} className="card-hover p-5">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={clsx(
                    'w-10 h-10 rounded-lg flex items-center justify-center',
                    provider.status === 'active' ? 'bg-emerald-100 dark:bg-emerald-900/30' :
                    provider.status === 'error' ? 'bg-red-100 dark:bg-red-900/30' :
                    'bg-slate-100 dark:bg-slate-700'
                  )}>
                    <Cloud className={clsx(
                      'w-5 h-5',
                      provider.status === 'active' ? 'text-emerald-600 dark:text-emerald-400' :
                      provider.status === 'error' ? 'text-red-600 dark:text-red-400' :
                      'text-slate-500 dark:text-slate-400'
                    )} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">{provider.name}</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{provider.type}</p>
                  </div>
                </div>
                <ProviderStatusBadge status={provider.status} />
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                  <Globe className="w-4 h-4 text-slate-400" />
                  <span className="font-mono text-xs truncate">{provider.endpoint}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <Clock className="w-3.5 h-3.5" />
                  Last check: {new Date(provider.last_check).toLocaleString()}
                </div>
              </div>

              {provider.metadata && Object.keys(provider.metadata).length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700">
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(provider.metadata).map(([key, value]) => (
                      <span key={key} className="badge bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                        {key}: {value}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
