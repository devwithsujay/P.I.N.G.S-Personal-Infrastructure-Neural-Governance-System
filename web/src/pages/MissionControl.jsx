import React, { useState, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { getAgents, getAgentRuns, getLastRunPerAgent, getJournalFeed, getMemory, getProactiveStatus, getSuggestions, dismissSuggestion } from '../api'
import { Button, Spinner } from '@heroui/react'

const EVENT_ICONS = {
  chat: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  task: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
  research: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  error: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
  system: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
}

const EVENT_COLORS = {
  chat: 'text-blue-400',
  task: 'text-green-400',
  research: 'text-purple-400',
  error: 'text-red-400',
  system: 'text-text-muted',
}

const EVENT_BORDER_COLORS = {
  chat: '#3b82f6',
  task: '#22c55e',
  research: '#a855f7',
  error: '#ef4444',
  system: 'var(--text-muted)',
}

const LOG_FILTERS = ['all', 'chat', 'task', 'research', 'error', 'system']

function parseJournalString(text) {
  if (!text || typeof text !== 'string') return []
  const entries = []
  const regex = /\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\w+\]\s+\[(\w+)\]\s+(.*)/g
  let match
  while ((match = regex.exec(text)) !== null) {
    entries.push({ type: match[2].toLowerCase(), content: match[3], timestamp: match[1] })
  }
  return entries
}

function CircularGauge({ value, max = 100, size = 72, label, color }) {
  const radius = (size - 12) / 2
  const circumference = 2 * Math.PI * radius
  const progress = Math.min(value / max, 1)
  const offset = circumference * (1 - progress)
  const displayValue = typeof value === 'number' ? `${Math.round(value)}` : '--'
  const strokeColor = color || 'var(--accent)'

  return (
    <div className="flex flex-col items-center gap-1.5">
      <svg width={size} height={size} className="transform -rotate-90" style={{ filter: `drop-shadow(0 0 6px ${strokeColor}44)` }}>
        {/* Outer track ring */}
        <circle cx={size/2} cy={size/2} r={radius} className="gauge-track" strokeWidth="3" />
        {/* Scale markers ring */}
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="var(--border)" strokeWidth="6" />
        {/* Progress arc */}
        <circle
          cx={size/2} cy={size/2} r={radius}
          className="gauge-fill"
          strokeWidth="3"
          stroke={strokeColor}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="text-center -mt-[calc(50%+12px)] mb-5">
        <span className="text-lg font-bold text-text-primary">{displayValue}</span>
        <span className="text-xs text-text-muted ml-0.5">%</span>
      </div>
      <span className="text-xs text-text-muted uppercase tracking-wider font-medium">{label}</span>
    </div>
  )
}

function LogEntry({ entry }) {
  const type = (entry.type || 'system').toLowerCase()
  const icon = EVENT_ICONS[type] || EVENT_ICONS.system
  const color = EVENT_COLORS[type] || EVENT_COLORS.system
  const borderColor = EVENT_BORDER_COLORS[type] || EVENT_BORDER_COLORS.system

  return (
    <div
      className="flex items-start gap-3 p-3 rounded-xl hover:bg-bg-surface/40 transition-all duration-200 group"
      style={{ borderLeft: `2px solid ${borderColor}` }}
    >
      <div className={`flex-shrink-0 w-8 h-8 rounded-lg bg-bg-surface flex items-center justify-center ${color}`}>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-xs text-text-muted uppercase tracking-wider font-medium">{type}</span>
          <span className="text-xs text-text-muted">
            {new Date(entry.timestamp || entry.created_at).toLocaleTimeString()}
          </span>
        </div>
        <p className="text-xs text-text-secondary leading-relaxed">
          {entry.content || entry.message || entry.text || ''}
        </p>
        {entry.agent && (
          <span className="inline-block mt-1 px-1.5 py-0.5 rounded-md bg-accent/10 text-accent-light text-xs font-medium">
            {entry.agent}
          </span>
        )}
      </div>
    </div>
  )
}

export default function MissionControl() {
  const [agents, setAgents] = useState([])
  const [runs, setRuns] = useState([])
  const [journal, setJournal] = useState([])
  const [memory, setMemory] = useState(null)
  const [status, setStatus] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [memoryQuery, setMemoryQuery] = useState('')
  const [memoryResults, setMemoryResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [logFilter, setLogFilter] = useState('all')

  const loadData = useCallback(async () => {
    try {
      const [a, r, j, m, s, sg] = await Promise.all([
        getAgents().catch(() => []),
        getLastRunPerAgent().catch(() => []),
        getJournalFeed().catch(() => []),
        getMemory().catch(() => null),
        getProactiveStatus().catch(() => null),
        getSuggestions().catch(() => [])
      ])
      setAgents(Array.isArray(a) ? a : a?.agents || [])
      setRuns(Array.isArray(r) ? r : r?.runs || [])
      setJournal(Array.isArray(j) ? j : j?.entries || j?.feed || parseJournalString(j?.journal) || [])
      setMemory(m)
      setStatus(s)
      setSuggestions(Array.isArray(sg) ? sg : sg?.suggestions || [])
    } catch {} finally { setLoading(false) }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  const handleDismissSuggestion = async (id) => {
    try { await dismissSuggestion(id); setSuggestions(prev => prev.filter(s => s.id !== id)) } catch {}
  }

  const handleMemorySearch = async () => {
    if (!memoryQuery.trim()) return
    try {
      const { searchMemory } = await import('../api')
      const res = await searchMemory(memoryQuery.trim())
      setMemoryResults(Array.isArray(res) ? res : res?.results || [])
    } catch {}
  }

  const agentStatusColor = (agent) => {
    const lastRun = runs.find(r => r.agent === agent.id || r.agent === agent.name)
    if (!lastRun) return '#636e72'
    const age = Date.now() - new Date(lastRun.timestamp || lastRun.created_at).getTime()
    if (age < 3600000) return '#00b894'
    if (age < 86400000) return '#fdcb6e'
    return '#e17055'
  }

  const filteredJournal = logFilter === 'all' ? journal : journal.filter(e => (e.type || 'system').toLowerCase() === logFilter)

  const agentCount = agents.length
  const activeCount = runs.filter(r => {
    const age = Date.now() - new Date(r.timestamp || r.created_at).getTime()
    return age < 3600000
  }).length

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 glass-strong border-b" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))' }}>
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <span className="font-brand text-sm font-medium text-text-primary">Mission Control</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <span className="w-6 h-6 border-2 border-accent/50 border-t-accent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="p-4 max-w-7xl mx-auto space-y-4">
            {/* System Metrics Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 animate-fade-in">
              <div className="card-hover p-4 flex flex-col items-center gradient-stripe">
                <CircularGauge value={agents.length > 0 ? (activeCount / agentCount) * 100 : 0} label="Active" color="#00b894" />
              </div>
              <div className="card-hover p-4 flex flex-col items-center gradient-stripe">
                <CircularGauge value={journal.length > 0 ? Math.min(journal.length * 5, 100) : 0} label="Events" color="var(--accent)" />
              </div>
              <div className="card-hover p-4 flex flex-col items-center gradient-stripe">
                <CircularGauge value={memory?.total_entries ? Math.min(memory.total_entries, 100) : 0} label="Memory" color="#fdcb6e" />
              </div>
              <div className="card-hover p-4 flex flex-col items-center gradient-stripe">
                <CircularGauge value={status?.running || status?.enabled ? 100 : 0} label="Proactive" color={status?.running || status?.enabled ? '#00b894' : '#636e72'} />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Agents Column */}
              <div className="space-y-4">
                <h3 className="text-xs text-text-muted uppercase tracking-wider font-medium px-1">Agents</h3>
                {agents.length === 0 ? (
                  <div className="card p-4 text-center text-text-muted text-xs">No agents configured</div>
                ) : (
                  <div className="space-y-2">
                    {agents.map(agent => {
                      const lastRun = runs.find(r => r.agent === agent.id || r.agent === agent.name)
                      const statusColor = agentStatusColor(agent)
                      const isActive = statusColor === '#00b894'
                      return (
                        <div key={agent.id || agent.name} className="card-hover p-4 animate-slide-up">
                          <div className="flex items-center gap-3">
                            <div className="relative">
                              <div className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ background: `linear-gradient(135deg, ${statusColor}, ${statusColor}88)` }}>
                                <span className="text-sm font-brand font-semibold text-white">
                                  {(agent.name || agent.id || 'A')[0].toUpperCase()}
                                </span>
                              </div>
                              <div
                                className={`absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-bg-base ${isActive ? 'animate-pulse' : ''}`}
                                style={{ backgroundColor: statusColor }}
                              />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-text-primary truncate">{agent.name || agent.id}</div>
                              <div className="text-xs text-text-muted">
                                {lastRun ? (() => {
                                  const age = Date.now() - new Date(lastRun.timestamp || lastRun.created_at).getTime()
                                  if (age < 60000) return 'Active now'
                                  if (age < 3600000) return `${Math.floor(age / 60000)}m ago`
                                  if (age < 86400000) return `${Math.floor(age / 3600000)}h ago`
                                  return `${Math.floor(age / 86400000)}d ago`
                                })() : 'No runs yet'}
                              </div>
                            </div>
                          </div>
                          {agent.description && <p className="text-xs text-text-secondary mt-2 line-clamp-2">{agent.description}</p>}
                        </div>
                      )
                    })}
                  </div>
                )}

                {status && (
                  <div className="card p-4 animate-slide-up">
                    <h4 className="text-xs text-text-muted uppercase tracking-wider font-medium mb-3">Proactive Status</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-text-secondary">Enabled</span>
                        <span className={`status-pill ${status.running || status.enabled ? 'status-pill-success' : 'status-pill-error'}`}>{status.running || status.enabled ? 'Yes' : 'No'}</span>
                      </div>
                      {status.last_check && (
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-text-secondary">Last Check</span>
                          <span className="text-text-muted">{new Date(status.last_check).toLocaleTimeString()}</span>
                        </div>
                      )}
                      {status.interval && (
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-text-secondary">Interval</span>
                          <span className="text-text-muted">{status.interval}s</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Journal Column */}
              <div className="space-y-4">
                <div className="flex items-center justify-between px-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs text-text-muted uppercase tracking-wider font-medium">Journal</h3>
                    {logFilter !== 'all' && (
                      <span className="status-pill status-pill-online text-xs">LIVE</span>
                    )}
                  </div>
                  <div className="flex gap-1">
                    {LOG_FILTERS.slice(0, 4).map(f => (
                      <Button
                        key={f}
                        onPress={() => setLogFilter(f)}
                        variant="ghost"
                        size="sm"
                        className={`px-2 py-0.5 rounded-full text-xs font-medium transition-all duration-200 ${
                          logFilter === f ? 'status-pill status-pill-online' : 'text-text-muted hover:text-text-secondary'
                        }`}
                      >
                        {f}
                      </Button>
                    ))}
                  </div>
                </div>

                {filteredJournal.length === 0 ? (
                  <div className="card p-4 text-center text-text-muted text-xs">No journal entries</div>
                ) : (
                  <div className="space-y-1">
                    {filteredJournal.slice(0, 20).map((entry, i) => <LogEntry key={entry.id || i} entry={entry} />)}
                  </div>
                )}

                <h3 className="text-xs text-text-muted uppercase tracking-wider font-medium px-1 pt-2">Agent Runs</h3>
                {runs.length === 0 ? (
                  <div className="card p-4 text-center text-text-muted text-xs">No recent runs</div>
                ) : (
                  <div className="space-y-2">
                    {runs.map((run, i) => (
                      <div key={run.id || i} className="card-hover p-3 flex items-center gap-3 animate-slide-up">
                        <div className="w-8 h-8 rounded-lg bg-accent/15 flex items-center justify-center flex-shrink-0">
                          <span className="text-accent-light text-xs font-brand">{(run.agent || 'A')[0].toUpperCase()}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-medium text-text-primary">{run.agent || 'Agent'}</div>
                          <div className="text-xs text-text-muted truncate">{run.task || run.action || 'Task completed'}</div>
                        </div>
                        <span className={`status-pill ${run.status === 'success' ? 'status-pill-success' : run.status === 'failed' ? 'status-pill-error' : 'status-pill-info'}`}>
                          {run.status || 'done'}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Memory Column */}
              <div className="space-y-4">
                <h3 className="text-xs text-text-muted uppercase tracking-wider font-medium px-1">Memory</h3>
                <div className="card p-4 animate-slide-up">
                  {memory ? (
                    <div className="space-y-3">
                      {memory.total_entries !== undefined && (
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-text-secondary">Entries</span>
                          <span className="text-text-primary font-semibold text-lg">{memory.total_entries}</span>
                        </div>
                      )}
                      {memory.categories && (
                        <div className="space-y-1.5">
                          {Object.entries(memory.categories).map(([cat, count]) => (
                            <div key={cat} className="flex items-center justify-between text-xs">
                              <span className="text-text-secondary capitalize">{cat}</span>
                              <span className="text-text-muted font-mono">{count}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-xs text-text-muted text-center">Memory data unavailable</div>
                  )}
                </div>

                <div className="card p-4 animate-slide-up">
                  <h4 className="text-xs text-text-muted uppercase tracking-wider font-medium mb-3">Search Memory</h4>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={memoryQuery}
                      onChange={e => setMemoryQuery(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handleMemorySearch()}
                      placeholder="Search..."
                      className="input-field flex-1 text-xs"
                    />
                    <Button isIconOnly variant="light" onPress={handleMemorySearch} aria-label="Search memory" className="btn-accent !px-3 !py-2">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </Button>
                  </div>

                  {memoryResults && (
                    <div className="mt-3 space-y-2 max-h-60 overflow-y-auto">
                      {memoryResults.length === 0 ? (
                        <div className="text-xs text-text-muted text-center py-2">No results</div>
                      ) : (
                        memoryResults.map((r, i) => (
                          <div key={i} className="rounded-lg p-2.5 text-xs text-text-secondary" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
                            {typeof r === 'string' ? r : r.content || r.text || JSON.stringify(r)}
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>

                {suggestions.length > 0 && (
                  <div className="animate-slide-up">
                    <h3 className="text-xs text-text-muted uppercase tracking-wider font-medium px-1 mb-2">Suggestions</h3>
                    <div className="space-y-2">
                      {suggestions.map((sug, i) => (
                        <div key={sug.id || i} className="card p-3 flex items-start gap-2">
                          <div className="w-6 h-6 rounded-lg bg-accent/15 flex items-center justify-center flex-shrink-0">
                            <svg className="w-3.5 h-3.5 text-accent-light" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                          </div>
                          <div className="flex-1">
                            <p className="text-xs text-text-secondary">{sug.text || sug.content || sug.message}</p>
                          </div>
                          <Button isIconOnly variant="light" onPress={() => handleDismissSuggestion(sug.id)} aria-label="Dismiss suggestion" className="text-text-muted hover:text-text-secondary transition-colors flex-shrink-0 p-1 rounded-lg hover:bg-bg-surface">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
