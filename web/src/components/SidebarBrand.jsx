import React from 'react'

export default function SidebarBrand({ collapsed }) {
  return (
    <div className="px-4 py-5 border-b-2 flex items-center gap-3" style={{ borderColor: 'var(--border-subtle)' }}>
      <div className="relative w-6 h-6 flex-shrink-0">
        <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-6 h-6">
          <circle cx="16" cy="16" r="3" fill="var(--accent)" />
          <circle cx="16" cy="16" r="7" stroke="var(--accent)" strokeWidth="1.5" opacity="0.7" />
          <circle cx="16" cy="16" r="11" stroke="var(--accent)" strokeWidth="1" opacity="0.4" />
          <circle cx="16" cy="16" r="14.5" stroke="var(--accent)" strokeWidth="0.5" opacity="0.2" />
          <circle cx="16" cy="9" r="1.5" fill="var(--accent-light)" opacity="0.9" />
          <circle cx="22" cy="13" r="1" fill="var(--accent-light)" opacity="0.6" />
          <circle cx="21" cy="21" r="1.2" fill="var(--accent-light)" opacity="0.5" />
          <line x1="16" y1="16" x2="16" y2="9" stroke="var(--accent-light)" strokeWidth="0.5" opacity="0.3" />
          <line x1="16" y1="16" x2="22" y2="13" stroke="var(--accent-light)" strokeWidth="0.5" opacity="0.2" />
          <line x1="16" y1="16" x2="21" y2="21" stroke="var(--accent-light)" strokeWidth="0.5" opacity="0.2" />
        </svg>
      </div>
      {!collapsed && (
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold tracking-wide" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
              P.I.N.G.S
            </span>
            <span className="relative flex h-1.5 w-1.5 flex-shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ background: 'var(--accent)' }} />
              <span className="relative inline-flex rounded-full h-full w-full" style={{ background: 'var(--accent)' }} />
            </span>
          </div>
          <div className="text-xs leading-tight mt-0.5" style={{ color: 'var(--text-secondary)' }}>
            Personal Infrastructure &amp; Neural Governance System
          </div>
        </div>
      )}
    </div>
  )
}
