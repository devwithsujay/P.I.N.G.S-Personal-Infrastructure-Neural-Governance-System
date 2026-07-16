import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react'
import { sendChat, chatUpload, getAgents, getModels, getSessionMessages, startResearch, getResearchQueue, listResearchRuns } from '../api'

const ChatContext = createContext(null)

const MAX_CACHED_MESSAGES = 500

function generateSessionId() {
  return crypto.randomUUID?.() || `session-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem('pings-chat-messages')
      return saved ? JSON.parse(saved) : []
    } catch { return [] }
  })
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('pings-chat-session') || generateSessionId()
  })
  const [isResponding, setIsResponding] = useState(false)
  const [isResearchResponding, setIsResearchResponding] = useState(false)
  const [isResearchQueued, setIsResearchQueued] = useState(false)
  const [agents, setAgents] = useState([])
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState(() => {
    return localStorage.getItem('pings-chat-model') || ''
  })

  const cancelledRef = useRef(false)
  const respondingRef = useRef(false)

  // Persist messages to localStorage
  useEffect(() => {
    if (messages.length > 0) {
      const toStore = messages.length > MAX_CACHED_MESSAGES
        ? messages.slice(messages.length - MAX_CACHED_MESSAGES)
        : messages
      localStorage.setItem('pings-chat-messages', JSON.stringify(toStore))
    }
  }, [messages])

  // Persist sessionId
  useEffect(() => {
    if (sessionId) localStorage.setItem('pings-chat-session', sessionId)
  }, [sessionId])

  // Persist selectedModel
  useEffect(() => {
    if (selectedModel) localStorage.setItem('pings-chat-model', selectedModel)
  }, [selectedModel])

  // Load agents, models, and research status on mount
  useEffect(() => {
    getAgents().then(res => {
      setAgents(Array.isArray(res) ? res : res?.agents || [])
    }).catch(() => {})

    getModels().then(res => {
      const list = res?.models || []
      setModels(list)
      if (!selectedModel && res?.default) setSelectedModel(res.default)
      else if (list.length > 0 && selectedModel) {
        const match = list.find(m => m.id === selectedModel)
        if (!match) setSelectedModel(list[0].id)
      } else if (list.length > 0 && !selectedModel) {
        setSelectedModel(list[0].id)
      }
    }).catch(() => {
      const fallback = [
        { id: "opencode/mimo-v2.5-free", name: "MiMo V2.5 Free" },
        { id: "opencode/deepseek-v4-flash-free", name: "DeepSeek V4 Flash Free" },
        { id: "opencode/nemotron-3-ultra-free", name: "Nemotron 3 Ultra Free" },
        { id: "opencode/big-pickle", name: "Big Pickle" },
        { id: "opencode/north-mini-code-free", name: "North Mini Code Free" },
      ]
      setModels(fallback)
      if (!selectedModel) setSelectedModel(fallback[0].id)
    })

    // Load research status
    const loadResearchStatus = async () => {
      try {
        const [queue, runs] = await Promise.all([
          getResearchQueue().catch(() => []),
          listResearchRuns().catch(() => []),
        ])
        const queued = Array.isArray(queue) ? queue : queue?.queue || []
        const researchRuns = Array.isArray(runs) ? runs : runs?.runs || []
        setIsResearchQueued(queued.length > 0)
        setIsResearchResponding(researchRuns.some(r => r.status === 'running'))
      } catch {}
    }

    loadResearchStatus()
    // Poll for research status changes
    const researchInterval = setInterval(loadResearchStatus, 3000)
    return () => clearInterval(researchInterval)
  }, [])

  // Load history from server on mount if messages are empty
  useEffect(() => {
    if (messages.length === 0 && sessionId) {
      getSessionMessages(sessionId).then(res => {
        const serverMessages = Array.isArray(res) ? res : res?.messages || res?.turns || []
        if (serverMessages.length > 0) {
          setMessages(serverMessages.map((m, i) => ({
            id: m.id || `hist-${i}-${Date.now()}`,
            role: m.role || (m.sender === 'user' ? 'user' : 'agent'),
            content: m.content || m.message || m.text || '',
            agent: m.agent,
            model_used: m.model_used,
            timestamp: m.timestamp || new Date().toISOString(),
          })))
        }
      }).catch(() => {
        console.warn('Failed to load chat history from server')
      })
    }
  }, [])

  // Listen for new-chat event
  useEffect(() => {
    const handler = () => {
      setMessages([])
      const newId = generateSessionId()
      setSessionId(newId)
      localStorage.removeItem('pings-chat-messages')
      localStorage.setItem('pings-chat-session', newId)
    }
    window.addEventListener('new-chat', handler)
    return () => window.removeEventListener('new-chat', handler)
  }, [])

  const sendMessage = useCallback(async (text, file = null) => {
    if (respondingRef.current) return

    let messageText = text
    let agentName = null

    const mentionMatch = text.match(/^@(\w+)\s*/)
    if (mentionMatch) {
      agentName = mentionMatch[1]
      messageText = text.slice(mentionMatch[0].length)
    }

    const userMsg = {
      id: crypto.randomUUID?.() || Date.now().toString(),
      role: 'user',
      content: messageText,
      agent: agentName,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMsg])
    setIsResponding(true)
    respondingRef.current = true
    cancelledRef.current = false

    try {
      let res
      if (file) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('message', messageText)
        if (sessionId) formData.append('session_id', sessionId)
        res = await chatUpload(formData)
      } else {
        const payload = {
          message: messageText,
          session_id: sessionId,
          agent: agentName,
          model: selectedModel || undefined
        }
        res = await sendChat(payload)
      }

      if (cancelledRef.current) return

      if (res.session_id && !sessionId) setSessionId(res.session_id)

      const agentMsg = {
        id: crypto.randomUUID?.() || (Date.now() + 1).toString(),
        role: 'agent',
        content: res.response || res.message || res.reply || 'No response received.',
        agent: res.agent || agentName || 'default',
        model_used: res.model_used,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, agentMsg])
    } catch (err) {
      if (cancelledRef.current) return
      const errorMsg = {
        id: crypto.randomUUID?.() || (Date.now() + 1).toString(),
        role: 'agent',
        content: 'Something went wrong. Try again.',
        agent: 'system',
        timestamp: new Date().toISOString(),
        isError: true,
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsResponding(false)
      respondingRef.current = false
    }
  }, [sessionId, selectedModel])

  const clearMessages = useCallback(() => {
    cancelledRef.current = true
    respondingRef.current = false
    setIsResponding(false)
    setMessages([])
    const newId = generateSessionId()
    setSessionId(newId)
    localStorage.removeItem('pings-chat-messages')
    localStorage.setItem('pings-chat-session', newId)
  }, [])

  return (
    <ChatContext.Provider value={{
      messages,
      isResponding,
      sessionId,
      agents,
      models,
      selectedModel,
      setSelectedModel,
      sendMessage,
      clearMessages,
    }}>
      {children}
    </ChatContext.Provider>
  )
}

export const useResearchStatus = () => {
  const context = useContext(ChatContext)
  if (!context) {
    throw new Error('useResearchStatus must be used within ChatProvider')
  }
  return {
    isResearchQueued: context.isResearchQueued,
    isResearchResponding: context.isResearchResponding,
    isResearchActive: context.isResearchQueued || context.isResearchResponding,
  }
}

export const useChat = () => useContext(ChatContext)
