import React, { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { Button } from '@heroui/react'
import { useChat } from '../context/ChatContext'
import EmptyState from '../components/EmptyState'

const AGENT_COLORS = {
  default: 'var(--accent)',
  pings: '#6c5ce7',
  researcher: '#00cec9',
  coder: '#fdcb6e',
  planner: '#e17055',
  creative: '#fd79a8',
  'homelab-monitor': '#00b894',
}

const AGENT_AVATARS = {
  pings: 'P',
  researcher: 'R',
  coder: 'C',
  planner: 'PL',
  creative: 'CR',
  'homelab-monitor': 'H',
}

function CodeBlock({ language, children }) {
  const [copied, setCopied] = useState(false)
  const codeRef = useRef(null)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(children)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {}
  }

  return (
    <div className="code-block-wrapper group">
      <div className="code-block-header">
        <span className="code-block-lang">{language || 'code'}</span>
        <Button
          size="sm"
          variant="ghost"
          onPress={handleCopy}
          className="code-block-copy"
          aria-label={copied ? 'Copied' : 'Copy code'}
        >
          {copied ? (
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Copied
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy
            </span>
          )}
        </Button>
      </div>
      <pre className="p-3 overflow-x-auto text-xs m-0 bg-transparent border-0">
        <code ref={codeRef} className="font-mono text-text-secondary">{children}</code>
      </pre>
    </div>
  )
}

function MessageActions({ content }) {
  const [show, setShow] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {}
  }

  return (
    <div
      className="relative"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {show && (
        <div className="absolute -top-8 right-0 flex items-center gap-1 glass-modal rounded-lg px-1 py-0.5 fade-in z-10">
          <Button
            isIconOnly
            size="sm"
            variant="ghost"
            onPress={handleCopy}
            aria-label="Copy text"
            className="min-w-0 h-auto p-1.5 text-text-muted hover:text-text-secondary"
          >
            {copied ? (
              <svg className="w-3.5 h-3.5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            )}
          </Button>
        </div>
      )}
    </div>
  )
}

function AgentCard({ agent, color, onClick }) {
  const name = agent.name || agent.id
  const initial = (AGENT_AVATARS[name] || name.charAt(0)).slice(0, 2).toUpperCase()

  return (
    <Button
      fullWidth
      variant="ghost"
      onPress={onClick}
      className="flex items-center gap-3 px-4 py-3 rounded-xl text-left group h-auto"
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold text-white flex-shrink-0 transition-transform group-hover:scale-105"
        style={{ background: `linear-gradient(135deg, ${color}, color-mix(in srgb, ${color} 60%, black))` }}
      >
        {initial}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-text-primary">{name}</span>
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
        </div>
        {agent.description && (
          <div className="text-xs text-text-muted truncate mt-0.5">{agent.description}</div>
        )}
      </div>
      <svg className="w-4 h-4 text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>
    </Button>
  )
}

export default function Chat() {
  const {
    messages,
    isResponding,
    agents,
    models,
    selectedModel,
    setSelectedModel,
    sendMessage,
    clearMessages,
  } = useChat()

  const [input, setInput] = useState('')
  const [showAgents, setShowAgents] = useState(false)
  const [agentFilter, setAgentFilter] = useState('')
  const [filePreview, setFilePreview] = useState(null)
  const [modelOpen, setModelOpen] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)
  const modelDropdownRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isResponding])

  useEffect(() => {
    const handleClick = (e) => {
      if (modelDropdownRef.current && !modelDropdownRef.current.contains(e.target)) {
        setModelOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const autoGrow = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 150) + 'px'
  }, [])

  useEffect(() => { autoGrow() }, [input, autoGrow])

  const handleSend = useCallback(() => {
    const text = input.trim()
    if (!text || isResponding) return

    sendMessage(text, filePreview)
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setShowAgents(false)
    setFilePreview(null)
  }, [input, isResponding, filePreview, sendMessage])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e) => {
    const val = e.target.value
    setInput(val)
    if (val.startsWith('@')) {
      setAgentFilter(val.slice(1))
      setShowAgents(true)
    } else {
      setShowAgents(false)
    }
  }

  const selectAgent = (agent) => {
    setInput(`@${agent.name || agent.id} `)
    setShowAgents(false)
    inputRef.current?.focus()
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) setFilePreview({ name: file.name, size: file.size, type: file.type })
  }

  const filteredAgents = agents.filter(a =>
    !agentFilter || (a.name || a.id || '').toLowerCase().includes(agentFilter.toLowerCase())
  )

  const currentModelObj = models.find(m => m.id === selectedModel)
  const shortModelName = currentModelObj?.name?.replace(' Free', '').replace('opencode/', '') || 'Model'

  const getAgentColor = (agent) => {
    const name = (agent || '').toLowerCase()
    for (const [key, color] of Object.entries(AGENT_COLORS)) {
      if (name.includes(key)) return color
    }
    return AGENT_COLORS.default
  }

  return (
    <div className="flex flex-col h-full pb-16 md:pb-0">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 glass-strong border-b" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 flex-shrink-0">
            <svg viewBox="0 0 32 32" fill="none" className="w-8 h-8">
              <circle cx="16" cy="16" r="3" fill="var(--accent)" />
              <circle cx="16" cy="16" r="7" stroke="var(--accent)" strokeWidth="1.5" opacity="0.7" />
              <circle cx="16" cy="16" r="11" stroke="var(--accent)" strokeWidth="1" opacity="0.4" />
              <circle cx="16" cy="9" r="1.5" fill="var(--accent-light)" opacity="0.9" />
              <circle cx="22" cy="13" r="1" fill="var(--accent-light)" opacity="0.6" />
            </svg>
          </div>
          <div>
            <div className="text-base font-medium text-text-primary leading-tight">Chat</div>
            <div className="text-xs text-text-muted leading-tight">P.I.N.G.S, via {shortModelName}</div>
          </div>
          <div className="relative flex h-2 w-2 ml-1">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ background: 'var(--accent)' }} />
            <span className="relative inline-flex rounded-full h-2 w-2" style={{ background: 'var(--accent)' }} />
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            isIconOnly
            variant="ghost"
            aria-label="New chat"
            onPress={clearMessages}
            className="text-text-muted hover:text-text-secondary"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </Button>
          <Button
            isIconOnly
            variant="ghost"
            aria-label="Export chat"
            onPress={() => exportChat(messages)}
            className="text-text-muted hover:text-text-secondary"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </Button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <EmptyState
            icon="chat"
            suggestions={[
              { label: 'Explain quantum computing', onClick: () => { setInput('Explain quantum computing in simple terms'); inputRef.current?.focus() } },
              { label: 'Write a Python script', onClick: () => { setInput('Write a Python script to scrape a website'); inputRef.current?.focus() } },
              { label: 'Compare React vs Vue', onClick: () => { setInput('@researcher Compare React vs Vue for a new project'); inputRef.current?.focus() } },
            ]}
          />
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} slide-up`}>
            <div className={`relative max-w-[85%] ${msg.role === 'user'
              ? 'rounded-2xl rounded-br-md px-4 py-3'
              : 'rounded-2xl rounded-bl-md px-4 py-3'
            }`}
            style={msg.role === 'user' ? {
              background: 'var(--bubble-user)',
              borderRight: '2px solid var(--accent)',
            } : {
              background: msg.isError ? 'rgba(var(--status-error-rgb, 239,68,68), 0.1)' : 'var(--bubble-agent)',
              borderLeft: `2px solid ${msg.isError ? 'var(--status-error, #ef4444)' : 'var(--accent)'}`,
            }}>
              {msg.role === 'agent' && (
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                    style={{ background: `linear-gradient(135deg, ${getAgentColor(msg.agent)}, color-mix(in srgb, ${getAgentColor(msg.agent)} 60%, black))` }}
                  >
                    {(AGENT_AVATARS[msg.agent] || (msg.agent || 'A').charAt(0)).slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <span className="text-xs text-text-primary uppercase tracking-wider font-medium">{msg.agent || 'agent'}</span>
                    {msg.model_used && (
                      <div className="text-xs text-accent/60 font-mono">{msg.model_used.split('/').pop()}</div>
                    )}
                  </div>
                </div>
              )}
              <div className="text-base leading-relaxed">
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '')
                      const lang = match?.[1]
                      return inline ? (
                        <code className="bg-bg-surface px-1.5 py-0.5 rounded text-accent-light text-xs font-mono" {...props}>
                          {children}
                        </code>
                      ) : (
                        <CodeBlock language={lang}>{String(children).replace(/\n$/, '')}</CodeBlock>
                      )
                    },
                    a({ children, ...props }) {
                      return <a className="text-accent-light hover:underline" target="_blank" rel="noopener noreferrer" {...props}>{children}</a>
                    }
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>
              <div className="flex items-center justify-end gap-2 mt-1.5">
                <span className="text-xs text-text-muted">
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <MessageActions content={msg.content} />
            </div>
          </div>
        ))}

        {isResponding && (
          <div className="flex justify-start slide-up">
            <div className="rounded-2xl rounded-bl-md px-4 py-3" style={{
              background: 'var(--bubble-agent)',
              borderLeft: '2px solid var(--accent)',
            }}>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold text-white" style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))' }}>
                  P
                </div>
                <span className="text-xs text-text-muted uppercase tracking-wider font-medium">thinking</span>
              </div>
              <div className="h-2 w-32 rounded-full overflow-hidden" style={{ background: 'var(--bg-elevated)' }}>
                <div className="h-full w-full animate-shimmer" style={{
                  background: 'linear-gradient(90deg, transparent 0%, rgba(var(--accent-rgb),0.2) 50%, transparent 100%)',
                  backgroundSize: '200% 100%',
                }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Agent Suggestion Menu */}
      {showAgents && filteredAgents.length > 0 && (
        <div className="mx-4 mb-2 glass-modal rounded-2xl py-2 max-h-64 overflow-y-auto animate-slide-up border" style={{ borderColor: 'var(--border-subtle)' }}>
          <div className="px-4 py-2 text-xs text-text-muted uppercase tracking-wider font-medium border-b" style={{ borderColor: 'var(--border-subtle)' }}>
            Select Agent
          </div>
          {filteredAgents.map((agent) => (
            <AgentCard
              key={agent.id || agent.name}
              agent={agent}
              color={getAgentColor(agent.name || agent.id)}
              onClick={() => selectAgent(agent)}
            />
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="px-4 pb-4 pt-2">
        {filePreview && (
          <div className="mb-2 flex items-center gap-2 glass rounded-xl px-3 py-2 text-xs fade-in border" style={{ borderColor: 'var(--border-subtle)' }}>
            <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-text-secondary truncate">{filePreview.name}</span>
            <span className="text-text-muted">({(filePreview.size / 1024).toFixed(1)}KB)</span>
            <Button
              isIconOnly
              size="sm"
              variant="ghost"
              aria-label="Remove file"
              onPress={() => setFilePreview(null)}
              className="ml-auto text-text-muted hover:text-text-secondary min-w-0 h-auto p-1"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </Button>
          </div>
        )}

        <div className="flex items-end gap-2 glass-glow-border rounded-2xl p-2" style={{ background: 'var(--bg-surface)' }}>
          <Button
            isIconOnly
            variant="ghost"
            aria-label="Attach file"
            onPress={() => fileInputRef.current?.click()}
            className="text-text-muted hover:text-text-secondary"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept=".txt,.md,.pdf,.doc,.docx,.csv,.json,.py,.js,.ts,.jsx,.tsx"
          />

          <textarea
            ref={(el) => { textareaRef.current = el; inputRef.current = el }}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={isResponding ? 'Waiting for response...' : 'Message P.I.N.G.S... (@agent for specific agent)'}
            rows={1}
            className="flex-1 bg-transparent text-text-primary text-base placeholder-text-muted resize-none py-2.5 px-1 outline-none"
            style={{ minHeight: '40px', maxHeight: '150px', border: 'none' }}
          />

          <div className="relative flex-shrink-0" ref={modelDropdownRef}>
            <Button
              variant="ghost"
              onPress={() => setModelOpen(!modelOpen)}
              className="px-3 py-2 text-text-secondary text-xs flex items-center gap-1.5 max-w-[130px]"
              style={{ background: 'var(--bg-elevated)' }}
              aria-label="Select model"
            >
              <svg className="w-3 h-3 text-accent flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span className="truncate">{shortModelName}</span>
              <svg className={`w-2.5 h-2.5 transition-transform duration-200 flex-shrink-0 ${modelOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </Button>
            {modelOpen && models.length > 0 && (
              <div className="absolute bottom-full right-0 mb-2 w-60 glass-modal rounded-2xl py-2 z-50 max-h-64 overflow-y-auto animate-scale-in">
                <div className="px-4 py-2 text-xs text-text-muted uppercase tracking-wider font-medium border-b" style={{ borderColor: 'var(--border-subtle)' }}>
                  Select Model
                </div>
                {models.map(model => (
                  <Button
                    key={model.id}
                    fullWidth
                    variant="ghost"
                    onPress={() => { setSelectedModel(model.id); setModelOpen(false) }}
                    className={`px-4 py-2.5 text-xs flex items-center justify-between ${
                      selectedModel === model.id ? 'text-accent-light' : 'text-text-secondary'
                    }`}
                  >
                    <span className="truncate">{model.name}</span>
                    {selectedModel === model.id && (
                      <svg className="w-3.5 h-3.5 text-accent flex-shrink-0 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </Button>
                ))}
              </div>
            )}
          </div>

          <Button
            isIconOnly
            variant="light"
            aria-label="Send message"
            isDisabled={!input.trim() || isResponding}
            onPress={handleSend}
            className="btn-accent !rounded-xl flex-shrink-0"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </Button>
        </div>
      </div>
    </div>
  )
}

function exportChat(messages) {
  if (!messages || messages.length === 0) return
  try {
    const text = messages.map(m => `[${m.role.toUpperCase()}] ${m.content}`).join('\n\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `pings-chat-${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  } catch {}
}
