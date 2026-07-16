import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Button } from '@heroui/react'
import SidebarBrand from './SidebarBrand'
import { useChat } from '../context/ChatContext'
import { useTheme } from '../context/ThemeContext'

const navItems = [
  { path: '/', icon: ChatIcon, label: 'Chat', shortcut: '1' },
  { path: '/research', icon: ResearchIcon, label: 'Research', shortcut: '2' },
  { path: '/tasks', icon: TasksIcon, label: 'Tasks', shortcut: '3' },
  { path: '/calendar', icon: CalendarIcon, label: 'Calendar', shortcut: '4' },
  { path: '/skills', icon: SkillsIcon, label: 'Skills', shortcut: '5' },
  { path: '/homelab', icon: HomeLabIcon, label: 'HomeLab', shortcut: '6' },
  { path: '/automations', icon: AutomationsIcon, label: 'Automations', shortcut: '7' },
  { path: '/history', icon: HistoryIcon, label: 'History', shortcut: '8' },
]

function ResearchNavIndicator({ collapsed }) {
  const { isResearchQueued, isResearchResponding } = useChat()

  if (!isResearchQueued && !isResearchResponding) {
    return null
  }

  return (
    <div className="absolute right-1 top-1/2 -translate-y-1/2 flex gap-1">
      {isResearchQueued && (
        <span
          className="w-1.5 h-1.5 rounded-full bg-warning animate-pulse"
          title="Research queued"
          aria-label="Research queued"
        />
      )}
      {isResearchResponding && (
        <span
          className="w-1.5 h-1.5 rounded-full bg-success animate-pulse"
          title="Research running"
          aria-label="Research running"
        />
      )}
    </div>
  )
}

const isMac = typeof navigator !== 'undefined' && navigator.platform?.includes('Mac')
const modKey = isMac ? '⌘' : 'Ctrl+'

export default function Sidebar({ collapsed, onToggleCollapse }) {
  const navigate = useNavigate()
  const { isResponding } = useChat()

  const handleNewChat = () => {
    navigate('/')
    window.dispatchEvent(new CustomEvent('new-chat'))
  }

  return (
    <aside className={`sidebar-desktop hidden md:flex fixed left-0 top-0 h-full z-40 flex-col transition-all duration-300 ${collapsed ? 'w-[68px]' : 'w-64'}`} style={{ background: 'var(--bg-surface)', borderRight: '1px solid var(--border-subtle)' }}>
      <SidebarBrand collapsed={collapsed} />

      <div className="px-3 mt-8 mb-3">
        <Button
          fullWidth
          aria-label="New Chat"
          onPress={handleNewChat}
          className="rounded-xl text-sm font-medium"
          style={{
            color: 'var(--accent-text)',
            background: 'var(--accent)',
          }}
        >
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {!collapsed && <span>New Chat</span>}
        </Button>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 space-y-0.5" aria-label="Main navigation">
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `sidebar-link ${collapsed ? 'justify-center' : ''}`
            }
            title={collapsed ? `${item.label} (${modKey}${item.shortcut})` : undefined}
          >
            {({ isActive }) => (
              <>
                <item.icon className={`w-[18px] h-[18px] flex-shrink-0 ${isActive ? 'text-accent' : ''}`} />
                {!collapsed && <span className="flex-1 text-left">{item.label}</span>}
                {!collapsed && item.path === '/' && isResponding && (
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: 'var(--accent)',
                      display: 'inline-block',
                      marginRight: 4,
                      animation: 'sidebar-pulse 1.5s ease-in-out infinite',
                    }}
                    role="status"
                    aria-label="Agent is responding"
                  />
                )}
                {!collapsed && !isActive && (
                  <span className="text-[10px] text-text-muted font-mono opacity-0 group-hover:opacity-100 transition-opacity">{modKey}{item.shortcut}</span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 pb-3 space-y-0.5 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center gap-2.5 px-3 py-2.5">
          <StatusDot />
          {!collapsed && (
            <span className="text-xs text-text-muted">v2.0</span>
          )}
        </div>
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `sidebar-link ${collapsed ? 'justify-center' : ''}`
          }
        >
          <SettingsIcon className="w-[18px] h-[18px] flex-shrink-0" />
          {!collapsed && <span>Settings</span>}
        </NavLink>
        <Button
          variant="ghost"
          fullWidth
          onPress={onToggleCollapse}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="sidebar-link justify-start"
        >
          <CollapseIcon className={`w-[18px] h-[18px] flex-shrink-0 transition-transform ${collapsed ? 'rotate-180' : ''}`} />
          {!collapsed && <span>Collapse</span>}
        </Button>
      </div>
    </aside>
  )
}

function StatusDot() {
  return (
    <span className="relative flex h-2 w-2 flex-shrink-0">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ background: 'var(--status-success)' }} />
      <span className="relative inline-flex rounded-full h-2 w-2" style={{ background: 'var(--status-success)' }} />
    </span>
  )
}

function ChatIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  )
}

function ResearchIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  )
}

function TasksIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
    </svg>
  )
}

function CalendarIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  )
}

function SkillsIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  )
}

function HomeLabIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
    </svg>
  )
}

function AutomationsIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function HistoryIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function SettingsIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  )
}

function CollapseIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
    </svg>
  )
}
