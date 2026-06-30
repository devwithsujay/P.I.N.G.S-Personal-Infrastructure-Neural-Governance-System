import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { useToast } from '../components/Toast'

export default function HomeLab() {
  const [status, setStatus] = useState(null)
  const [containers, setContainers] = useState([])
  const [system, setSystem] = useState(null)
  const [sshConfig, setSshConfig] = useState({ host: '', port: '22', user: '', auth_type: 'key', key_path: '', password: '' })
  const [testResult, setTestResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('containers')
  const toast = useToast()

  const loadStatus = useCallback(async () => {
    try {
      const res = await axios.get('/api/homelab/status')
      setStatus(res.data)
      setContainers(res.data?.containers || [])
      setSystem(res.data?.system || null)
      if (res.data?.ssh_config) {
        setSshConfig(res.data.ssh_config)
      }
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
      const res = await axios.post('/api/homelab/ssh/test', sshConfig)
      setTestResult({ success: true, message: res.data?.message || 'Connected successfully' })
      toast.success('SSH connection successful')
    } catch (err) {
      setTestResult({ success: false, message: err.response?.data?.detail || err.message })
      toast.error('SSH connection failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSsh = async () => {
    try {
      await axios.put('/api/homelab/ssh', sshConfig)
      toast.success('SSH config saved')
    } catch { toast.error('Failed to save SSH config') }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 glass-strong border-b flex items-center gap-2" style={{ borderColor: 'var(--border-subtle)' }}>
        <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
        </svg>
        <span className="font-brand text-sm font-medium text-text-primary">HomeLab</span>
        <div className="ml-auto flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${status?.host_reachable || status?.connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-text-muted">{status?.host_reachable || status?.connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-4xl mx-auto space-y-6">
          {system && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 slide-up">
              <StatCard label="CPU" value={`${system.cpu_percent || 0}%`} color="#6c5ce7" />
              <StatCard label="Memory" value={`${system.memory_percent || 0}%`} color="#00cec9" />
              <StatCard label="Disk" value={`${system.disk_percent || 0}%`} color="#fdcb6e" />
              <StatCard label="Uptime" value={system.uptime || 'N/A'} color="#e17055" />
            </div>
          )}

          <div className="flex gap-2 overflow-x-auto pb-1">
            {['containers', 'ssh'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all capitalize ${
                  activeTab === tab ? 'btn-primary' : 'bg-bg-surface text-text-muted hover:text-text-secondary'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {activeTab === 'containers' && (
            <div className="slide-up">
              {containers.length === 0 ? (
                <div className="text-center py-12 text-text-muted text-sm card rounded-xl">
                  No containers detected
                </div>
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
                        </tr>
                      </thead>
                      <tbody>
                        {containers.map((c, i) => (
                          <tr key={c.id || i} className="border-b hover:bg-bg-surface/30 transition-colors" style={{ borderColor: 'var(--border-subtle)' }}>
                            <td className="px-4 py-3 text-text-primary font-medium">{c.name || c.Names}</td>
                            <td className="px-4 py-3 text-text-secondary text-xs font-mono">{c.image || c.Image}</td>
                            <td className="px-4 py-3">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                (c.status || c.state || c.Status || '').toLowerCase().includes('up') || (c.status || '').toLowerCase() === 'running'
                                  ? 'bg-green-500/20 text-green-400'
                                  : 'bg-red-500/20 text-red-400'
                              }`}>
                                {c.status || c.state || c.Status || 'unknown'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-text-muted text-xs font-mono">{c.ports || c.Ports || '-'}</td>
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
                    <input
                      type="text"
                      value={sshConfig.host}
                      onChange={e => setSshConfig(p => ({ ...p, host: e.target.value }))}
                      placeholder="192.168.1.100"
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted"
                    />
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Port</label>
                    <input
                      type="text"
                      value={sshConfig.port}
                      onChange={e => setSshConfig(p => ({ ...p, port: e.target.value }))}
                      placeholder="22"
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted"
                    />
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">User</label>
                    <input
                      type="text"
                      value={sshConfig.user}
                      onChange={e => setSshConfig(p => ({ ...p, user: e.target.value }))}
                      placeholder="root"
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted"
                    />
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Auth Type</label>
                  <select
                    value={sshConfig.auth_type}
                    onChange={e => setSshConfig(p => ({ ...p, auth_type: e.target.value }))}
                    className="w-full input-field px-3 py-2.5 text-sm text-text-primary"
                    style={{ colorScheme: 'dark' }}
                  >
                    <option value="key">SSH Key</option>
                    <option value="password">Password</option>
                  </select>
                </div>
                {sshConfig.auth_type === 'key' ? (
                  <div className="sm:col-span-2">
                    <label className="block text-xs text-text-muted mb-1.5">Key Path</label>
                    <input
                      type="text"
                      value={sshConfig.key_path}
                      onChange={e => setSshConfig(p => ({ ...p, key_path: e.target.value }))}
                      placeholder="~/.ssh/id_rsa"
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted"
                    />
                  </div>
                ) : (
                  <div className="sm:col-span-2">
                    <label className="block text-xs text-text-muted mb-1.5">Password</label>
                    <input
                      type="password"
                      value={sshConfig.password}
                      onChange={e => setSshConfig(p => ({ ...p, password: e.target.value }))}
                      placeholder="Enter SSH password"
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted"
                    />
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleTestConnection}
                  disabled={loading || !sshConfig.host}
                  className="btn-primary px-4 py-2 rounded-lg disabled:opacity-30 text-xs font-medium transition-colors flex items-center gap-2"
                >
                  {loading ? (
                    <span className="w-3 h-3 border-2 border-accent/50 border-t-accent rounded-full animate-spin" />
                  ) : (
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  )}
                  Test Connection
                </button>
                <button
                  onClick={handleSaveSsh}
                  className="btn-ghost px-4 py-2 rounded-lg bg-bg-surface hover:bg-bg-overlay text-text-secondary text-xs transition-colors"
                >
                  Save Config
                </button>
              </div>

              {testResult && (
                <div className={`rounded-lg p-3 text-xs fade-in ${
                  testResult.success ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                }`}>
                  {testResult.message}
                </div>
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
