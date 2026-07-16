import React, { useState, useEffect, useCallback, useRef } from 'react'
import { getHomelabStatus, testSshConnection, saveSshConfig, containerAction } from '../api'
import { useToast } from '../components/Toast'
import { Button } from '@heroui/react'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'

function TerminalPanel({ active }) {
  const containerRef = useRef(null)
  const termRef = useRef(null)
  const fitAddonRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || termRef.current) return

    const term = new XTerm({
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
      fontSize: 14,
      lineHeight: 1.2,
      theme: {
        background: '#0d1117',
        foreground: '#c9d1d9',
        cursor: '#58a6ff',
        cursorAccent: '#0d1117',
        selectionBackground: '#264f78',
      },
      cursorBlink: true,
      cursorStyle: 'bar',
      scrollback: 10000,
      allowProposedApi: true,
    })

    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.loadAddon(new WebLinksAddon())
    term.open(containerRef.current)
    termRef.current = term
    fitAddonRef.current = fitAddon

    setTimeout(() => { fitAddon.fit(); term.focus() }, 100)

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${wsProtocol}://${window.location.host}/api/ws/terminal`)

    ws.onopen = () => {
      const el = document.getElementById('term-status')
      if (el) el.textContent = 'Connected'
      const dot = document.getElementById('term-status-dot')
      if (dot) dot.className = 'w-2 h-2 rounded-full bg-green-500'
      term.focus()
    }

    ws.onmessage = (event) => {
      const write = (text) => term.write(text)
      if (event.data instanceof Blob) {
        event.data.text().then(write)
      } else {
        write(event.data)
      }
    }

    ws.onclose = () => {
      const el = document.getElementById('term-status')
      if (el) el.textContent = 'Disconnected'
      const dot = document.getElementById('term-status-dot')
      if (dot) dot.className = 'w-2 h-2 rounded-full bg-red-500'
    }

    ws.onerror = () => {
      const el = document.getElementById('term-status')
      if (el) el.textContent = 'Error'
    }

    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data)
      }
    })

    const onResize = () => { try { fitAddon.fit() } catch {} }
    window.addEventListener('resize', onResize)

    return () => {
      window.removeEventListener('resize', onResize)
      ws.close()
      term.dispose()
      termRef.current = null
    }
  }, [])

  useEffect(() => {
    if (active && termRef.current) {
      setTimeout(() => {
        try { fitAddonRef.current?.fit() } catch {}
        termRef.current?.focus()
      }, 50)
    }
  }, [active])

  const handleClick = () => { termRef.current?.focus() }

  return (
    <div className="slide-up" style={{ height: 'calc(100vh - 220px)', minHeight: '500px' }}>
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border-subtle, #30363d)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', gap: '6px' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f57' }} />
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#febc2e' }} />
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#28c840' }} />
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'monospace', marginLeft: '8px' }}>pings@host ~ bash</span>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span id="term-status-dot" style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f85149' }} />
            <span id="term-status" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Connecting...</span>
          </div>
        </div>
        <div ref={containerRef} onClick={handleClick} style={{ flex: 1, background: 'var(--bg-base)', cursor: 'text' }} />
      </div>
    </div>
  )
}

export default function HomeLab() {
  const [status, setStatus] = useState(null)
  const [containers, setContainers] = useState([])
  const [system, setSystem] = useState(null)
  const [sshConfig, setSshConfig] = useState({ host: '', port: '22', user: '', auth_type: 'key', key_path: '', password: '' })
  const [testResult, setTestResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('terminal')
  const [actioningName, setActioningName] = useState(null)
  const toast = useToast()

  const loadStatus = useCallback(async () => {
    try {
      const res = await getHomelabStatus()
      setStatus(res)
      setContainers(res?.containers || [])
      setSystem(res?.system || null)
      if (res?.ssh_config) setSshConfig(res.ssh_config)
    } catch {}
  }, [])

  useEffect(() => { loadStatus() }, [loadStatus])
  useEffect(() => {
    const interval = setInterval(loadStatus, 10000)
    return () => clearInterval(interval)
  }, [loadStatus])

  const handleTestConnection = async () => {
    setLoading(true)
    setTestResult(null)
    try {
      const res = await testSshConnection(sshConfig)
      setTestResult({ success: true, message: res?.message || 'Connected successfully' })
      toast.success('SSH connection successful')
    } catch (err) {
      setTestResult({ success: false, message: err.message })
      toast.error('SSH connection failed')
    } finally { setLoading(false) }
  }

  const handleSaveSsh = async () => {
    try { await saveSshConfig(sshConfig); toast.success('SSH config saved') }
    catch { toast.error('Failed to save SSH config') }
  }

  const handleContainerAction = async (action, name) => {
    setActioningName(name)
    try {
      await containerAction(action, name)
      toast.success(`${action}ed ${name}`)
      loadStatus()
    } catch (err) {
      toast.error(`Failed to ${action} ${name}`)
    } finally {
      setActioningName(null)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 glass-strong border-b flex items-center gap-2 shrink-0" style={{ borderColor: 'var(--border-subtle)' }}>
        <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
        </svg>
        <span className="font-brand text-sm font-medium text-text-primary">HomeLab</span>
        <div className="ml-auto flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${status?.host_reachable || status?.connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-text-muted">{status?.host_reachable || status?.connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <div className={`flex-1 ${activeTab !== 'terminal' ? 'overflow-y-auto' : ''} px-4 py-4`}>
        <div className={activeTab === 'terminal' ? '' : 'max-w-4xl mx-auto space-y-6'}>
          {activeTab !== 'terminal' && system && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 slide-up">
              <StatCard label="CPU" value={`${system.cpu_percent || 0}%`} color="#6c5ce7" />
              <StatCard label="Memory" value={`${system.memory_percent || 0}%`} color="#00cec9" />
              <StatCard label="Disk" value={`${system.disk_percent || 0}%`} color="#fdcb6e" />
              <StatCard label="Uptime" value={system.uptime || 'N/A'} color="#e17055" />
            </div>
          )}

          <div className="flex gap-2 overflow-x-auto pb-1 shrink-0">
            {['terminal', 'containers', 'ssh'].map(tab => (
              <Button key={tab} variant="light" onPress={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all capitalize ${activeTab === tab ? 'btn-primary' : 'bg-bg-surface text-text-muted hover:text-text-secondary'}`}>
                {tab}
              </Button>
            ))}
          </div>

          {activeTab === 'terminal' && <TerminalPanel active={activeTab === 'terminal'} />}

          {activeTab === 'containers' && (
            <div className="slide-up">
              {containers.length === 0 ? (
                <div className="text-center py-12 text-text-muted text-sm card rounded-xl">No containers detected</div>
              ) : (
                <div className="card rounded-xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b" style={{ borderColor: 'var(--border-subtle)' }}>
                          <th className="text-left px-4 py-3 text-xs text-text-muted font-medium">Name</th>
                          <th className="text-left px-4 py-3 text-xs text-text-muted font-medium">Image</th>
                          <th className="text-left px-4 py-3 text-xs text-text-muted font-medium">Status</th>
                          <th className="text-left px-4 py-3 text-xs text-text-muted font-medium">Ports</th>
                          <th className="text-left px-4 py-3 text-xs text-text-muted font-medium">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {containers.map((c, i) => (
                          <tr key={c.id || i} className="border-b hover:bg-bg-surface/30 transition-colors" style={{ borderColor: 'var(--border-subtle)' }}>
                            <td className="px-4 py-3 text-text-primary font-medium">{c.name || c.Names}</td>
                            <td className="px-4 py-3 text-text-secondary text-xs font-mono">{c.image || c.Image}</td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${(() => { const s = (c.status || c.state || c.Status || '').toLowerCase(); if (s.includes('paused')) return 'bg-yellow-500/20 text-yellow-400'; if (s.includes('up') || s.includes('running')) return 'bg-green-500/20 text-green-400'; return 'bg-red-500/20 text-red-400'; })()}`}>
                                {c.status || c.state || c.Status || 'unknown'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-text-muted text-xs font-mono">{c.ports || c.Ports || '-'}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-1.5">
                                {(() => {
                                  const s = (c.status || '').toLowerCase()
                                  const isPaused = s.includes('paused')
                                  const isRunning = s.includes('up') && !isPaused
                                  if (isPaused) return (
                                    <>
                                      <button onClick={() => handleContainerAction('unpause', c.name)} disabled={actioningName === c.name}
                                        className="px-2 py-1 rounded text-xs font-medium bg-green-500/15 text-green-400 hover:bg-green-500/25 transition-colors disabled:opacity-40">
                                        {actioningName === c.name ? '...' : 'Start'}
                                      </button>
                                      <button onClick={() => handleContainerAction('restart', c.name)} disabled={actioningName === c.name}
                                        className="px-2 py-1 rounded text-xs font-medium bg-yellow-500/15 text-yellow-400 hover:bg-yellow-500/25 transition-colors disabled:opacity-40">
                                        {actioningName === c.name ? '...' : 'Restart'}
                                      </button>
                                    </>
                                  )
                                  if (isRunning) return (
                                    <>
                                      <button onClick={() => handleContainerAction('pause', c.name)} disabled={actioningName === c.name}
                                        className="px-2 py-1 rounded text-xs font-medium bg-yellow-500/15 text-yellow-400 hover:bg-yellow-500/25 transition-colors disabled:opacity-40">
                                        {actioningName === c.name ? '...' : 'Pause'}
                                      </button>
                                      <button onClick={() => handleContainerAction('restart', c.name)} disabled={actioningName === c.name}
                                        className="px-2 py-1 rounded text-xs font-medium bg-blue-500/15 text-blue-400 hover:bg-blue-500/25 transition-colors disabled:opacity-40">
                                        {actioningName === c.name ? '...' : 'Restart'}
                                      </button>
                                    </>
                                  )
                                  return (
                                    <>
                                      <button onClick={() => handleContainerAction('start', c.name)} disabled={actioningName === c.name}
                                        className="px-2 py-1 rounded text-xs font-medium bg-green-500/15 text-green-400 hover:bg-green-500/25 transition-colors disabled:opacity-40">
                                        {actioningName === c.name ? '...' : 'Start'}
                                      </button>
                                      <button onClick={() => handleContainerAction('restart', c.name)} disabled={actioningName === c.name}
                                        className="px-2 py-1 rounded text-xs font-medium bg-yellow-500/15 text-yellow-400 hover:bg-yellow-500/25 transition-colors disabled:opacity-40">
                                        {actioningName === c.name ? '...' : 'Restart'}
                                      </button>
                                    </>
                                  )
                                })()}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'ssh' && (
            <div className="card rounded-xl p-5 space-y-4 slide-up">
              <h3 className="text-sm font-medium text-text-primary">SSH Configuration</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Host</label>
                  <input type="text" value={sshConfig.host} onChange={e => setSshConfig(p => ({ ...p, host: e.target.value }))} placeholder="192.168.1.100" className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted" />
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Port</label>
                  <input type="text" value={sshConfig.port} onChange={e => setSshConfig(p => ({ ...p, port: e.target.value }))} placeholder="22" className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted" />
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">User</label>
                  <input type="text" value={sshConfig.user} onChange={e => setSshConfig(p => ({ ...p, user: e.target.value }))} placeholder="root" className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted" />
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Auth Type</label>
                  <select value={sshConfig.auth_type} onChange={e => setSshConfig(p => ({ ...p, auth_type: e.target.value }))} className="w-full input-field px-3 py-2.5 text-sm text-text-primary" style={{ colorScheme: 'dark' }}>
                    <option value="key">SSH Key</option>
                    <option value="password">Password</option>
                  </select>
                </div>
                {sshConfig.auth_type === 'key' ? (
                  <div className="sm:col-span-2">
                    <label className="block text-xs text-text-muted mb-1.5">Key Path</label>
                    <input type="text" value={sshConfig.key_path} onChange={e => setSshConfig(p => ({ ...p, key_path: e.target.value }))} placeholder="~/.ssh/id_rsa" className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted" />
                  </div>
                ) : (
                  <div className="sm:col-span-2">
                    <label className="block text-xs text-text-muted mb-1.5">Password</label>
                    <input type="password" value={sshConfig.password} onChange={e => setSshConfig(p => ({ ...p, password: e.target.value }))} placeholder="Enter SSH password" className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted" />
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button variant="light" onPress={handleTestConnection} isDisabled={loading || !sshConfig.host} isLoading={loading}
                  className="btn-primary px-4 py-2 rounded-lg disabled:opacity-30 text-xs font-medium transition-colors flex items-center gap-2">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                  Test Connection
                </Button>
                <Button variant="light" onPress={handleSaveSsh} className="btn-ghost px-4 py-2 rounded-lg bg-bg-surface hover:bg-bg-overlay text-text-secondary text-xs transition-colors">Save Config</Button>
              </div>
              {testResult && (
                <div className={`rounded-lg p-3 text-xs fade-in ${testResult.success ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>{testResult.message}</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div className="card rounded-xl p-4">
      <div className="text-xs text-text-muted mb-1">{label}</div>
      <div className="text-xl font-semibold font-brand" style={{ color }}>{value}</div>
    </div>
  )
}
