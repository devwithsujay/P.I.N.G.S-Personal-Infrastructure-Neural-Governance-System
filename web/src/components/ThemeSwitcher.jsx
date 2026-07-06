import React from 'react'
import { useTheme, THEMES } from '../context/ThemeContext'

const THEME_META = {
  'claude': { bg: '#faf9f5', surface: '#efe9de', accent: '#cc785c', text: '#141413', textSecondary: '#3d3d3a', desc: 'Warm cream, coral accent' },
  'mistral': { bg: '#ffffff', surface: '#fff8e0', accent: '#fa520f', text: '#1f1f1f', textSecondary: '#4a4a4a', desc: 'White canvas, orange sunset' },
  'cohere': { bg: '#ffffff', surface: '#eeece7', accent: '#1863dc', text: '#212121', textSecondary: '#75758a', desc: 'White canvas, blue accent' },
  'replicate': { bg: '#f9f7f3', surface: '#ffffff', accent: '#ea2804', text: '#202020', textSecondary: '#3a3a3a', desc: 'Warm cream, hot orange' },
  'opencode': { bg: '#fdfcfc', surface: '#f1eeee', accent: '#201d1d', text: '#201d1d', textSecondary: '#424245', desc: 'Blush cream, monospace' },
  'voltagent': { bg: '#101010', surface: '#1a1a1a', accent: '#00d992', text: '#f2f2f2', textSecondary: '#bdbdbd', desc: 'Dark canvas, green accent' },
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
              border: `1px solid ${isActive ? t.accent : 'var(--border-subtle)'}`,
              boxShadow: isActive ? `0 0 20px ${t.accent}33` : 'none',
            }}
          >
            <div className="flex gap-1.5 flex-shrink-0">
              <div className="w-5 h-5 rounded-full" style={{ background: t.bg, border: '1px solid var(--border-subtle)' }} />
              <div className="w-5 h-5 rounded-full" style={{ background: t.accent }} />
              <div className="w-5 h-5 rounded-full" style={{ background: t.surface, border: '1px solid var(--border-subtle)' }} />
            </div>

            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium" style={{ color: isActive ? t.accent : t.text }}>
                {meta.name}
              </div>
              <div className="text-[11px]" style={{ color: isActive ? t.accent : t.textSecondary }}>
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
