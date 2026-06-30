import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { getScheduledTasks, createScheduledTask, updateScheduledTask, deleteScheduledTask } from '../api'
import { useToast } from '../components/Toast'
import ConfirmDialog from '../components/ConfirmDialog'

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
const PRIORITY_COLORS = {
  urgent: 'bg-red-500/20 text-red-400 border border-red-500/20',
  high: 'bg-orange-500/15 text-orange-400 border border-orange-500/15',
  medium: 'bg-accent/10 text-accent-light border border-accent/15',
  low: 'bg-blue-500/10 text-blue-400 border border-blue-500/10',
}

function getDaysInMonth(year, month) { return new Date(year, month + 1, 0).getDate() }
function getFirstDayOfMonth(year, month) { return new Date(year, month, 1).getDay() }
function toDateStr(y, m, d) { return `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}` }

export default function Calendar() {
  const [tasks, setTasks] = useState([])
  const [today] = useState(new Date())
  const [viewYear, setViewYear] = useState(today.getFullYear())
  const [viewMonth, setViewMonth] = useState(today.getMonth())
  const [selectedDate, setSelectedDate] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [form, setForm] = useState({ title: '', description: '', due_time: '', priority: 'medium' })
  const [loading, setLoading] = useState(false)
  const [deleteTaskId, setDeleteTaskId] = useState(null)
  const toast = useToast()

  const loadTasks = useCallback(async () => {
    try { const res = await getScheduledTasks(); setTasks(Array.isArray(res) ? res : res?.tasks || res?.scheduled || []) } catch {}
  }, [])

  useEffect(() => { loadTasks() }, [loadTasks])

  const tasksByDate = useMemo(() => {
    const map = {}
    tasks.forEach(t => { if (t.due_date) { if (!map[t.due_date]) map[t.due_date] = []; map[t.due_date].push(t) } })
    Object.keys(map).forEach(date => { map[date].sort((a, b) => (a.due_time || '').localeCompare(b.due_time || '')) })
    return map
  }, [tasks])

  const daysInMonth = getDaysInMonth(viewYear, viewMonth)
  const firstDay = getFirstDayOfMonth(viewYear, viewMonth)
  const todayStr = toDateStr(today.getFullYear(), today.getMonth(), today.getDate())
  const selectedTasks = selectedDate ? (tasksByDate[selectedDate] || []) : []

  const prevMonth = () => { if (viewMonth === 0) { setViewMonth(11); setViewYear(y => y - 1) } else setViewMonth(m => m - 1) }
  const nextMonth = () => { if (viewMonth === 11) { setViewMonth(0); setViewYear(y => y + 1) } else setViewMonth(m => m + 1) }

  const resetForm = () => { setForm({ title: '', description: '', due_time: '', priority: 'medium' }); setEditingTask(null); setShowForm(false) }
  const openAddForDate = (dateStr) => { setSelectedDate(dateStr); setEditingTask(null); setForm({ title: '', description: '', due_time: '', priority: 'medium' }); setShowForm(true) }
  const startEdit = (task) => { setEditingTask(task); setForm({ title: task.title || '', description: task.description || '', due_time: task.due_time || '', priority: task.priority || 'medium' }); setShowForm(true) }

  const handleSubmit = async () => {
    if (!form.title.trim() || !selectedDate) return
    setLoading(true)
    try {
      const payload = { title: form.title.trim(), description: form.description.trim(), due_date: selectedDate, due_time: form.due_time || null, recurrence: editingTask?.recurrence || 'none', priority: form.priority }
      if (editingTask) await updateScheduledTask(editingTask.id, payload); else await createScheduledTask(payload)
      resetForm(); await loadTasks(); toast.success(editingTask ? 'Task updated' : 'Task created')
    } catch { toast.error('Failed to save task') } finally { setLoading(false) }
  }

  const handleDelete = async (id) => {
    try { await deleteScheduledTask(id); await loadTasks(); setDeleteTaskId(null); toast.success('Task deleted') } catch { toast.error('Failed to delete task') }
  }

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit() }; if (e.key === 'Escape') resetForm() }

  const calendarCells = useMemo(() => {
    const cells = []
    for (let i = 0; i < firstDay; i++) cells.push({ key: `empty-${i}`, empty: true })
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = toDateStr(viewYear, viewMonth, d)
      cells.push({ key: dateStr, day: d, dateStr, isToday: dateStr === todayStr, tasks: tasksByDate[dateStr] || [] })
    }
    return cells
  }, [firstDay, daysInMonth, viewYear, viewMonth, tasksByDate, todayStr])

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col min-w-0">
        <div className="px-4 py-3 glass-strong border-b flex items-center justify-between" style={{ borderColor: 'var(--border-subtle)' }}>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))' }}>
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <span className="font-brand text-sm font-medium text-text-primary">Calendar</span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={prevMonth} className="p-1.5 rounded-xl hover:bg-bg-surface text-text-muted hover:text-text-primary transition-all" aria-label="Previous month">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
            </button>
            <span className="text-sm font-medium text-text-primary w-36 text-center">{MONTHS[viewMonth]} {viewYear}</span>
            <button onClick={nextMonth} className="p-1.5 rounded-xl hover:bg-bg-surface text-text-muted hover:text-text-primary transition-all" aria-label="Next month">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
            </button>
            <button onClick={() => { setViewYear(today.getFullYear()); setViewMonth(today.getMonth()); setSelectedDate(todayStr); }} className="ml-2 px-2.5 py-1 rounded-xl text-xs text-accent hover:bg-accent/10 transition-all">
              Today
            </button>
          </div>
        </div>

        <div className="grid grid-cols-7 border-b" style={{ borderColor: 'var(--border-subtle)' }}>
          {DAYS.map(d => <div key={d} className="py-2 text-center text-xs font-medium text-text-muted uppercase tracking-wider">{d}</div>)}
        </div>

        <div className="flex-1 grid grid-cols-7 overflow-hidden" style={{ gridTemplateRows: `repeat(${Math.ceil((daysInMonth + firstDay) / 7)}, 1fr)` }}>
          {calendarCells.map(cell => {
            if (cell.empty) return <div key={cell.key} className="border-b border-r" style={{ borderColor: 'var(--border-subtle)', background: 'var(--bg-elevated)' }} />
            const isSelected = cell.dateStr === selectedDate
            return (
              <div
                key={cell.key}
                onClick={() => { setSelectedDate(cell.dateStr); setShowForm(false); setEditingTask(null) }}
                className={`border-b border-r relative cursor-pointer transition-all duration-200 group ${cell.isToday ? 'bg-accent/5' : 'hover:bg-bg-surface/30'} ${isSelected ? 'ring-1 ring-inset ring-accent/40 bg-accent/10' : ''}`}
                style={{ borderColor: 'var(--border-subtle)' }}
              >
                <div className="flex items-start justify-between p-1.5">
                  <span className={`text-xs font-medium w-6 h-6 flex items-center justify-center rounded-lg ${cell.isToday ? 'text-white' : 'text-text-secondary group-hover:text-text-primary'}`}
                    style={cell.isToday ? { background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))' } : {}}>
                    {cell.day}
                  </span>
                  <button onClick={(e) => { e.stopPropagation(); openAddForDate(cell.dateStr) }} className="opacity-0 group-hover:opacity-100 p-0.5 rounded-lg hover:bg-accent/20 text-text-muted hover:text-accent transition-all" aria-label="Add task">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                  </button>
                </div>
                {cell.tasks.length > 0 && (
                  <div className="px-1 pb-1 space-y-0.5">
                    {cell.tasks.slice(0, 3).map(t => (
                      <div key={t.id} className={`text-xs leading-tight px-1 py-0.5 rounded-md truncate ${PRIORITY_COLORS[t.priority] || PRIORITY_COLORS.medium}`}>
                        {t.due_time && <span className="opacity-70">{t.due_time.slice(0, 5)} </span>}
                        {t.title}
                      </div>
                    ))}
                    {cell.tasks.length > 3 && <div className="text-xs text-text-muted text-center">+{cell.tasks.length - 3} more</div>}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {selectedDate && (
        <div className="w-80 border-l flex flex-col overflow-hidden" style={{ borderColor: 'var(--border-subtle)', background: 'rgba(var(--accent-rgb), 0.02)' }}>
          <div className="px-4 py-3 glass-strong border-b flex items-center justify-between" style={{ borderColor: 'var(--border-subtle)' }}>
            <div>
              <div className="text-sm font-medium text-text-primary">{new Date(selectedDate + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</div>
              <div className="text-xs text-text-muted">{selectedTasks.length} task{selectedTasks.length !== 1 ? 's' : ''}</div>
            </div>
            <button onClick={() => openAddForDate(selectedDate)} className="p-1.5 rounded-xl hover:bg-accent/15 text-accent transition-all" aria-label="Add task">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {showForm && (
              <div className="card p-3 space-y-2 animate-slide-up">
                <input type="text" value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} onKeyDown={handleKeyDown} placeholder="Task title" className="input-field" autoFocus />
                <textarea value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} onKeyDown={handleKeyDown} placeholder="Description (optional)" rows={2} className="input-field resize-none text-xs" />
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs text-text-muted mb-1">Time</label>
                    <input type="time" value={form.due_time} onChange={e => setForm(p => ({ ...p, due_time: e.target.value }))} className="input-field text-xs" style={{ colorScheme: 'dark' }} />
                  </div>
                  <div>
                    <label className="block text-xs text-text-muted mb-1">Priority</label>
                    <select value={form.priority} onChange={e => setForm(p => ({ ...p, priority: e.target.value }))} className="input-field text-xs" style={{ colorScheme: 'dark' }}>
                       {['low','medium','high','urgent'].map(p => <option key={p} value={p} className="text-text-primary capitalize" style={{ background: 'var(--bg-elevated)' }}>{p}</option>)}
                    </select>
                  </div>
                </div>
                <div className="flex justify-end gap-2 pt-1">
                  <button onClick={resetForm} className="btn-ghost !text-xs">Cancel</button>
                  <button onClick={handleSubmit} disabled={!form.title.trim() || loading} className="btn-primary !text-xs !px-3 !py-1" style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))' }}>
                    {editingTask ? 'Update' : 'Add'}
                  </button>
                </div>
              </div>
            )}

            {selectedTasks.length === 0 && !showForm && (
              <div className="text-center py-10">
                <div className="text-text-muted text-sm mb-3">No tasks for this day</div>
                <button onClick={() => openAddForDate(selectedDate)} className="btn-primary !text-xs">
                  + Add Task
                </button>
              </div>
            )}

            {selectedTasks.map(task => (
              <div key={task.id} className="card p-3 group animate-slide-up">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      {task.due_time && <span className="text-xs text-text-muted font-mono">{task.due_time.slice(0, 5)}</span>}
                      <span className="text-sm font-medium text-text-primary">{task.title}</span>
                    </div>
                    {task.description && <p className="text-xs text-text-secondary mt-1 line-clamp-2">{task.description}</p>}
                    <div className="flex items-center gap-2 mt-1.5">
                      {task.priority && task.priority !== 'medium' && <span className={`text-xs px-1.5 py-0.5 rounded-md capitalize ${PRIORITY_COLORS[task.priority] || ''}`}>{task.priority}</span>}
                       {task.recurrence && task.recurrence !== 'none' && <span className="text-xs text-text-muted px-1.5 py-0.5 rounded-md" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>{task.recurrence}</span>}
                    </div>
                  </div>
                  <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
                    <button onClick={() => startEdit(task)} aria-label="Edit task" className="p-1 rounded-lg hover:bg-bg-surface text-text-muted hover:text-text-secondary transition-all">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                    </button>
                    <button onClick={() => setDeleteTaskId(task.id)} aria-label="Delete task" className="p-1 rounded-lg hover:bg-bg-surface text-text-muted hover:text-red-400 transition-all">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      <ConfirmDialog open={!!deleteTaskId} title="Delete Task" message="This calendar task will be permanently removed." confirmLabel="Delete" danger onConfirm={() => handleDelete(deleteTaskId)} onCancel={() => setDeleteTaskId(null)} />
    </div>
  )
}
