import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' }
})

client.interceptors.response.use(
  res => res.data,
  err => {
    const msg = err.response?.data?.detail || err.message || 'Request failed'
    return Promise.reject(new Error(msg))
  }
)

export const sendChat = (data) => client.post('/chat', data)
export const chatUpload = (formData) => client.post('/chat/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const uploadDocument = (formData) => client.post('/documents/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const getSessions = () => client.get('/sessions')
export const getSessionMessages = (sessionId) => client.get(`/sessions/${sessionId}`)
export const clearHistory = () => client.delete('/history')

export const getTasks = () => client.get('/tasks')
export const createTask = (data) => client.post('/tasks', data)
export const updateTask = (id, data) => client.put(`/tasks/${id}`, data)
export const deleteTask = (id) => client.delete(`/tasks/${id}`)

export const getScheduledTasks = () => client.get('/calendar')
export const createScheduledTask = (data) => client.post('/calendar', data)
export const updateScheduledTask = (id, data) => client.put(`/calendar/${id}`, data)
export const deleteScheduledTask = (id) => client.delete(`/calendar/${id}`)

export const getSkills = () => client.get('/skills')
export const getSkill = (id) => client.get(`/skills/${id}`)
export const createSkill = (data) => client.post('/skills', data)
export const updateSkill = (id, data) => client.put(`/skills/${id}`, data)
export const deleteSkill = (id) => client.delete(`/skills/${id}`)

export const getSettings = () => client.get('/settings')
export const saveSettings = (data) => client.put('/settings', data)

export const getAgents = () => client.get('/agents')
export const createAgent = (data) => client.post('/agents', data)
export const updateAgent = (id, data) => client.put(`/agents/${id}`, data)
export const deleteAgent = (id) => client.delete(`/agents/${id}`)

export const getPersonality = () => client.get('/personality')
export const savePersonality = (data) => client.put('/personality', data)

export const getMemory = () => client.get('/knowledge')
export const clearMemory = () => client.delete('/memory')

export const getKnowledge = () => client.get('/knowledge')
export const addKnowledge = (data) => client.post('/knowledge', data)
export const deleteKnowledge = (id) => client.delete(`/knowledge/${id}`)

export const getPatterns = () => client.get('/patterns')

export const getProactiveStatus = () => client.get('/proactive/status')

export const getJournalFeed = () => client.get('/persona/journal')
export const searchMemory = (query) => client.get('/memory/search', { params: { q: query } })

export const getAgentRuns = () => client.get('/agent-runs')
export const getLastRunPerAgent = () => client.get('/agent-runs/last')

export const startResearch = (data) => client.post('/research/start', data)
export const getResearchQueue = () => client.get('/research/queue')
export const listResearchRuns = () => client.get('/research/runs')
export const getResearchRun = (id) => client.get(`/research/runs/${id}`)
export const deleteResearchRun = (id) => client.delete(`/research/runs/${id}`)
export const discussResearch = (data) => client.post('/research/discuss', data)

export const startDeepResearch = (data) => client.post('/research/deep', data)
export const downloadDeepResearchDocx = (id) => `${client.defaults.baseURL || '/api'}/research/deep/${id}/download.docx`

export const exportContent = (data) => client.post('/export', data)

export const getModels = () => client.get('/models')
export const setDefaultModel = (model) => client.put('/models/default', { model })
export const testModels = () => client.post('/models/test')
