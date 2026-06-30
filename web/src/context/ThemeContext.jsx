import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

const ThemeContext = createContext(null)

const THEME_KEY = 'pings-theme'
const DEFAULT_THEME = 'deep-space'

const THEMES = {
  'deep-space':   { name: 'Deep Space',   accent: '#3b82f6' },
  'terminal':     { name: 'Terminal',      accent: '#22c55e' },
  'cyberpunk':    { name: 'Cyberpunk',     accent: '#8b5cf6' },
  'warm-dark':    { name: 'Warm Dark',     accent: '#f59e0b' },
  'slate-indigo': { name: 'Slate Indigo',  accent: '#6366f1' },
}

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return { r, g, b }
}

function applyThemeVars(themeId) {
  const root = document.documentElement
  root.setAttribute('data-theme', themeId)

  // Apply --font-ui to body for terminal theme monospace override
  const fontUi = getComputedStyle(root).getPropertyValue('--font-ui').trim()
  if (fontUi) {
    document.body.style.fontFamily = fontUi
  }

  // Derive --accent-rgb from --accent for legacy compatibility
  const accent = getComputedStyle(root).getPropertyValue('--accent').trim()
  if (accent && accent.startsWith('#')) {
    const { r, g, b } = hexToRgb(accent)
    root.style.setProperty('--accent-rgb', `${r}, ${g}, ${b}`)

    // Derive legacy accent variants
    root.style.setProperty('--accent-light', `color-mix(in srgb, ${accent} 70%, white)`)
    root.style.setProperty('--accent-dark', accent)
    root.style.setProperty('--accent-glow', `rgba(${r}, ${g}, ${b}, 0.35)`)
    root.style.setProperty('--border-glow', `rgba(${r}, ${g}, ${b}, 0.25)`)
  }
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => {
    try {
      return localStorage.getItem(THEME_KEY) || DEFAULT_THEME
    } catch {
      return DEFAULT_THEME
    }
  })

  // Apply theme on mount (synchronous — no flash)
  useEffect(() => {
    applyThemeVars(theme)
  }, [])

  const setTheme = useCallback((id) => {
    if (!THEMES[id]) return
    setThemeState(id)
    try {
      localStorage.setItem(THEME_KEY, id)
    } catch {}
    applyThemeVars(id)
  }, [])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes: THEMES }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}

export { THEMES }
