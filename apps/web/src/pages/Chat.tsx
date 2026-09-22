import { useState, useRef, useEffect } from 'react'
import { useMesh } from '../contexts/MeshContext'
import {
  Send,
  Bot,
  User,
  Sparkles,
  Loader2,
  Trash2,
} from 'lucide-react'
import clsx from 'clsx'

export default function Chat() {
  const { chatHistory, sendChatMessage, connected } = useMesh()
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory, isTyping])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    
    const message = input.trim()
    setInput('')
    setIsTyping(true)
    await sendChatMessage(message)
    setIsTyping(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  const clearChat = () => {
    // Note: This would need to be supported in context
    setInput('')
  }

  const suggestedPrompts = [
    'What nodes are currently online?',
    'Show me the cluster health status',
    'Which tasks are running right now?',
    'Explain the current resource usage',
  ]

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">AI Assistant</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Chat with your cluster AI for insights and management
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className={clsx(
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium',
            connected ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
          )}>
            <div className={clsx('w-2 h-2 rounded-full', connected ? 'bg-emerald-500' : 'bg-red-500')} />
            {connected ? 'Connected' : 'Offline'}
          </div>
          <button
            onClick={clearChat}
            className="btn-secondary p-2"
            title="Clear chat"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 space-y-4">
        {chatHistory.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-mesh-primary to-mesh-secondary flex items-center justify-center mb-4">
              <Bot className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Welcome to CortexMesh AI
            </h3>
            <p className="text-slate-500 dark:text-slate-400 text-sm max-w-md mb-6">
              Ask questions about your cluster, get insights on resource usage, or request actions.
              Your AI assistant is here to help.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => setInput(prompt)}
                  className="text-left px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-700 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                >
                  <Sparkles className="w-3 h-3 inline mr-2 text-mesh-primary" />
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {chatHistory.map((msg) => (
              <div
                key={msg.id}
                className={clsx(
                  'flex items-start gap-3 animate-fade-in',
                  msg.role === 'user' ? 'flex-row-reverse' : ''
                )}
              >
                <div className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                  msg.role === 'user' ? 'bg-mesh-primary' :
                  msg.role === 'assistant' ? 'bg-gradient-to-br from-mesh-secondary to-mesh-accent' :
                  'bg-slate-300 dark:bg-slate-600'
                )}>
                  {msg.role === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : msg.role === 'assistant' ? (
                    <Bot className="w-4 h-4 text-white" />
                  ) : (
                    <Sparkles className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                  )}
                </div>
                <div className={clsx(
                  'max-w-[75%] rounded-xl px-4 py-3',
                  msg.role === 'user'
                    ? 'bg-mesh-primary text-white'
                    : msg.role === 'system'
                    ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white'
                )}>
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  <div className={clsx(
                    'flex items-center gap-2 mt-2 text-[10px]',
                    msg.role === 'user' ? 'text-white/70' : 'text-slate-400'
                  )}>
                    {new Date(msg.timestamp).toLocaleTimeString()}
                    {msg.tokens && <span>• {msg.tokens} tokens</span>}
                  </div>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex items-start gap-3 animate-fade-in">
                <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-mesh-secondary to-mesh-accent">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-slate-100 dark:bg-slate-700 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-mesh-primary" />
                    <span className="text-sm text-slate-500 dark:text-slate-400">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="mt-4 flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your cluster..."
            rows={1}
            className="input-field resize-none pr-12 min-h-[48px] max-h-32"
            style={{ height: 'auto', overflow: 'hidden' }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement
              target.style.height = 'auto'
              target.style.height = Math.min(target.scrollHeight, 128) + 'px'
            }}
          />
        </div>
        <button
          type="submit"
          disabled={!input.trim() || isTyping}
          className="btn-primary h-12 w-12 flex items-center justify-center rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isTyping ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </form>
    </div>
  )
}
