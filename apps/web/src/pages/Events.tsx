import { useState } from 'react'
import { useMesh } from '../contexts/MeshContext'
import { Bell, CheckCircle, AlertTriangle, XCircle, Info, Filter } from 'lucide-react'
import clsx from 'clsx'

type FilterType = 'all' | 'info' | 'warning' | 'error' | 'success'

function EventIcon({ type }: { type: string }) {
  switch (type) {
    case 'success':
      return <CheckCircle className="w-5 h-5 text-emerald-500" />
    case 'warning':
      return <AlertTriangle className="w-5 h-5 text-amber-500" />
    case 'error':
      return <XCircle className="w-5 h-5 text-red-500" />
    default:
      return <Info className="w-5 h-5 text-blue-500" />
  }
}

export default function Events() {
  const { events } = useMesh()
  const [filter, setFilter] = useState<FilterType>('all')

  const filteredEvents = filter === 'all'
    ? events
    : events.filter(e => e.type === filter)

  const errorCount = events.filter(e => e.type === 'error').length
  const warningCount = events.filter(e => e.type === 'warning').length
  const successCount = events.filter(e => e.type === 'success').length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Events</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          System events, alerts, and notifications
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <button
          onClick={() => setFilter('all')}
          className={clsx('card p-4 text-left transition-all', filter === 'all' && 'ring-2 ring-mesh-primary')}
        >
          <p className="text-2xl font-bold text-slate-900 dark:text-white">{events.length}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">All Events</p>
        </button>
        <button
          onClick={() => setFilter('error')}
          className={clsx('card p-4 text-left transition-all', filter === 'error' && 'ring-2 ring-red-500')}
        >
          <p className="text-2xl font-bold text-red-600 dark:text-red-400">{errorCount}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Errors</p>
        </button>
        <button
          onClick={() => setFilter('warning')}
          className={clsx('card p-4 text-left transition-all', filter === 'warning' && 'ring-2 ring-amber-500')}
        >
          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">{warningCount}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Warnings</p>
        </button>
        <button
          onClick={() => setFilter('success')}
          className={clsx('card p-4 text-left transition-all', filter === 'success' && 'ring-2 ring-emerald-500')}
        >
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{successCount}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Success</p>
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-slate-400" />
        <span className="text-sm text-slate-500 dark:text-slate-400">Filter:</span>
        {(['all', 'info', 'warning', 'error', 'success'] as FilterType[]).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={clsx(
              'px-3 py-1 rounded-full text-xs font-medium transition-colors',
              filter === f
                ? 'bg-mesh-primary text-white'
                : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
            )}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {filteredEvents.length === 0 ? (
        <div className="card p-12 text-center">
          <Bell className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">
            No events to display. Events will appear here in real-time.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredEvents.map(event => (
            <div
              key={event.id}
              className={clsx(
                'card p-4 flex items-start gap-3 transition-all',
                !event.acknowledged && 'border-l-4',
                !event.acknowledged && event.type === 'error' && 'border-l-red-500',
                !event.acknowledged && event.type === 'warning' && 'border-l-amber-500',
                !event.acknowledged && event.type === 'info' && 'border-l-blue-500',
                !event.acknowledged && event.type === 'success' && 'border-l-emerald-500',
              )}
            >
              <EventIcon type={event.type} />
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-sm font-medium text-slate-900 dark:text-white">{event.title}</h4>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{event.message}</p>
                  </div>
                  <span className="text-xs text-slate-400 dark:text-slate-500 whitespace-nowrap">
                    {new Date(event.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <span className="badge bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                    {event.source}
                  </span>
                  {event.acknowledged && (
                    <span className="badge badge-success">Acknowledged</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
