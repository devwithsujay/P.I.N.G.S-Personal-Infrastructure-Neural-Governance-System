import React from 'react'
import { useTheme, THEMES } from '../context/ThemeContext'

const THEME_META = {
  'deep-space':   { bg: '#0a0a0f', surface: '#0d0d14', accent: '#3b82f6', desc: 'Cool blue on deep dark' },
  'terminal':     { bg: '#050d05', surface: '#080d08', accent: '#22c55e', desc: 'Green phosphor CRT' },
  'cyberpunk':    { bg: '#0a0514', surface: '#0d0818', accent: '#8b5cf6', desc: 'Purple neon nightlife' },
  'warm-dark':    { bg: '#0f0a05', surface: '#130d08', accent: '#f59e0b', desc: 'Warm amber glow' },
  'slate-indigo': { bg: '#0a0c14', surface: '#0d0f18', accent: '#6366f1', desc: 'Indigo twilight' },
}

export default function ThemeSwitcher() {
  const { theme: currentTheme, setTheme } = useTheme()

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {Object.entries(THEMES).map(([id, meta]) => {
        const t = THEME_META[id]
        const isActive = currentTheme === id

        return (
          <button
            key={id}
            onClick={() => setTheme(id)}
            className={`relative flex items-center gap-3 p-3 rounded-xl text-left transition-all duration-200 ${
              isActive ? 'ring-2' : 'hover:ring-1'
            }`}
            style={{
              background: t.bg,
              borderColor: isActive ? t.accent : 'transparent',
              border: `1px solid ${isActive ? t.accent : 'var(--border-subtle)'}`,
              ringColor: isActive ? t.accent : 'transparent',
              boxShadow: isActive ? `0 0 20px ${t.accent}33` : 'none',
            }}
          >
            {/* 3-swatch preview */}
            <div className="flex gap-1.5 flex-shrink-0">
              <div className="w-5 h-5 rounded-full" style={{ background: t.bg, border: '1px solid var(--border-subtle)' }} />
              <div className="w-5 h-5 rounded-full" style={{ background: t.accent }} />
              <div className="w-5 h-5 rounded-full" style={{ background: t.surface, border: '1px solid var(--border-subtle)' }} />
            </div>

            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium" style={{ color: isActive ? t.accent : '#e2e2f0' }}>
                {meta.name}
              </div>
              <div className="text-[11px]" style={{ color: isActive ? t.accent : '#6b6b80' }}>
                {t.desc}
              </div>
            </div>

            {isActive && (
              <div className="absolute top-2 right-2 flex-shrink-0">
                <svg className="w-4 h-4" style={{ color: t.accent }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            )}
          </button>
        )
      })}
    </div>
  )
}
