import { useState } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { Settings as SettingsIcon, Server, Bell, Shield, Save } from 'lucide-react'

export default function Settings() {
  const { theme, toggleTheme } = useTheme()
  const [apiUrl, setApiUrl] = useState('http://localhost:8000')
  const [wsUrl, setWsUrl] = useState('ws://localhost:8000/ws')
  const [refreshInterval, setRefreshInterval] = useState('5')
  const [notifications, setNotifications] = useState(true)
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    localStorage.setItem('hermes-mesh-settings', JSON.stringify({
      apiUrl,
      wsUrl,
      refreshInterval,
      notifications,
    }))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Settings</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Configure your HermesMesh dashboard
        </p>
      </div>

      {/* Appearance */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <SettingsIcon className="w-5 h-5 text-mesh-primary" />
          <h3 className="font-semibold text-slate-900 dark:text-white">Appearance</h3>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-white">Theme</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Switch between light and dark mode</p>
            </div>
            <button
              onClick={toggleTheme}
              className="btn-secondary flex items-center gap-2"
            >
              {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
            </button>
          </div>
        </div>
      </div>

      {/* Connection */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Server className="w-5 h-5 text-mesh-primary" />
          <h3 className="font-semibold text-slate-900 dark:text-white">Connection</h3>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              API URL
            </label>
            <input
              type="text"
              value={apiUrl}
              onChange={e => setApiUrl(e.target.value)}
              className="input-field"
              placeholder="http://localhost:8000"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              WebSocket URL
            </label>
            <input
              type="text"
              value={wsUrl}
              onChange={e => setWsUrl(e.target.value)}
              className="input-field"
              placeholder="ws://localhost:8000/ws"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Refresh Interval (seconds)
            </label>
            <input
              type="number"
              value={refreshInterval}
              onChange={e => setRefreshInterval(e.target.value)}
              className="input-field"
              min="1"
              max="60"
            />
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="w-5 h-5 text-mesh-primary" />
          <h3 className="font-semibold text-slate-900 dark:text-white">Notifications</h3>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-white">Enable Notifications</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Show desktop notifications for events</p>
            </div>
            <button
              onClick={() => setNotifications(!notifications)}
              className={`relative w-11 h-6 rounded-full transition-colors ${
                notifications ? 'bg-mesh-primary' : 'bg-slate-300 dark:bg-slate-600'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                  notifications ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Security */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-mesh-primary" />
          <h3 className="font-semibold text-slate-900 dark:text-white">Security</h3>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              API Token
            </label>
            <input
              type="password"
              className="input-field"
              placeholder="Enter your API token"
            />
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Token is stored locally and never sent to third parties
            </p>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button onClick={handleSave} className="btn-primary flex items-center gap-2">
          <Save className="w-4 h-4" />
          {saved ? 'Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}
