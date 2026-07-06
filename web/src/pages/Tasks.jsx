import React, { useState, useEffect, useCallback } from 'react'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'
import { Button } from '@heroui/react'
import { getTasks, createTask, updateTask, deleteTask } from '../api'
import { useToast } from '../components/Toast'
import EmptyState from '../components/EmptyState'
import ConfirmDialog from '../components/ConfirmDialog'

const COLUMNS = [
  { id: 'pending', title: 'To Do', color: '#fdcb6e', icon: 'M12 6v6m0 0v6m0-6h6m-6 0H6' },
  { id: 'in_progress', title: 'In Progress', color: '#74b9ff', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
  { id: 'in_review', title: 'In Review', color: '#a29bfe', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
  { id: 'completed', title: 'Done', color: '#00b894', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
]

const PRIORITY_STYLES = {
  urgent: 'bg-red-500/15 text-red-400 border border-red-500/20',
  high: 'bg-orange-500/15 text-orange-400 border border-orange-500/15',
  medium: 'bg-accent/10 text-accent-light border border-accent/15',
  low: 'bg-blue-500/10 text-blue-400 border border-blue-500/10',
}

const TaskCard = React.memo(function TaskCard({ task, index, onEdit, onDelete }) {
  return (
    <Draggable draggableId={String(task.id)} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`p-3 mb-2 rounded-xl group ${
            snapshot.isDragging ? 'shadow-lg ring-1 ring-accent/30' : ''
          }`}
          style={{
            ...provided.draggableProps.style,
            background: snapshot.isDragging ? 'var(--bg-elevated)' : 'var(--bg-surface)',
            border: '1px solid var(--border-subtle)',
            willChange: snapshot.isDragging ? 'transform' : undefined,
          }}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-text-primary leading-snug">{task.title}</div>
              {task.description && <p className="text-xs text-text-secondary mt-1 line-clamp-2">{task.description}</p>}
              <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                {task.priority && task.priority !== 'medium' && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-md capitalize ${PRIORITY_STYLES[task.priority] || ''}`}>
                    {task.priority}
                  </span>
                )}
                {task.due_date && (
                  <span className="text-xs text-text-muted px-1.5 py-0.5 rounded-md" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
                    {task.due_date}
                  </span>
                )}
              </div>
            </div>
            <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 flex-shrink-0">
              <Button isIconOnly aria-label="Edit task" size="sm" variant="light" onPress={() => onEdit(task)} className="text-text-muted hover:text-text-secondary min-w-0 w-auto h-auto p-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </Button>
              <Button isIconOnly aria-label="Delete task" size="sm" variant="light" onPress={() => onDelete(task.id)} className="text-text-muted hover:text-red-400 min-w-0 w-auto h-auto p-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </Button>
            </div>
          </div>
        </div>
      )}
    </Draggable>
  )
})

function Column({ column, tasks, onEdit, onDelete }) {
  return (
    <div className="flex-1 min-w-0 flex flex-col">
      <div className="flex items-center gap-2 px-2 py-2 mb-2">
        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: column.color, boxShadow: `0 0 8px ${column.color}44` }} />
        <span className="text-xs font-semibold text-text-primary uppercase tracking-wider">{column.title}</span>
        <span className="text-xs text-text-muted rounded-full px-1.5 py-0.5 ml-auto" style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
          {tasks.length}
        </span>
      </div>
      <Droppable droppableId={column.id}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={`flex-1 rounded-xl p-2 space-y-0 overflow-y-auto min-h-[120px] ${
              snapshot.isDraggingOver ? 'ring-1 ring-inset ring-accent/30' : ''
            }`}
            style={{
              background: snapshot.isDraggingOver ? 'rgba(var(--accent-rgb), 0.06)' : 'var(--bg-elevated)',
              border: `1px dashed ${snapshot.isDraggingOver ? 'rgba(var(--accent-rgb), 0.3)' : 'var(--border-subtle)'}`,
            }}
          >
            {tasks.map((task, index) => (
              <TaskCard key={task.id} task={task} index={index} onEdit={onEdit} onDelete={onDelete} />
            ))}
            {provided.placeholder}
            {tasks.length === 0 && !snapshot.isDraggingOver && (
              <div className="text-center py-8 text-text-muted text-xs">Drop tasks here</div>
            )}
          </div>
        )}
      </Droppable>
    </div>
  )
}

export default function Tasks() {
  const [tasks, setTasks] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [form, setForm] = useState({ title: '', description: '', priority: 'medium' })
  const [loading, setLoading] = useState(false)
  const [deleteId, setDeleteId] = useState(null)
  const toast = useToast()

  const loadTasks = useCallback(async () => {
    try { const res = await getTasks(); setTasks(Array.isArray(res) ? res : res?.tasks || []) } catch {}
  }, [])

  useEffect(() => { loadTasks() }, [loadTasks])

  const resetForm = () => { setForm({ title: '', description: '', priority: 'medium' }); setEditingTask(null); setShowForm(false) }

  const handleCreate = async () => {
    if (!form.title.trim()) return
    setLoading(true)
    try { await createTask({ title: form.title.trim(), description: form.description.trim(), priority: form.priority, status: 'pending' }); resetForm(); await loadTasks(); toast.success('Task created') }
    catch { toast.error('Failed to create task') } finally { setLoading(false) }
  }

  const handleUpdate = async (id, updates) => {
    try { await updateTask(id, updates) }
    catch { toast.error('Failed to update task') }
  }

  const handleDelete = async () => {
    if (!deleteId) return
    try { await deleteTask(deleteId); setDeleteId(null); await loadTasks(); toast.success('Task deleted') }
    catch { toast.error('Failed to delete task') }
  }

  const startEdit = (task) => { setEditingTask(task); setForm({ title: task.title, description: task.description || '', priority: task.priority || 'medium' }); setShowForm(true) }

  const handleEditSubmit = async () => {
    if (!form.title.trim() || !editingTask) return
    setLoading(true)
    try { await updateTask(editingTask.id, { title: form.title.trim(), description: form.description.trim(), priority: form.priority }); resetForm(); await loadTasks() }
    catch { toast.error('Failed to update task') } finally { setLoading(false) }
  }

  const onDragEnd = (result) => {
    const { destination, source, draggableId } = result
    if (!destination) return
    if (destination.droppableId === source.droppableId && destination.index === source.index) return

    const taskId = parseInt(draggableId)
    const newStatus = destination.droppableId
    const previousTasks = tasks

    setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: newStatus } : t))

    handleUpdate(taskId, { status: newStatus }).catch(() => {
      setTasks(previousTasks)
    })
  }

  const tasksByColumn = COLUMNS.map(col => ({ ...col, tasks: tasks.filter(t => t.status === col.id) }))
  const totalTasks = tasks.length

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); editingTask ? handleEditSubmit() : handleCreate() }
    if (e.key === 'Escape') resetForm()
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 glass-strong border-b flex items-center justify-between" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))' }}>
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <span className="font-brand text-sm font-medium text-text-primary">Tasks</span>
          <span className="text-xs text-text-muted">({totalTasks})</span>
        </div>
        <Button size="sm" variant="light" onPress={() => { resetForm(); setShowForm(true) }} className="btn-primary !text-xs min-w-0">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Task
        </Button>
      </div>

      {showForm && (
        <div className="px-4 py-3 glass-strong border-b animate-slide-up" style={{ borderColor: 'var(--border-subtle)' }}>
          <div className="max-w-2xl mx-auto">
            <div className="text-xs text-text-muted mb-2 uppercase tracking-wider font-medium">{editingTask ? 'Edit Task' : 'New Task'}</div>
            <input type="text" value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} onKeyDown={handleKeyDown} placeholder="Task title" className="input-field mb-2" autoFocus />
            <textarea value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} onKeyDown={handleKeyDown} placeholder="Description (optional)" rows={2} className="input-field mb-2 resize-none" />
            <div className="flex items-center justify-between">
              <select value={form.priority} onChange={e => setForm(p => ({ ...p, priority: e.target.value }))} className="input-field" style={{ colorScheme: 'dark' }}>
                <option value="low" className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>Low Priority</option>
                <option value="medium" className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>Medium Priority</option>
                <option value="high" className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>High Priority</option>
                <option value="urgent" className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>Urgent</option>
              </select>
              <div className="flex gap-2">
                <Button size="sm" variant="light" onPress={resetForm} className="!text-xs">Cancel</Button>
                <Button size="sm" variant="light" onPress={editingTask ? handleEditSubmit : handleCreate} isDisabled={!form.title.trim() || loading} className="btn-primary !text-xs" style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))' }}>
                  {editingTask ? 'Update' : 'Create'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-hidden px-4 py-4">
        <DragDropContext onDragEnd={onDragEnd}>
          <div className="flex gap-4 h-full">
            {tasksByColumn.map(col => (
              <Column key={col.id} column={col} tasks={col.tasks} onEdit={startEdit} onDelete={(id) => setDeleteId(id)} />
            ))}
          </div>
        </DragDropContext>
      </div>

      <ConfirmDialog open={!!deleteId} title="Delete Task" message="Are you sure you want to delete this task? This cannot be undone." confirmLabel="Delete" danger onConfirm={handleDelete} onCancel={() => setDeleteId(null)} />
    </div>
  )
}
