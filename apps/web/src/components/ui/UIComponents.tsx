import { Loader2, AlertTriangle, WifiOff } from 'lucide-react'
import clsx from 'clsx'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

export function LoadingSpinner({ size = 'md', label }: LoadingSpinnerProps) {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' }
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-3">
      <Loader2 className={clsx('text-mesh-primary animate-spin', sizes[size])} />
      {label && <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>}
    </div>
  )
}

interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>
  title: string
  description?: string
  action?: React.ReactNode
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="card p-12 text-center">
      {Icon && <Icon className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />}
      <p className="text-slate-500 dark:text-slate-400 font-medium">{title}</p>
      {description && <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
}

export function ErrorState({ title = 'Something went wrong', message, onRetry }: ErrorStateProps) {
  return (
    <div className="card p-8 text-center border-red-200 dark:border-red-800">
      <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-3" />
      <p className="font-medium text-red-600 dark:text-red-400">{title}</p>
      {message && <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{message}</p>}
      {onRetry && (
        <button onClick={onRetry} className="btn-primary mt-4">
          Try Again
        </button>
      )}
    </div>
  )
}

interface OfflineBannerProps {
  message?: string
}

export function OfflineBanner({ message = 'WebSocket disconnected. Attempting to reconnect...' }: OfflineBannerProps) {
  return (
    <div className="card p-4 border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20">
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
        <WifiOff className="w-4 h-4 text-amber-600 dark:text-amber-400" />
        <p className="text-sm text-amber-700 dark:text-amber-400">{message}</p>
      </div>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  trend?: { value: number; label: string }
  delay?: number
}

export function StatCard({ title, value, subtitle, icon: Icon, color, trend, delay = 0 }: StatCardProps) {
  return (
    <div
      className="card p-5 animate-fade-in"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400">{title}</p>
          <p className="text-2xl font-bold mt-1 text-slate-900 dark:text-white">{value}</p>
          {subtitle && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{subtitle}</p>
          )}
          {trend && (
            <div className={clsx(
              'flex items-center gap-1 mt-2 text-xs font-medium',
              trend.value >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
            )}>
              <span>{trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}%</span>
              <span className="text-slate-400">{trend.label}</span>
            </div>
          )}
        </div>
        <div className={`p-2.5 rounded-lg ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
    </div>
  )
}

interface UsageBarProps {
  value: number
  label: string
  showPercentage?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function UsageBar({ value, label, showPercentage = true, size = 'md' }: UsageBarProps) {
  const color = value > 90 ? 'bg-red-500' : value > 75 ? 'bg-amber-500' : value > 60 ? 'bg-blue-500' : 'bg-emerald-500'
  const heights = { sm: 'h-1.5', md: 'h-2', lg: 'h-3' }
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-500 dark:text-slate-400">{label}</span>
        {showPercentage && (
          <span className="font-medium text-slate-700 dark:text-slate-300">{value}%</span>
        )}
      </div>
      <div className={clsx('w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden', heights[size])}>
        <div
          className={clsx('h-full rounded-full transition-all duration-700 ease-out', color)}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  )
}
