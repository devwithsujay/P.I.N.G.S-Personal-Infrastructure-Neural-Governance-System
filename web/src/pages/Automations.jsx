import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { Button } from '@heroui/react'
import { useToast } from '../components/Toast'

const CORE_API = import.meta.env.VITE_CORE_URL || '/api'

export default function Automations() {
  const [automations, setAutomations] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ name: '', instructions: '', schedule_time: '07:00', timezone: 'Asia/Kolkata' })
  const [runs, setRuns] = useState({})
  const [expandedId, setExpandedId] = useState(null)
  const toast = useToast()

  const fetchAutomations = useCallback(async () => {
    try {
      const { data } = await axios.get(`${CORE_API}/automations`)
      setAutomations(data)
    } catch (e) {
      toast.error('Failed to load automations')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchAutomations() }, [fetchAutomations])

  const fetchRuns = async (id) => {
    try {
      const { data } = await axios.get(`${CORE_API}/automations/${id}/runs`)
      setRuns(prev => ({ ...prev, [id]: data }))
    } catch (e) {
      toast.error('Failed to load runs')
    }
  }

  const toggleExpand = (id) => {
    if (expandedId === id) {
      setExpandedId(null)
    } else {
      setExpandedId(id)
      fetchRuns(id)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const fd = new FormData()
      fd.append('name', form.name)
      fd.append('instructions', form.instructions)
      fd.append('schedule_time', form.schedule_time)
      fd.append('timezone', form.timezone)

      if (editing) {
        await axios.patch(`${CORE_API}/automations/${editing.id}`, fd)
        toast.success('Automation updated')
      } else {
        await axios.post(`${CORE_API}/automations`, fd)
        toast.success('Automation created')
      }
      setShowForm(false)
      setEditing(null)
      setForm({ name: '', instructions: '', schedule_time: '07:00', timezone: 'Asia/Kolkata' })
      fetchAutomations()
    } catch (e) {
      toast.error('Failed to save automation')
    }
  }

  const handleToggle = async (id, active) => {
    try {
      const fd = new FormData()
      fd.append('active', active ? '0' : '1')
      await axios.patch(`${CORE_API}/automations/${id}`, fd)
      fetchAutomations()
    } catch (e) {
      toast.error('Failed to toggle')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this automation?')) return
    try {
      await axios.delete(`${CORE_API}/automations/${id}`)
      toast.success('Deleted')
      fetchAutomations()
    } catch (e) {
      toast.error('Failed to delete')
    }
  }

  const handleEdit = (a) => {
    setEditing(a)
    setForm({ name: a.name, instructions: a.instructions, schedule_time: a.schedule_time, timezone: a.timezone })
    setShowForm(true)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="text-text-muted">Loading automations...</span>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Automations</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Scheduled briefings and tasks</p>
        </div>
        <Button
          onPress={() => { setEditing(null); setForm({ name: '', instructions: '', schedule_time: '07:00', timezone: 'Asia/Kolkata' }); setShowForm(true) }}
          className="rounded-xl text-sm font-medium"
          style={{ color: 'var(--accent-text)', background: 'var(--accent)' }}
        >
          + New
        </Button>
      </div>

      {showForm && (
        <div className="rounded-xl p-4 space-y-3" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
          <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>{editing ? 'Edit Automation' : 'New Automation'}</h3>
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="text"
              placeholder="Name"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              required
              className="w-full px-3 py-2 rounded-lg text-sm"
              style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: '1px solid var(--border-subtle)' }}
            />
            <textarea
              placeholder="Instructions (what to research)"
              value={form.instructions}
              onChange={e => setForm(f => ({ ...f, instructions: e.target.value }))}
              required
              rows={3}
              className="w-full px-3 py-2 rounded-lg text-sm resize-none"
              style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: '1px solid var(--border-subtle)' }}
            />
            <div className="flex gap-3">
              <input
                type="time"
                value={form.schedule_time}
                onChange={e => setForm(f => ({ ...f, schedule_time: e.target.value }))}
                required
                className="px-3 py-2 rounded-lg text-sm"
                style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: '1px solid var(--border-subtle)' }}
              />
              <select
                value={form.timezone}
                onChange={e => setForm(f => ({ ...f, timezone: e.target.value }))}
                className="px-3 py-2 rounded-lg text-sm flex-1"
                style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: '1px solid var(--border-subtle)' }}
              >
                <option value="UTC">UTC</option>
                <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                <option value="America/New_York">America/New_York (EST)</option>
                <option value="Europe/London">Europe/London (GMT)</option>
                <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
              </select>
            </div>
            <div className="flex gap-2">
              <Button type="submit" className="rounded-xl text-sm" style={{ background: 'var(--accent)', color: 'var(--accent-text)' }}>
                {editing ? 'Update' : 'Create'}
              </Button>
              <Button type="button" onPress={() => { setShowForm(false); setEditing(null) }} className="rounded-xl text-sm" style={{ background: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
                Cancel
              </Button>
            </div>
          </form>
        </div>
      )}

      {automations.length === 0 && (
        <div className="text-center py-12" style={{ color: 'var(--text-muted)' }}>
          <p>No automations yet. Create one to schedule research briefings.</p>
        </div>
      )}

      <div className="space-y-3">
        {automations.map(a => (
          <div key={a.id} className="rounded-xl p-4" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold truncate" style={{ color: 'var(--text-primary)' }}>{a.name}</h3>
                  <span className="text-xs px-2 py-0.5 rounded-full" style={{
                    background: a.active ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                    color: a.active ? '#22c55e' : '#ef4444'
                  }}>
                    {a.active ? 'Active' : 'Paused'}
                  </span>
                </div>
                <p className="text-sm mt-1 truncate" style={{ color: 'var(--text-muted)' }}>{a.instructions}</p>
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                  {a.schedule_time} {a.timezone}
                </p>
              </div>
              <div className="flex items-center gap-2 ml-4">
                <Button size="sm" onPress={() => toggleExpand(a.id)} className="rounded-lg text-xs" style={{ background: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
                  Runs
                </Button>
                <Button size="sm" onPress={() => handleToggle(a.id, a.active)} className="rounded-lg text-xs" style={{ background: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
                  {a.active ? 'Pause' : 'Resume'}
                </Button>
                <Button size="sm" onPress={() => handleEdit(a)} className="rounded-lg text-xs" style={{ background: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
                  Edit
                </Button>
                <Button size="sm" onPress={() => handleDelete(a.id)} className="rounded-lg text-xs" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
                  Delete
                </Button>
              </div>
            </div>

            {expandedId === a.id && runs[a.id] && (
              <div className="mt-3 pt-3 space-y-2" style={{ borderTop: '1px solid var(--border-subtle)' }}>
                <h4 className="text-xs font-semibold uppercase" style={{ color: 'var(--text-muted)' }}>Run History</h4>
                {runs[a.id].length === 0 && (
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No runs yet</p>
                )}
                {runs[a.id].map(r => (
                  <div key={r.id} className="flex items-center justify-between text-xs py-1">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full" style={{
                        background: r.status === 'success' ? '#22c55e' : r.status === 'failed' ? '#ef4444' : r.status === 'running' ? '#f59e0b' : '#6b7280'
                      }} />
                      <span style={{ color: 'var(--text-secondary)' }}>{r.status}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{r.started_at ? new Date(r.started_at).toLocaleString() : '-'}</span>
                    </div>
                    {r.pdf_path && (
                      <a
                        href={`${CORE_API}/automations/${a.id}/runs/${r.id}/pdf`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs underline"
                        style={{ color: 'var(--accent)' }}
                      >
                        View PDF
                      </a>
                    )}
                    {r.error_message && (
                      <span className="text-xs truncate max-w-[200px]" style={{ color: '#ef4444' }}>{r.error_message}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
