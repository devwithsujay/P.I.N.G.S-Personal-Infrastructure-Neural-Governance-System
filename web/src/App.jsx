import React, { useState, useEffect, useCallback } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import MobileNav from './components/MobileNav'
import BootSequence from './components/BootSequence'
import Chat from './pages/Chat'
import ResearchPage from './pages/ResearchPage'
import Tasks from './pages/Tasks'
import Calendar from './pages/Calendar'
import HomeLab from './pages/HomeLab'
import Skills from './pages/Skills'
import History from './pages/History'

import Settings from './pages/Settings'

export default function App() {
  const [booted, setBooted] = useState(() => {
    return localStorage.getItem('pings-booted') === 'true'
  })
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const savedCollapsed = localStorage.getItem('pings-sidebar-collapsed')
    if (savedCollapsed === 'true') setSidebarCollapsed(true)
  }, [])

  const handleBootComplete = useCallback(() => {
    setBooted(true)
    localStorage.setItem('pings-booted', 'true')
  }, [])

  useEffect(() => {
    const handleKey = (e) => {
      if (!e.metaKey && !e.ctrlKey) return
      const routes = {
        '1': '/',
        '2': '/research',
        '3': '/tasks',
        '4': '/calendar',
        '5': '/skills',
        '6': '/homelab',

        '8': '/history',
      }
      const key = e.key
      if (routes[key]) {
        e.preventDefault()
        navigate(routes[key])
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [navigate])

  const toggleSidebar = () => {
    setSidebarCollapsed(prev => {
      const next = !prev
      localStorage.setItem('pings-sidebar-collapsed', next.toString())
      return next
    })
  }

  if (!booted) {
    return <BootSequence onComplete={handleBootComplete} />
  }

  return (
    <div className="mesh-bg min-h-screen font-body">
      <Sidebar collapsed={sidebarCollapsed} onToggleCollapse={toggleSidebar} />

      <main className={`main-content min-h-screen transition-all duration-300 ${
        sidebarCollapsed ? 'md:ml-[68px]' : 'md:ml-64'
      }`}>
        <div className="h-screen flex flex-col">
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/homelab" element={<HomeLab />} />
            <Route path="/skills" element={<Skills />} />
            <Route path="/history" element={<History />} />

            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </main>

      <MobileNav />
    </div>
  )
}
