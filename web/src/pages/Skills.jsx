import React, { useState, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { getSkills, getSkill, createSkill, updateSkill, deleteSkill } from '../api'
import { useToast } from '../components/Toast'
import ConfirmDialog from '../components/ConfirmDialog'
import { Button, Spinner } from '@heroui/react'

export default function Skills() {
  const [skills, setSkills] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState({ name: '', description: '', content: '' })
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState(false)
  const [deleteId, setDeleteId] = useState(null)
  const toast = useToast()

  const loadSkills = useCallback(async () => {
    try {
      const res = await getSkills()
      setSkills(Array.isArray(res) ? res : res?.skills || [])
    } catch {}
  }, [])

  useEffect(() => { loadSkills() }, [loadSkills])

  const resetForm = () => {
    setForm({ name: '', description: '', content: '' })
    setEditingId(null)
    setShowForm(false)
    setPreview(false)
  }

  const handleSubmit = async () => {
    if (!form.name.trim()) return
    setLoading(true)
    try {
      const payload = { name: form.name.trim(), description: form.description.trim(), content: form.content }
      if (editingId) {
        await updateSkill(editingId, payload)
      } else {
        await createSkill(payload)
      }
      resetForm()
      await loadSkills()
      toast.success(editingId ? 'Skill updated' : 'Skill created')
    } catch { toast.error('Failed to save skill') } finally {
      setLoading(false)
    }
  }

  const startEdit = async (skill) => {
    try {
      const detail = await getSkill(skill.id)
      setEditingId(skill.id)
      setForm({
        name: detail.name || skill.name || '',
        description: detail.description || skill.description || '',
        content: detail.content || ''
      })
      setShowForm(true)
    } catch {
      setEditingId(skill.id)
      setForm({ name: skill.name || '', description: skill.description || '', content: '' })
      setShowForm(true)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteSkill(id)
      if (editingId === id) resetForm()
      setDeleteId(null)
      await loadSkills()
      toast.success('Skill deleted')
    } catch { toast.error('Failed to delete skill') }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 glass-strong border-b flex items-center justify-between" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span className="font-brand text-sm font-medium text-text-primary">Skills</span>
        </div>
        <Button
          variant="light"
          onPress={() => { resetForm(); setShowForm(!showForm) }}
          className="btn-primary flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
          startContent={<svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>}
        >
          New Skill
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {showForm && (
            <div className="card rounded-xl p-5 slide-up">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-text-primary">{editingId ? 'Edit Skill' : 'New Skill'}</h3>
                <Button
                  onPress={() => setPreview(!preview)}
                  className="text-xs text-text-muted hover:text-text-secondary transition-colors flex items-center gap-1 bg-transparent"
                >
                  {preview ? (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Edit
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      Preview
                    </>
                  )}
                </Button>
              </div>

              <div className="space-y-3">
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                  placeholder="Skill name"
                  className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted"
                />
                <input
                  type="text"
                  value={form.description}
                  onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                  placeholder="Short description"
                  className="w-full input-field px-3 py-2.5 text-sm text-text-primary placeholder-text-muted"
                />
                {preview ? (
                  <div className="chat-bubble-agent rounded-lg p-4 min-h-[200px] text-sm">
                    <ReactMarkdown>{form.content}</ReactMarkdown>
                  </div>
                ) : (
                  <textarea
                    value={form.content}
                    onChange={e => setForm(p => ({ ...p, content: e.target.value }))}
                    placeholder="# Skill Content&#10;&#10;Write your skill definition in Markdown..."
                    rows={12}
                    className="w-full input-field px-3 py-3 text-sm text-text-primary placeholder-text-muted resize-none font-mono"
                  />
                )}
              </div>

              <div className="flex justify-end gap-2 mt-3">
                <Button variant="light" onPress={resetForm} className="px-3 py-1.5 rounded-lg text-xs text-text-muted hover:text-text-secondary btn-ghost transition-colors bg-transparent">Cancel</Button>
                <Button
                  variant="light"
                  onPress={handleSubmit}
                  isDisabled={!form.name.trim() || loading}
                  className="btn-primary px-4 py-1.5 rounded-lg disabled:opacity-30 text-xs font-medium transition-colors"
                >
                  {editingId ? 'Update' : 'Create'}
                </Button>
              </div>
            </div>
          )}

          {skills.length === 0 ? (
            <div className="text-center py-16 text-text-muted text-sm">
              No skills defined
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {skills.map(skill => (
                <div key={skill.id} className="card rounded-xl p-4 group hover:bg-bg-surface/30 transition-colors slide-up">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <svg className="w-4 h-4 text-accent flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span className="text-sm font-medium text-text-primary truncate">{skill.name}</span>
                      </div>
                      {skill.description && (
                        <p className="text-xs text-text-secondary mt-1 line-clamp-2">{skill.description}</p>
                      )}
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
                      <Button isIconOnly variant="light" onPress={() => startEdit(skill)} aria-label="Edit skill" className="p-1.5 rounded hover:bg-bg-surface text-text-muted hover:text-text-secondary transition-colors">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </Button>
                      <Button isIconOnly variant="light" onPress={() => setDeleteId(skill.id)} aria-label="Delete skill" className="p-1.5 rounded hover:bg-bg-surface text-text-muted hover:text-red-400 transition-colors">
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
      </div>
      <ConfirmDialog
        open={!!deleteId}
        title="Delete Skill"
        message="This skill will be permanently removed."
        confirmLabel="Delete"
        danger
        onConfirm={() => handleDelete(deleteId)}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  )
}
