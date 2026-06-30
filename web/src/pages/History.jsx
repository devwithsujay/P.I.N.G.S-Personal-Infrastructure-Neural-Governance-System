import React, { useState, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { getSessions, getSessionMessages, clearHistory } from '../api'
import { useToast } from '../components/Toast'
import ConfirmDialog from '../components/ConfirmDialog'
import EmptyState from '../components/EmptyState'

export default function History() {
  const [sessions, setSessions] = useState([])
  const [expandedId, setExpandedId] = useState(null)
  const [messages, setMessages] = useState({})
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const toast = useToast()

  const loadSessions = useCallback(async () => {
    try {
      const res = await getSessions()
      const list = Array.isArray(res) ? res : res?.sessions || []
      setSessions(list.filter(s => s.session_id && s.session_id.trim()))
    } catch {}
  }, [])

  useEffect(() => { loadSessions() }, [loadSessions])

  const toggleSession = async (id) => {
    if (expandedId === id) {
      setExpandedId(null)
      return
    }
    setExpandedId(id)
    if (!messages[id]) {
      try {
        const res = await getSessionMessages(id)
        const msgs = Array.isArray(res) ? res : res?.messages || []
        setMessages(prev => ({ ...prev, [id]: msgs }))
      } catch {}
    }
  }

  const handleDeleteAll = async () => {
    try {
      await clearHistory()
      setSessions([])
      setMessages({})
      setShowClearConfirm(false)
      toast.success('History cleared')
    } catch { toast.error('Failed to clear history') }
  }

  const filteredSessions = sessions.filter(s => {
    if (!filter) return true
    const term = filter.toLowerCase()
    return (s.title || s.session_id || '').toLowerCase().includes(term)
  })

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    try {
      const d = new Date(dateStr)
      const now = new Date()
      const diffMs = now - d
      const diffDays = Math.floor(diffMs / 86400000)
      if (diffDays === 0) return 'Today'
      if (diffDays === 1) return 'Yesterday'
      if (diffDays < 7) return `${diffDays} days ago`
      return d.toLocaleDateString()
    } catch {
      return dateStr
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 glass-strong border-b flex items-center justify-between" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-brand text-sm font-medium text-text-primary">History</span>
          <span className="text-xs text-text-muted">({sessions.length})</span>
        </div>
        {sessions.length > 0 && (
          <button
            onClick={() => setShowClearConfirm(true)}
            className="px-3 py-1.5 rounded-lg text-xs text-red-400 hover:bg-red-500/10 transition-colors"
          >
            Clear All
          </button>
        )}
      </div>

      <div className="px-4 py-3">
        <input
          type="text"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Filter sessions..."
          className="w-full input-field px-4 py-2.5 text-sm text-text-primary placeholder-text-muted"
        />
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4">
        {filteredSessions.length === 0 ? (
          <div className="text-center py-16 text-text-muted text-sm">
            {sessions.length === 0 ? 'No session history' : 'No matching sessions'}
          </div>
        ) : (
          <div className="space-y-2 max-w-3xl mx-auto">
            {filteredSessions.map(session => (
              <div key={session.session_id} className="card rounded-lg overflow-hidden slide-up">
                <button
                  onClick={() => toggleSession(session.session_id)}
                  aria-label={`Toggle session ${session.title || session.session_id}`}
                  className="w-full flex items-center justify-between p-4 text-left hover:bg-bg-surface/30 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-text-primary truncate">
                      {session.title || session.session_id}
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-text-muted">
                      <span>{formatDate(session.created_at || session.timestamp)}</span>
                      <span>{session.message_count || '?'} messages</span>
                    </div>
                  </div>
                  <svg className={`w-4 h-4 text-text-muted transition-transform flex-shrink-0 ml-2 ${expandedId === session.session_id ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {expandedId === session.session_id && (
                  <div className="border-t p-4 max-h-96 overflow-y-auto fade-in" style={{ borderColor: 'var(--border-subtle)' }}>
                    {messages[session.session_id] ? (
                      <div className="space-y-3">
                        {messages[session.session_id].map((msg, i) => (
                          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`chat-bubble text-xs ${msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-agent'}`}>
                              <div className="text-xs text-text-muted mb-1 uppercase">{msg.role}</div>
                              <div className="text-sm">
                                <ReactMarkdown>{msg.content || msg.message || ''}</ReactMarkdown>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex justify-center py-4">
                        <span className="w-4 h-4 border-2 border-accent/50 border-t-accent rounded-full animate-spin" />
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <ConfirmDialog
        open={showClearConfirm}
        title="Clear All History"
        message="This will permanently delete all chat sessions and messages. This cannot be undone."
        confirmLabel="Clear All"
        danger
        onConfirm={handleDeleteAll}
        onCancel={() => setShowClearConfirm(false)}
      />
    </div>
  )
}
