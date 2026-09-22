import { useState } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import {
  Settings as SettingsIcon,
  Server,
  Bell,
  Shield,
  Save,
  User,
  Key,
  Palette,
  Globe,
  CheckCircle,
  Plus,
  Trash2,
} from 'lucide-react'
import clsx from 'clsx'

interface ProviderConfig {
  id: string
  name: string
  type: 'ollama' | 'openai' | 'custom'
  endpoint: string
  model: string
  apiKey: string
  active: boolean
}

interface UserProfile {
  id: string
  name: string
  email: string
  role: 'admin' | 'operator' | 'viewer'
}

export default function Settings() {
  const { theme, toggleTheme } = useTheme()
  const [apiUrl, setApiUrl] = useState('http://localhost:8000')
  const [wsUrl, setWsUrl] = useState('ws://localhost:8000/ws')
  const [refreshInterval, setRefreshInterval] = useState('5')
  const [notifications, setNotifications] = useState(true)
  const [saved, setSaved] = useState(false)
  const [activeTab, setActiveTab] = useState<'general' | 'providers' | 'profiles' | 'security'>('general')

  // Providers
  const [providers, setProviders] = useState<ProviderConfig[]>([
    {
      id: '1',
      name: 'Ollama Local',
      type: 'ollama',
      endpoint: 'http://localhost:11434',
      model: 'llama3.2',
      apiKey: '',
      active: true,
    },
  ])
  const [showAddProvider, setShowAddProvider] = useState(false)
  const [newProvider, setNewProvider] = useState<Partial<ProviderConfig>>({
    name: '',
    type: 'ollama',
    endpoint: '',
    model: '',
    apiKey: '',
    active: true,
  })

  // Profiles
  const [profiles] = useState<UserProfile[]>([
    { id: '1', name: 'Admin', email: 'admin@cortexmesh.local', role: 'admin' },
  ])

  const handleSave = () => {
    localStorage.setItem('cortex-mesh-settings', JSON.stringify({
      apiUrl,
      wsUrl,
      refreshInterval,
      notifications,
    }))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const addProvider = () => {
    if (!newProvider.name || !newProvider.endpoint) return
    setProviders([...providers, {
      id: Date.now().toString(),
      name: newProvider.name || '',
      type: newProvider.type || 'ollama',
      endpoint: newProvider.endpoint || '',
      model: newProvider.model || '',
      apiKey: newProvider.apiKey || '',
      active: newProvider.active ?? true,
    }])
    setShowAddProvider(false)
    setNewProvider({ name: '', type: 'ollama', endpoint: '', model: '', apiKey: '', active: true })
  }

  const removeProvider = (id: string) => {
    setProviders(providers.filter(p => p.id !== id))
  }

  const tabs = [
    { id: 'general', label: 'General', icon: SettingsIcon },
    { id: 'providers', label: 'AI Providers', icon: Server },
    { id: 'profiles', label: 'Profiles', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
  ]

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Settings</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Configure your CortexMesh dashboard
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
        {tabs.map(tab => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all flex-1 justify-center',
                activeTab === tab.id
                  ? 'bg-white dark:bg-slate-700 text-mesh-primary shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* General Tab */}
      {activeTab === 'general' && (
        <div className="space-y-4 animate-fade-in">
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Palette className="w-5 h-5 text-mesh-primary" />
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

          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Globe className="w-5 h-5 text-mesh-primary" />
              <h3 className="font-semibold text-slate-900 dark:text-white">Connection</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">API URL</label>
                <input type="text" value={apiUrl} onChange={e => setApiUrl(e.target.value)} className="input-field" placeholder="http://localhost:8000" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">WebSocket URL</label>
                <input type="text" value={wsUrl} onChange={e => setWsUrl(e.target.value)} className="input-field" placeholder="ws://localhost:8000/ws" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Refresh Interval (seconds)</label>
                <input type="number" value={refreshInterval} onChange={e => setRefreshInterval(e.target.value)} className="input-field" min="1" max="60" />
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Bell className="w-5 h-5 text-mesh-primary" />
              <h3 className="font-semibold text-slate-900 dark:text-white">Notifications</h3>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-white">Enable Notifications</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">Show desktop notifications for events</p>
              </div>
              <button
                onClick={() => setNotifications(!notifications)}
                className={clsx('relative w-11 h-6 rounded-full transition-colors', notifications ? 'bg-mesh-primary' : 'bg-slate-300 dark:bg-slate-600')}
              >
                <span className={clsx('absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform', notifications ? 'translate-x-5' : 'translate-x-0')} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Providers Tab */}
      {activeTab === 'providers' && (
        <div className="space-y-4 animate-fade-in">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Server className="w-5 h-5 text-mesh-primary" />
                <h3 className="font-semibold text-slate-900 dark:text-white">AI Providers</h3>
              </div>
              <button
                onClick={() => setShowAddProvider(true)}
                className="btn-primary flex items-center gap-2 text-sm"
              >
                <Plus className="w-4 h-4" /> Add Provider
              </button>
            </div>

            {showAddProvider && (
              <div className="mb-4 p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg space-y-3 animate-fade-in">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Name</label>
                    <input type="text" value={newProvider.name} onChange={e => setNewProvider({ ...newProvider, name: e.target.value })} className="input-field text-sm" placeholder="My Provider" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Type</label>
                    <select value={newProvider.type} onChange={e => setNewProvider({ ...newProvider, type: e.target.value as any })} className="input-field text-sm">
                      <option value="ollama">Ollama</option>
                      <option value="openai">OpenAI</option>
                      <option value="custom">Custom</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Endpoint</label>
                  <input type="text" value={newProvider.endpoint} onChange={e => setNewProvider({ ...newProvider, endpoint: e.target.value })} className="input-field text-sm" placeholder="http://localhost:11434" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Model</label>
                    <input type="text" value={newProvider.model} onChange={e => setNewProvider({ ...newProvider, model: e.target.value })} className="input-field text-sm" placeholder="llama3.2" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">API Key</label>
                    <input type="password" value={newProvider.apiKey} onChange={e => setNewProvider({ ...newProvider, apiKey: e.target.value })} className="input-field text-sm" placeholder="sk-..." />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={addProvider} className="btn-primary text-sm">Save Provider</button>
                  <button onClick={() => setShowAddProvider(false)} className="btn-secondary text-sm">Cancel</button>
                </div>
              </div>
            )}

            <div className="space-y-3">
              {providers.map(provider => (
                <div key={provider.id} className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={clsx(
                      'w-10 h-10 rounded-lg flex items-center justify-center',
                      provider.active ? 'bg-emerald-100 dark:bg-emerald-900/30' : 'bg-slate-200 dark:bg-slate-600'
                    )}>
                      <Server className={clsx('w-5 h-5', provider.active ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-500')} />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">{provider.name}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{provider.type} • {provider.endpoint}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {provider.active && <span className="badge badge-success">Active</span>}
                    <button onClick={() => removeProvider(provider.id)} className="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Profiles Tab */}
      {activeTab === 'profiles' && (
        <div className="space-y-4 animate-fade-in">
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-mesh-primary" />
              <h3 className="font-semibold text-slate-900 dark:text-white">User Profiles</h3>
            </div>
            <div className="space-y-3">
              {profiles.map(profile => (
                <div key={profile.id} className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-mesh-primary/10 flex items-center justify-center">
                      <User className="w-5 h-5 text-mesh-primary" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900 dark:text-white">{profile.name}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{profile.email}</p>
                    </div>
                  </div>
                  <span className={clsx(
                    'badge',
                    profile.role === 'admin' && 'badge-danger',
                    profile.role === 'operator' && 'badge-info',
                    profile.role === 'viewer' && 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400',
                  )}>
                    {profile.role}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="space-y-4 animate-fade-in">
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Key className="w-5 h-5 text-mesh-primary" />
              <h3 className="font-semibold text-slate-900 dark:text-white">API Token</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Current Token</label>
                <input type="password" className="input-field" placeholder="Enter your API token" />
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Token is stored locally and never sent to third parties</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Save Button */}
      <div className="flex justify-end">
        <button onClick={handleSave} className="btn-primary flex items-center gap-2">
          {saved ? <CheckCircle className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          {saved ? 'Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}
