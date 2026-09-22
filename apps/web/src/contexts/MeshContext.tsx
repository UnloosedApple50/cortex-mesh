import { createContext, useContext, useEffect, useState, useCallback, useRef, type ReactNode } from 'react'

export interface Node {
  id: string
  hostname: string
  status: 'online' | 'offline' | 'degraded'
  ip_address: string
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  gpu_usage: number
  gpu_model: string
  gpu_memory: number
  os: string
  roles: string[]
  uptime: string
  last_heartbeat: string
  labels: Record<string, string>
}

export interface Task {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  node_id: string
  created_at: string
  updated_at: string
  progress: number
  type: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  cpu_usage: number
  memory_mb: number
  duration: string
}

export interface StorageInfo {
  id: string
  name: string
  type: 'local' | 'nfs' | 's3' | 'ceph'
  total_gb: number
  used_gb: number
  status: 'healthy' | 'warning' | 'critical'
  mount_point: string
  iops: number
}

export interface Provider {
  id: string
  name: string
  type: string
  status: 'active' | 'inactive' | 'error'
  endpoint: string
  last_check: string
  metadata: Record<string, string>
  model_count: number
  response_time_ms: number
}

export interface EventItem {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  timestamp: string
  source: string
  acknowledged: boolean
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  tokens?: number
}

export interface ClusterStats {
  total_nodes: number
  online_nodes: number
  total_tasks: number
  running_tasks: number
  storage_used_gb: number
  storage_total_gb: number
  active_providers: number
  unread_events: number
  avg_cpu: number
  avg_memory: number
  avg_gpu: number
}

export interface WebSocketMessage {
  type: 'node_update' | 'task_update' | 'event' | 'stats_update' | 'storage_update' | 'provider_update'
  payload: any
  timestamp: string
}

interface MeshContextType {
  connected: boolean
  nodes: Node[]
  tasks: Task[]
  storage: StorageInfo[]
  providers: Provider[]
  events: EventItem[]
  stats: ClusterStats
  chatHistory: ChatMessage[]
  sendMessage: (msg: any) => void
  sendChatMessage: (content: string) => void
}

const defaultStats: ClusterStats = {
  total_nodes: 0,
  online_nodes: 0,
  total_tasks: 0,
  running_tasks: 0,
  storage_used_gb: 0,
  storage_total_gb: 0,
  active_providers: 0,
  unread_events: 0,
  avg_cpu: 0,
  avg_memory: 0,
  avg_gpu: 0,
}

const MeshContext = createContext<MeshContextType>({
  connected: false,
  nodes: [],
  tasks: [],
  storage: [],
  providers: [],
  events: [],
  stats: defaultStats,
  chatHistory: [],
  sendMessage: () => {},
  sendChatMessage: () => {},
})

export function MeshProvider({ children }: { children: ReactNode }) {
  const [connected, setConnected] = useState(false)
  const [nodes, setNodes] = useState<Node[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [storage, setStorage] = useState<StorageInfo[]>([])
  const [providers, setProviders] = useState<Provider[]>([])
  const [events, setEvents] = useState<EventItem[]>([])
  const [stats, setStats] = useState<ClusterStats>(defaultStats)
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const reconnectAttempts = useRef<number>(0)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        reconnectAttempts.current = 0
        fetchInitialData()
      }

      ws.onmessage = (event) => {
        try {
          const msg: WebSocketMessage = JSON.parse(event.data)
          handleMessage(msg)
        } catch (e) {
          console.error('WebSocket message parse error:', e)
        }
      }

      ws.onclose = () => {
        setConnected(false)
        scheduleReconnect()
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch (e) {
      console.error('WebSocket connection error:', e)
      scheduleReconnect()
    }
  }, [])

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) return
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
    reconnectAttempts.current++
    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectTimeoutRef.current = undefined
      connect()
    }, delay)
  }, [connect])

  const handleMessage = useCallback((msg: WebSocketMessage) => {
    switch (msg.type) {
      case 'node_update':
        if (Array.isArray(msg.payload)) {
          setNodes(msg.payload)
        } else {
          setNodes(prev => {
            const idx = prev.findIndex(n => n.id === msg.payload.id)
            if (idx >= 0) {
              const updated = [...prev]
              updated[idx] = { ...updated[idx], ...msg.payload }
              return updated
            }
            return [...prev, msg.payload]
          })
        }
        break
      case 'task_update':
        if (Array.isArray(msg.payload)) {
          setTasks(msg.payload)
        } else {
          setTasks(prev => {
            const idx = prev.findIndex(t => t.id === msg.payload.id)
            if (idx >= 0) {
              const updated = [...prev]
              updated[idx] = { ...updated[idx], ...msg.payload }
              return updated
            }
            return [...prev, msg.payload]
          })
        }
        break
      case 'event':
        setEvents(prev => [msg.payload, ...prev].slice(0, 100))
        break
      case 'stats_update':
        setStats(prev => ({ ...prev, ...msg.payload }))
        break
      case 'storage_update':
        if (Array.isArray(msg.payload)) {
          setStorage(msg.payload)
        }
        break
      case 'provider_update':
        if (Array.isArray(msg.payload)) {
          setProviders(msg.payload)
        }
        break
    }
  }, [])

  const fetchInitialData = async () => {
    try {
      const headers = { 'Content-Type': 'application/json' }
      const urls = [
        '/api/v1/nodes',
        '/api/v1/tasks',
        '/api/v1/storage',
        '/api/v1/providers',
        '/api/v1/events',
        '/api/v1/health',
      ]
      const results = await Promise.allSettled(
        urls.map(url => fetch(url, { headers }))
      )

      if (results[0].status === 'fulfilled' && results[0].value.ok) {
        const data = await results[0].value.json()
        setNodes(Array.isArray(data) ? data : data.nodes || [])
      }
      if (results[1].status === 'fulfilled' && results[1].value.ok) {
        const data = await results[1].value.json()
        setTasks(Array.isArray(data) ? data : data.tasks || [])
      }
      if (results[2].status === 'fulfilled' && results[2].value.ok) {
        const data = await results[2].value.json()
        setStorage(Array.isArray(data) ? data : data.storage || [])
      }
      if (results[3].status === 'fulfilled' && results[3].value.ok) {
        const data = await results[3].value.json()
        setProviders(Array.isArray(data) ? data : data.providers || [])
      }
      if (results[4].status === 'fulfilled' && results[4].value.ok) {
        const data = await results[4].value.json()
        setEvents(Array.isArray(data) ? data : data.events || [])
      }
    } catch (e) {
      console.error('Error fetching initial data:', e)
    }
  }

  const sendMessage = useCallback((msg: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  const sendChatMessage = useCallback(async (content: string) => {
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    setChatHistory(prev => [...prev, userMsg])

    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, history: chatHistory }),
      })
      if (res.ok) {
        const data = await res.json()
        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: data.response || data.message || 'Response received',
          timestamp: new Date().toISOString(),
          tokens: data.tokens,
        }
        setChatHistory(prev => [...prev, assistantMsg])
      } else {
        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          role: 'system',
          content: 'Failed to get response from AI. Please check your provider configuration.',
          timestamp: new Date().toISOString(),
        }
        setChatHistory(prev => [...prev, errorMsg])
      }
    } catch {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: 'Connection error. Is the CortexMesh API running?',
        timestamp: new Date().toISOString(),
      }
      setChatHistory(prev => [...prev, errorMsg])
    }
  }, [chatHistory])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return (
    <MeshContext.Provider value={{ connected, nodes, tasks, storage, providers, events, stats, chatHistory, sendMessage, sendChatMessage }}>
      {children}
    </MeshContext.Provider>
  )
}

export function useMesh() {
  return useContext(MeshContext)
}
