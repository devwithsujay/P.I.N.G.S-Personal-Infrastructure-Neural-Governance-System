import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { Button } from '@heroui/react'

const ToastContext = createContext(null)

let toastId = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((message, type = 'info', duration = 3000) => {
    const id = ++toastId
    setToasts(prev => [...prev, { id, message, type, duration }])
    if (duration > 0) {
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id))
      }, duration)
    }
    return id
  }, [])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const toast = useCallback((msg) => addToast(msg, 'info'), [addToast])
  toast.success = (msg) => addToast(msg, 'success')
  toast.error = (msg) => addToast(msg, 'error', 5000)
  toast.warning = (msg) => addToast(msg, 'warning', 4000)
  toast.info = (msg) => addToast(msg, 'info')

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none" style={{ maxWidth: '380px' }}>
        {toasts.map(t => (
          <ToastItem key={t.id} toast={t} onRemove={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}

const BORDER_COLORS = {
  success: 'var(--status-success)',
  error: 'var(--status-error)',
  warning: 'var(--status-warning)',
  info: 'var(--status-info)',
}

const ICONS = {
  success: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  error: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  warning: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
    </svg>
  ),
  info: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
}

function ToastItem({ toast, onRemove }) {
  const [exiting, setExiting] = useState(false)
  const [progress, setProgress] = useState(100)
  const duration = toast.duration || 3000

  useEffect(() => {
    const start = Date.now()
    const tick = () => {
      const elapsed = Date.now() - start
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100)
      setProgress(remaining)
      if (remaining > 0) requestAnimationFrame(tick)
    }
    const raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [duration])

  useEffect(() => {
    const t = setTimeout(() => setExiting(true), duration - 300)
    return () => clearTimeout(t)
  }, [duration])

  const handleAnimEnd = () => {
    if (exiting) onRemove(toast.id)
  }

  return (
    <div
      onTransitionEnd={handleAnimEnd}
      className={`pointer-events-auto glass-strong rounded-lg flex items-start gap-3 border shadow-lg shadow-black/20 overflow-hidden
        ${exiting ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'}`}
      style={{
        borderLeft: `3px solid ${BORDER_COLORS[toast.type]}`,
        transition: 'opacity 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
      }}
    >
      <div className="flex-1 px-4 py-3">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex-shrink-0" style={{ color: BORDER_COLORS[toast.type] }}>{ICONS[toast.type]}</span>
          <span className="text-sm text-text-primary flex-1">{toast.message}</span>
          <Button
            isIconOnly
            size="sm"
            variant="ghost"
            aria-label="Dismiss"
            onPress={() => onRemove(toast.id)}
            className="flex-shrink-0 mt-0.5 min-w-0 h-auto p-0.5 text-text-muted hover:text-text-primary"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </Button>
        </div>
      </div>
      <div className="h-0.5 w-full" style={{ position: 'absolute', bottom: 0, left: 0 }}>
        <div
          className="h-full transition-none"
          style={{
            width: `${progress}%`,
            background: BORDER_COLORS[toast.type],
            opacity: 0.5,
          }}
        />
      </div>
    </div>
  )
}
