import React from 'react'

const ICONS = {
  tasks: (
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
  ),
  chat: (
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  ),
  calendar: (
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  ),
  search: (
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  ),
  server: (
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
    </svg>
  ),
  skills: (
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  ),
  history: (
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  folder: (
    <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
    </svg>
  ),
}

export default function EmptyState({ icon = 'folder', title, description, action, className = '', suggestions = [] }) {
  const showLogo = icon === 'chat' && !title

  return (
    <div className={`flex flex-col items-center justify-center py-12 text-center ${className}`}>
      {showLogo ? (
        <div className="animate-float mb-6">
          <svg viewBox="0 0 96 96" fill="none" className="w-20 h-20" style={{ filter: 'drop-shadow(0 0 20px rgba(var(--accent-rgb),0.3))' }}>
            <circle cx="48" cy="48" r="44" stroke="rgba(var(--accent-rgb),0.15)" strokeWidth="1" />
            <circle cx="48" cy="48" r="34" stroke="rgba(var(--accent-rgb),0.25)" strokeWidth="1" />
            <circle cx="48" cy="48" r="23" stroke="rgba(var(--accent-rgb),0.5)" strokeWidth="1.5" />
            <circle cx="48" cy="48" r="23" stroke="rgba(var(--accent-rgb),0.15)" strokeWidth="10" style={{ filter: 'blur(4px)' }} />
            <circle cx="48" cy="48" r="6" fill="var(--accent)" style={{ filter: 'drop-shadow(0 0 8px rgba(var(--accent-rgb),0.9))' }} />
            <circle cx="48" cy="48" r="3" fill="var(--accent-light)" />
          </svg>
        </div>
      ) : (
        <div className="text-text-muted/40 mb-4">
          {ICONS[icon] || ICONS.folder}
        </div>
      )}
      <h3 className="text-sm font-medium text-text-secondary mb-1">{title || 'Start a conversation'}</h3>
      {description && (
        <p className="text-xs text-text-muted max-w-xs">{description}</p>
      )}
      {suggestions.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2 justify-center max-w-md">
          {suggestions.map((sug, i) => (
            <button
              key={i}
              onClick={sug.onClick}
              className="px-3 py-1.5 rounded-full text-xs text-text-secondary glass hover:border-glow hover:text-accent-light transition-all duration-200"
            >
              {sug.label}
            </button>
          ))}
        </div>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
