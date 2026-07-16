import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

const ThemeContext = createContext(null)

const THEME_KEY = 'pings-theme'
const DEFAULT_THEME = 'claude'

function getSystemTheme() {
  if (typeof window === 'undefined') return null
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'voltagent' : null
}

const THEMES = {
  'claude': { name: 'Claude Editorial', accent: '#cc785c' },
  'mistral': { name: 'Mistral AI', accent: '#fa520f' },
  'cohere': { name: 'Cohere', accent: '#1863dc' },
  'replicate': { name: 'Replicate', accent: '#ea2804' },
  'opencode': { name: 'OpenCode', accent: '#201d1d' },
  'voltagent': { name: 'Voltagent', accent: '#00d992' },
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

  const fontUi = getComputedStyle(root).getPropertyValue('--font-ui').trim()
  if (fontUi) {
    document.body.style.fontFamily = fontUi
  }

  const accent = getComputedStyle(root).getPropertyValue('--accent').trim()
  if (accent && accent.startsWith('#')) {
    const { r, g, b } = hexToRgb(accent)
    root.style.setProperty('--accent-rgb', `${r}, ${g}, ${b}`)
    root.style.setProperty('--accent-light', `color-mix(in srgb, ${accent} 70%, white)`)
    root.style.setProperty('--accent-dark', accent)
    root.style.setProperty('--accent-glow', `rgba(${r}, ${g}, ${b}, 0.35)`)
    root.style.setProperty('--border-glow', `rgba(${r}, ${g}, ${b}, 0.25)`)
  }
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => {
    try {
      const saved = localStorage.getItem(THEME_KEY)
      if (saved && THEMES[saved]) return saved
      return getSystemTheme() || DEFAULT_THEME
    } catch {
      return getSystemTheme() || DEFAULT_THEME
    }
  })

  useEffect(() => {
    applyThemeVars(theme)
  }, [])

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e) => {
      const saved = localStorage.getItem(THEME_KEY)
      if (saved) return
      applyThemeVars(e.matches ? 'voltagent' : DEFAULT_THEME)
      setThemeState(e.matches ? 'voltagent' : DEFAULT_THEME)
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
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
