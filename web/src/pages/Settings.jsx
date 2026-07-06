import React, { useState, useEffect, useCallback } from 'react'
import { Button, Spinner } from '@heroui/react'
import { getSettings, saveSettings, getAgents, createAgent, updateAgent, deleteAgent, getPersonality, savePersonality, getModels, testModels } from '../api'
import { useToast } from '../components/Toast'
import ConfirmDialog from '../components/ConfirmDialog'
import ThemeSwitcher from '../components/ThemeSwitcher'

export default function Settings() {
  const [settings, setSettings] = useState(null)
  const [agents, setAgents] = useState([])
  const [personality, setPersonality] = useState('')
  const [models, setModels] = useState([])
  const [activeTab, setActiveTab] = useState('general')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [testing, setTesting] = useState(false)
  const [deleteAgentId, setDeleteAgentId] = useState(null)
  const toast = useToast()

  const [showAgentForm, setShowAgentForm] = useState(false)
  const [agentForm, setAgentForm] = useState({ name: '', description: '', system_prompt: '' })
  const [editingAgentId, setEditingAgentId] = useState(null)

  const loadData = useCallback(async () => {
    try {
      const [s, a, p, m] = await Promise.all([
        getSettings().catch(() => ({})),
        getAgents().catch(() => []),
        getPersonality().catch(() => ({})),
        getModels().catch(() => ({}))
      ])
      setSettings(s)
      setAgents(Array.isArray(a) ? a : a?.agents || [])
      setPersonality(p?.personality || p?.content || '')
      const modelList = m?.models || m?.available || []
      setModels(Array.isArray(modelList) ? modelList : [])
    } catch {} finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  const handleSaveSettings = async () => {
    setSaving(true)
    try {
      await saveSettings(settings)
      toast.success('Settings saved')
    } catch { toast.error('Failed to save settings') } finally {
      setSaving(false)
    }
  }

  const handleSavePersonality = async () => {
    setSaving(true)
    try {
      await savePersonality({ personality })
      toast.success('Persona saved')
    } catch { toast.error('Failed to save persona') } finally {
      setSaving(false)
    }
  }

  const handleTestModels = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await testModels()
      setTestResult({ success: true, data: res })
      toast.success('Model connection successful')
    } catch (err) {
      setTestResult({ success: false, error: err.message })
      toast.error('Model connection failed')
    } finally {
      setTesting(false)
    }
  }

  const handleCreateAgent = async () => {
    if (!agentForm.name.trim()) return
    try {
      if (editingAgentId) {
        await updateAgent(editingAgentId, agentForm)
      } else {
        await createAgent(agentForm)
      }
      setAgentForm({ name: '', description: '', system_prompt: '' })
      setEditingAgentId(null)
      setShowAgentForm(false)
      await loadData()
      toast.success(editingAgentId ? 'Agent updated' : 'Agent created')
    } catch { toast.error('Failed to save agent') }
  }

  const handleDeleteAgent = async (id) => {
    try {
      await deleteAgent(id)
      await loadData()
      setDeleteAgentId(null)
      toast.success('Agent deleted')
    } catch { toast.error('Failed to delete agent') }
  }

  const startEditAgent = (agent) => {
    setEditingAgentId(agent.id)
    setAgentForm({ name: agent.name || '', description: agent.description || '', system_prompt: agent.system_prompt || '' })
    setShowAgentForm(true)
  }

  const updateSettingsField = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner size="sm" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 glass-strong border-b flex items-center gap-2" style={{ borderColor: 'var(--border-subtle)' }}>
        <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span className="font-brand text-sm font-medium text-text-primary">Settings</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="flex gap-2 overflow-x-auto pb-1">
            {['general', 'theme', 'agents', 'personality', 'models'].map(tab => (
              <Button
                key={tab}
                variant="light"
                onPress={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all capitalize ${
                  activeTab === tab ? 'btn-primary' : 'bg-bg-surface text-text-muted hover:text-text-secondary'
                }`}
              >
                {tab}
              </Button>
            ))}
          </div>

          {activeTab === 'theme' && (
            <div className="space-y-4 slide-up">
              <div className="card rounded-xl p-5">
                <h3 className="text-sm font-medium text-text-primary mb-1">Theme</h3>
                <p className="text-xs text-text-muted mb-4">Choose a color theme for the dashboard. Changes apply instantly.</p>
                <ThemeSwitcher />
              </div>
            </div>
          )}

          {activeTab === 'general' && (
            <div className="space-y-4 slide-up">
              <div className="card rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-medium text-text-primary">Configuration</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-text-muted mb-1.5">Default Model</label>
                    <select
                      value={settings?.default_model || ''}
                      onChange={e => updateSettingsField('default_model', e.target.value)}
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary"
                      style={{ colorScheme: 'dark' }}
                    >
                      <option value="" className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>System Default</option>
                      {models.map(m => (
                        <option key={m.id || m} value={m.id || m} className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>
                          {m.name || m.id || m}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-text-muted mb-1.5">Temperature</label>
                    <input
                      type="number"
                      min="0"
                      max="2"
                      step="0.1"
                      value={settings?.temperature || 0.7}
                      onChange={e => updateSettingsField('temperature', parseFloat(e.target.value))}
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-text-muted mb-1.5">Max Tokens</label>
                    <input
                      type="number"
                      min="256"
                      max="32768"
                      step="256"
                      value={settings?.max_tokens || 4096}
                      onChange={e => updateSettingsField('max_tokens', parseInt(e.target.value))}
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-text-muted mb-1.5">System Prompt</label>
                    <input
                      type="text"
                      value={settings?.system_prompt || ''}
                      onChange={e => updateSettingsField('system_prompt', e.target.value)}
                      placeholder="Default system prompt"
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings?.memory_enabled ?? true}
                      onChange={e => updateSettingsField('memory_enabled', e.target.checked)}
                      className="w-4 h-4 rounded bg-bg-surface border-text-muted text-accent focus:ring-accent"
                    />
                    Memory System
                  </label>
                </div>
                <Button
                  variant="light"
                  onPress={handleSaveSettings}
                  isDisabled={saving}
                  className="btn-primary px-4 py-2 rounded-lg disabled:opacity-30 text-sm font-medium transition-colors"
                >
                  {saving ? 'Saving...' : 'Save Settings'}
                </Button>
              </div>
            </div>
          )}

          {activeTab === 'agents' && (
            <div className="space-y-4 slide-up">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-text-primary">Agents</h3>
                <Button
                  variant="light"
                  onPress={() => { setAgentForm({ name: '', description: '', system_prompt: '' }); setEditingAgentId(null); setShowAgentForm(!showAgentForm) }}
                  className="btn-primary flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  New Agent
                </Button>
              </div>

              {showAgentForm && (
                <div className="card rounded-xl p-5 slide-up">
                  <h4 className="text-sm font-medium text-text-primary mb-3">{editingAgentId ? 'Edit Agent' : 'New Agent'}</h4>
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={agentForm.name}
                      onChange={e => setAgentForm(p => ({ ...p, name: e.target.value }))}
                      placeholder="Agent name"
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted"
                    />
                    <input
                      type="text"
                      value={agentForm.description}
                      onChange={e => setAgentForm(p => ({ ...p, description: e.target.value }))}
                      placeholder="Description"
                      className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted"
                    />
                    <textarea
                      value={agentForm.system_prompt}
                      onChange={e => setAgentForm(p => ({ ...p, system_prompt: e.target.value }))}
                      placeholder="System prompt..."
                      rows={4}
                      className="w-full input-field px-3 py-3 text-sm text-text-primary placeholder-text-muted resize-none"
                    />
                    <div className="flex justify-end gap-2">
                      <Button variant="light" onPress={() => setShowAgentForm(false)} className="px-3 py-1.5 text-xs text-text-muted hover:text-text-secondary btn-ghost">Cancel</Button>
                      <Button
                        variant="light"
                        onPress={handleCreateAgent}
                        isDisabled={!agentForm.name.trim()}
                        className="btn-primary px-4 py-1.5 rounded-lg disabled:opacity-30 text-xs font-medium transition-colors"
                      >
                        {editingAgentId ? 'Update' : 'Create'}
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {agents.length === 0 ? (
                <div className="card rounded-xl p-6 text-center text-text-muted text-sm">No agents configured</div>
              ) : (
                <div className="space-y-2">
                  {agents.map(agent => (
                    <div key={agent.id || agent.name} className="card rounded-lg p-4 group slide-up">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-text-primary">{agent.name || agent.id}</div>
                          {agent.description && <p className="text-xs text-text-secondary mt-1">{agent.description}</p>}
                          {agent.system_prompt && (
                            <p className="text-xs text-text-muted mt-1.5 line-clamp-2 font-mono">{agent.system_prompt}</p>
                          )}
                        </div>
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button isIconOnly aria-label="Edit agent" variant="light" onPress={() => startEditAgent(agent)} className="p-1.5 rounded hover:bg-bg-surface text-text-muted hover:text-text-secondary">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </Button>
                          <Button isIconOnly aria-label="Delete agent" variant="light" onPress={() => setDeleteAgentId(agent.id)} className="p-1.5 rounded hover:bg-bg-surface text-text-muted hover:text-red-400">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'personality' && (
            <div className="card rounded-xl p-5 slide-up">
              <h3 className="text-sm font-medium text-text-primary mb-3">Personality</h3>
              <textarea
                value={personality}
                onChange={e => setPersonality(e.target.value)}
                placeholder="Define the personality and tone of your P.I.N.G.S instance..."
                rows={10}
                className="w-full input-field px-4 py-3 text-sm text-text-primary placeholder-text-muted resize-none mb-3"
              />
              <Button
                variant="light"
                onPress={handleSavePersonality}
                isDisabled={saving}
                className="btn-primary px-4 py-2 rounded-lg disabled:opacity-30 text-sm font-medium transition-colors"
              >
                {saving ? 'Saving...' : 'Save Personality'}
              </Button>
            </div>
          )}

          {activeTab === 'models' && (
            <div className="space-y-4 slide-up">
              <div className="card rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium text-text-primary">Model Discovery</h3>
                  <Button
                    variant="light"
                    onPress={handleTestModels}
                    isDisabled={testing}
                    className="btn-primary px-4 py-2 rounded-lg disabled:opacity-30 text-xs font-medium transition-colors flex items-center gap-2"
                  >
                    {testing ? (
                      <Spinner size="sm" />
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    )}
                    Test Models
                  </Button>
                </div>

                {testResult && (
                  <div className={`rounded-lg p-3 text-xs fade-in ${testResult.success ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                    {testResult.success ? 'Models discovered successfully' : testResult.error}
                  </div>
                )}

                {models.length === 0 ? (
                  <div className="text-center py-8 text-text-muted text-xs">No models available</div>
                ) : (
                  <div className="space-y-2">
                    {models.map(m => (
                      <div key={m.id || m} className="flex items-center justify-between py-2 border-b last:border-0" style={{ borderColor: 'var(--border-subtle)' }}>
                        <div>
                          <div className="text-sm text-text-primary">{m.name || m.id || m}</div>
                          {m.provider && <div className="text-xs text-text-muted">{m.provider}</div>}
                        </div>
                        <span className={`w-2 h-2 rounded-full ${m.available !== false ? 'bg-green-500' : 'bg-red-500'}`} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={!!deleteAgentId}
        title="Delete Agent"
        message="This agent will be permanently removed. This action cannot be undone."
        confirmLabel="Delete"
        danger
        onConfirm={() => handleDeleteAgent(deleteAgentId)}
        onCancel={() => setDeleteAgentId(null)}
      />
    </div>
  )
}
