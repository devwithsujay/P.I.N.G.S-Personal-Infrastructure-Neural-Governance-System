import React, { useState, useEffect, useCallback } from 'react'
import { Button } from '@heroui/react'
import { useToast } from '../components/Toast'
import ConfirmDialog from '../components/ConfirmDialog'
import { getAutomations, createAutomation, updateAutomation, deleteAutomation, getAutomationRuns, runAutomation } from '../api'

export default function Automations() {
  const [automations, setAutomations] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ name: '', instructions: '', schedule_time: '07:00', timezone: 'Asia/Kolkata' })
  const [runs, setRuns] = useState({})
  const [expandedId, setExpandedId] = useState(null)
  const [deleteId, setDeleteId] = useState(null)
  const toast = useToast()

  const fetchAutomations = useCallback(async () => {
    try {
      const data = await getAutomations()
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
      const data = await getAutomationRuns(id)
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
        await updateAutomation(editing.id, fd)
        toast.success('Automation updated')
      } else {
        await createAutomation(fd)
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
      await updateAutomation(id, fd)
      fetchAutomations()
    } catch (e) {
      toast.error('Failed to toggle')
    }
  }

  const handleRunNow = async (id) => {
    try {
      await runAutomation(id)
      toast.success('Briefing triggered')
      setTimeout(() => fetchRuns(id), 2000)
    } catch (e) {
      toast.error('Failed to trigger briefing')
    }
  }

  const handleDelete = async () => {
    if (!deleteId) return
    try {
      await deleteAutomation(deleteId)
      toast.success('Deleted')
      setDeleteId(null)
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
          <h1 className="text-2xl font-bold text-text-primary">Automations</h1>
          <p className="text-sm mt-1 text-text-muted">Scheduled briefings and tasks</p>
        </div>
        <Button
          onPress={() => { setEditing(null); setForm({ name: '', instructions: '', schedule_time: '07:00', timezone: 'Asia/Kolkata' }); setShowForm(true) }}
          className="btn-primary rounded-xl text-sm font-medium"
        >
          + New
        </Button>
      </div>

      {showForm && (
        <div className="card rounded-xl p-4 space-y-3">
          <h3 className="font-semibold text-text-primary">{editing ? 'Edit Automation' : 'New Automation'}</h3>
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="text"
              placeholder="Name"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              required
              className="input-field w-full"
            />
            <textarea
              placeholder="Instructions (what to research)"
              value={form.instructions}
              onChange={e => setForm(f => ({ ...f, instructions: e.target.value }))}
              required
              rows={3}
              className="input-field w-full resize-none"
            />
            <div className="flex gap-3">
              <input
                type="time"
                value={form.schedule_time}
                onChange={e => setForm(f => ({ ...f, schedule_time: e.target.value }))}
                required
                className="input-field"
              />
              <select
                value={form.timezone}
                onChange={e => setForm(f => ({ ...f, timezone: e.target.value }))}
                className="input-field flex-1"
              >
                <option value="UTC">UTC</option>
                <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                <option value="America/New_York">America/New_York (EST)</option>
                <option value="Europe/London">Europe/London (GMT)</option>
                <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
              </select>
            </div>
            <div className="flex gap-2">
              <Button type="submit" className="btn-primary rounded-xl text-sm">
                {editing ? 'Update' : 'Create'}
              </Button>
              <Button type="button" onPress={() => { setShowForm(false); setEditing(null) }} className="btn-ghost rounded-xl text-sm">
                Cancel
              </Button>
            </div>
          </form>
        </div>
      )}

      {automations.length === 0 && (
        <div className="text-center py-12 text-text-muted">
          <p>No automations yet. Create one to schedule research briefings.</p>
        </div>
      )}

      <div className="space-y-3">
        {automations.map(a => (
          <div key={a.id} className="card rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold truncate text-text-primary">{a.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${a.active ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400'}`}>
                    {a.active ? 'Active' : 'Paused'}
                  </span>
                </div>
                <p className="text-sm mt-1 truncate text-text-muted">{a.instructions}</p>
                <p className="text-xs mt-1 text-text-muted">
                  {a.schedule_time} {a.timezone}
                </p>
              </div>
              <div className="flex items-center gap-2 ml-4">
                <Button size="sm" onPress={() => toggleExpand(a.id)} className="btn-ghost rounded-lg text-xs">
                  Runs
                </Button>
                <Button size="sm" onPress={() => handleRunNow(a.id)} className="rounded-lg text-xs bg-green-500/15 text-green-400">
                  Run Now
                </Button>
                <Button size="sm" onPress={() => handleToggle(a.id, a.active)} className="btn-ghost rounded-lg text-xs">
                  {a.active ? 'Pause' : 'Resume'}
                </Button>
                <Button size="sm" onPress={() => handleEdit(a)} className="btn-ghost rounded-lg text-xs">
                  Edit
                </Button>
                <Button size="sm" onPress={() => setDeleteId(a.id)} className="rounded-lg text-xs bg-red-500/10 text-red-400">
                  Delete
                </Button>
              </div>
            </div>

            {expandedId === a.id && runs[a.id] && (
              <div className="mt-3 pt-3 space-y-2 border-t border-border-subtle">
                <h4 className="text-xs font-semibold uppercase text-text-muted">Run History</h4>
                {runs[a.id].length === 0 && (
                  <p className="text-xs text-text-muted">No runs yet</p>
                )}
                {runs[a.id].map(r => (
                  <div key={r.id} className="flex items-center justify-between text-xs py-1">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${r.status === 'success' ? 'bg-green-400' : r.status === 'failed' ? 'bg-red-400' : r.status === 'running' ? 'bg-yellow-400' : 'bg-gray-400'}`} />
                      <span className="text-text-secondary">{r.status}</span>
                      <span className="text-text-muted">{r.started_at ? new Date(r.started_at).toLocaleString() : '-'}</span>
                    </div>
                    {r.pdf_path && (
                      <a
                        href={`/api/automations/${a.id}/runs/${r.id}/pdf`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs underline text-accent"
                      >
                        View PDF
                      </a>
                    )}
                    {r.error_message && (
                      <span className="text-xs truncate max-w-[200px] text-red-400">{r.error_message}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title="Delete Automation"
        message="Are you sure you want to delete this automation? This cannot be undone."
        confirmLabel="Delete"
        variant="danger"
      />
    </div>
  )
}
