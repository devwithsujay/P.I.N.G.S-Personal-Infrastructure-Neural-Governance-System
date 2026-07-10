import React, { useState, useEffect, useCallback, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { startResearch, startDeepResearch, getResearchQueue, listResearchRuns, getResearchRun, deleteResearchRun, discussResearch, getModels, downloadDeepResearchDocx } from '../api'
import { useToast } from '../components/Toast'
import { Button, Spinner } from '@heroui/react'

const MODES = [
  { id: 'auto', label: 'Auto', color: 'var(--accent)' },
  { id: 'product', label: 'Product', color: '#00cec9' },
  { id: 'compare', label: 'Compare', color: '#fdcb6e' },
  { id: 'how-to', label: 'How-To', color: '#e17055' },
  { id: 'fact-check', label: 'Fact-Check', color: '#74b9ff' },
  { id: 'deep', label: 'Deep', color: '#a78bfa' },
]

const ROUNDS = [1, 2, 3, 4, 5]

const REPORT_TABS = [
  { id: 'summary', label: 'Summary', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { id: 'deepdive', label: 'Deep-Dive', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  { id: 'sources', label: 'Sources', icon: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1' },
]

function extractSections(markdown) {
  if (!markdown) return { summary: '', deepdive: '', sources: [], raw: '' }
  const lines = markdown.split('\n')
  let summary = [], deepdive = [], sources = []
  let currentSection = 'header', passedSummary = false

  for (const line of lines) {
    const lower = line.toLowerCase().trim()
    if (lower.startsWith('## summary') || lower.startsWith('## key takeaway')) { currentSection = 'summary'; passedSummary = true; continue }
    if (lower.startsWith('## source') || lower.startsWith('## references')) { currentSection = 'sources'; continue }
    if (lower.startsWith('## ') && passedSummary && currentSection !== 'sources') currentSection = 'deepdive'

    if (currentSection === 'summary') summary.push(line)
    else if (currentSection === 'sources') {
      const sourceMatch = line.match(/^\d+\.\s+(.*)/)
      if (sourceMatch) {
        const raw = sourceMatch[1].trim()
        const urlMatch = raw.match(/\[([^\]]+)\]\(([^)]+)\)/)
        if (urlMatch) sources.push({ title: urlMatch[1], url: urlMatch[2] })
        else if (raw.startsWith('http')) {
          try { const u = new URL(raw); sources.push({ title: u.hostname.replace('www.', ''), url: raw }) }
          catch { sources.push({ title: raw.slice(0, 60), url: raw }) }
        } else sources.push({ title: raw.slice(0, 80), url: '' })
      }
    } else if (currentSection === 'deepdive' || (currentSection === 'header' && !passedSummary)) deepdive.push(line)
  }

  if (summary.length === 0 && deepdive.length > 0) {
    const firstParagraph = deepdive.join('\n').split(/\n\n+/)[0]
    summary = [firstParagraph]
    deepdive = deepdive.slice(firstParagraph.split('\n').length)
  }

  return { summary: summary.join('\n').trim(), deepdive: deepdive.join('\n').trim(), sources, raw: markdown }
}

function SourceCard({ source, index }) {
  let domain = ''
  try { domain = new URL(source.url).hostname.replace('www.', '') } catch { domain = source.title.slice(0, 40) }

  const faviconUrl = source.url ? `https://www.google.com/s2/favicons?domain=${domain}&sz=32` : null

  const typeBadge = (() => {
    if (!domain) return null
    if (domain.endsWith('.pdf')) return { label: 'PDF', color: 'text-red-400 bg-red-500/10' }
    if (domain.includes('wiki')) return { label: 'Wiki', color: 'text-blue-400 bg-blue-500/10' }
    if (domain.includes('github')) return { label: 'Code', color: 'text-green-400 bg-green-500/10' }
    if (domain.includes('news') || domain.includes('bbc') || domain.includes('cnn')) return { label: 'News', color: 'text-orange-400 bg-orange-500/10' }
    return { label: 'Web', color: 'text-text-muted bg-bg-surface' }
  })()

  return (
    <div className="flex items-start gap-3 p-3 rounded-xl hover:bg-bg-surface/40 transition-all duration-200 group border border-transparent hover:border-border-glow">
      <div className="flex-shrink-0 mt-0.5 w-8 h-8 rounded-lg bg-bg-surface flex items-center justify-center overflow-hidden">
        {faviconUrl ? (
          <img src={faviconUrl} alt="" className="w-4 h-4" onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }} />
        ) : null}
        <span className={`text-xs font-bold font-mono ${faviconUrl ? 'hidden' : 'flex'} items-center justify-center w-full h-full text-accent-light`}>
          {index}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-text-primary font-medium truncate group-hover:text-accent-light transition-colors">{source.title}</div>
        <div className="flex items-center gap-2 mt-1">
          {domain && <span className="text-xs text-text-muted truncate">{domain}</span>}
          {typeBadge && (
            <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${typeBadge.color}`}>{typeBadge.label}</span>
          )}
        </div>
      </div>
      {source.url && (
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0 p-1.5 rounded-lg text-text-muted hover:text-accent-light hover:bg-accent/10 transition-all opacity-0 group-hover:opacity-100"
          onClick={e => e.stopPropagation()}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      )}
    </div>
  )
}

function ReportView({ report, reportHtml, activeTab }) {
  const sections = extractSections(report)
  const contentRef = useRef(null)

  useEffect(() => { if (contentRef.current) contentRef.current.scrollTop = 0 }, [activeTab])

  const renderMarkdown = (text) => (
    <div className="prose prose-invert prose-purple max-w-none">
      <ReactMarkdown>{text}</ReactMarkdown>
    </div>
  )

  if (activeTab === 'summary') {
    const summaryText = sections.summary || sections.raw.split('\n\n').slice(0, 3).join('\n\n')
    return (
      <div ref={contentRef} className="p-5 overflow-y-auto max-h-[60vh]">
        {summaryText ? renderMarkdown(summaryText) : <p className="text-text-muted text-sm italic">No executive summary available.</p>}
      </div>
    )
  }

  if (activeTab === 'deepdive') {
    return (
      <div ref={contentRef} className="p-5 overflow-y-auto max-h-[60vh]">
        {sections.deepdive ? renderMarkdown(sections.deepdive) : <p className="text-text-muted text-sm italic">No deep-dive content available.</p>}
      </div>
    )
  }

  if (activeTab === 'sources') {
    return (
      <div ref={contentRef} className="p-5 overflow-y-auto max-h-[60vh]">
        {sections.sources.length > 0 ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs text-text-muted uppercase tracking-wider font-medium">Sources Found</span>
              <span className="status-pill status-pill-info">{sections.sources.length} sources</span>
            </div>
            <div className="space-y-1">
              {sections.sources.map((s, i) => <SourceCard key={i} source={s} index={i + 1} />)}
            </div>
          </div>
        ) : (
          <p className="text-text-muted text-sm italic">No sources extracted from this report.</p>
        )}
      </div>
    )
  }
  return null
}

function CapsuleTabs({ tabs, active, onChange }) {
  const [indicatorStyle, setIndicatorStyle] = useState({})
  const tabRefs = useRef({})

  useEffect(() => {
    const el = tabRefs.current[active]
    if (el) {
      setIndicatorStyle({
        left: el.offsetLeft,
        width: el.offsetWidth,
      })
    }
  }, [active])

  return (
    <div className="capsule-tabs relative">
      <div
        className="absolute top-1 bottom-1 rounded-lg transition-all duration-300"
        style={{
          left: indicatorStyle.left || 0,
          width: indicatorStyle.width || 0,
          background: 'rgba(var(--accent-rgb), 0.15)',
          boxShadow: '0 0 12px rgba(var(--accent-rgb), 0.1)',
        }}
      />
      {tabs.map(tab => (
        <button
          key={tab.id}
          ref={el => { tabRefs.current[tab.id] = el }}
          onClick={() => onChange(tab.id)}
          className={`capsule-tab flex items-center gap-1.5 ${active === tab.id ? 'active' : ''}`}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
          </svg>
          <span className="hidden sm:inline">{tab.label}</span>
        </button>
      ))}
    </div>
  )
}

export default function ResearchPage() {
  const [topic, setTopic] = useState('')
  const [mode, setMode] = useState('auto')
  const [rounds, setRounds] = useState(3)
  const [searchEngine, setSearchEngine] = useState('auto')
  const [model, setModel] = useState('')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [queue, setQueue] = useState([])
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [loading, setLoading] = useState(false)
  const [deepLoading, setDeepLoading] = useState(false)
  const [discussMsg, setDiscussMsg] = useState('')
  const [models, setModels] = useState([])
  const [reportTab, setReportTab] = useState('summary')
  const [deepSections, setDeepSections] = useState(12)
  const toast = useToast()

  const loadData = useCallback(async () => {
    try {
      const [q, r, m] = await Promise.all([
        getResearchQueue().catch(() => []),
        listResearchRuns().catch(() => []),
        getModels().catch(() => ({}))
      ])
      setQueue(Array.isArray(q) ? q : q?.queue || [])
      setRuns(Array.isArray(r) ? r : r?.runs || [])
      const modelList = m?.models || m?.available || []
      setModels(Array.isArray(modelList) ? modelList : [])
      if (!model && m?.default_model) setModel(m.default_model)
    } catch {}
  }, [model])

  useEffect(() => { loadData() }, [loadData])

  useEffect(() => {
    const hasActive = queue.length > 0 || runs.some(r => r.status === 'running' || r.status === 'queued')
    if (!hasActive) return
    const interval = setInterval(loadData, 3000)
    return () => clearInterval(interval)
  }, [queue.length, runs, loadData])

  const handleStart = async () => {
    if (!topic.trim() || loading || deepLoading) return
    if (mode === 'deep') {
      setDeepLoading(true)
      try {
        await startDeepResearch({ topic: topic.trim(), sections: deepSections, max_sources: 50 })
        setTopic('')
        toast.success('Deep research started (this may take several minutes)')
        await loadData()
      } catch { toast.error('Failed to start deep research') } finally { setDeepLoading(false) }
      return
    }
    setLoading(true)
    try {
      await startResearch({ topic: topic.trim(), mode, rounds, search_engine: searchEngine === 'auto' ? null : searchEngine, model: model || undefined })
      setTopic('')
      toast.success('Research started')
      await loadData()
    } catch { toast.error('Failed to start research') } finally { setLoading(false) }
  }

  const handleDiscuss = async (runId) => {
    if (!discussMsg.trim()) return
    try {
      await discussResearch({ run_id: runId, message: discussMsg.trim() })
      setDiscussMsg('')
      const updated = await getResearchRun(runId)
      setSelectedRun(updated)
      toast.success('Discussion added')
    } catch { toast.error('Failed to add discussion') }
  }

  const handleDelete = async (id) => {
    try {
      await deleteResearchRun(id)
      if (selectedRun?.id === id) setSelectedRun(null)
      await loadData()
      toast.success('Research deleted')
    } catch { toast.error('Failed to delete research') }
  }

  const hasReport = selectedRun?.report || selectedRun?.report_html

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 glass-strong border-b" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))' }}>
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <span className="font-brand text-sm font-medium text-text-primary">Research</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
          {/* Search Bar */}
          <div className="glass-strong p-6 animate-slide-up rounded-2xl">
            <div className="flex gap-3 mb-4">
              <div className="flex-1 relative">
                <svg className="w-5 h-5 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  value={topic}
                  onChange={e => setTopic(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleStart()}
                  placeholder="What do you want to research?"
                  className="input-field flex-1 !pl-10"
                />
              </div>
              <Button
                onPress={handleStart}
                isDisabled={!topic.trim() || loading || deepLoading}
                className={`flex items-center gap-2 !px-5 ${mode === 'deep' ? 'btn-deep' : 'btn-accent'}`}
                startContent={loading || deepLoading ? <Spinner size="sm" className="text-white" /> : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>}
              >
                {deepLoading ? 'Researching...' : mode === 'deep' ? 'Deep Research' : 'Research'}
              </Button>
            </div>

            <div className="flex flex-wrap gap-2 mb-3">
              {MODES.map(m => (
                <Button
                  key={m.id}
                  onPress={() => setMode(m.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all duration-200 ${
                    mode === m.id ? 'text-white shadow-lg' : 'text-text-secondary hover:text-text-primary'
                  }`}
                  style={mode === m.id
                    ? { backgroundColor: m.color, boxShadow: `0 0 16px ${m.color}33` }
                    : { background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }
                  }
                >
                  {m.label}
                </Button>
              ))}
            </div>

            <Button
              onPress={() => setSettingsOpen(!settingsOpen)}
              className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors bg-transparent"
              startContent={<svg className={`w-3 h-3 transition-transform duration-200 ${settingsOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>}
            >
              Settings
            </Button>

            {settingsOpen && mode === 'deep' && (
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3 animate-fade-in">
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Sections ({deepSections})</label>
                  <input type="range" min={8} max={20} value={deepSections} onChange={e => setDeepSections(Number(e.target.value))} className="w-full accent-[#a78bfa]" />
                  <span className="text-[10px] text-text-muted mt-1 block">More sections = more comprehensive report</span>
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Model</label>
                  <select value={model} onChange={e => setModel(e.target.value)} className="input-field" style={{ colorScheme: 'dark' }}>
                    <option value="" className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>Default</option>
                    {models.map(m => <option key={m.id || m} value={m.id || m} className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>{m.name || m.id || m}</option>)}
                  </select>
                </div>
              </div>
            )}
            {settingsOpen && mode !== 'deep' && (
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 animate-fade-in">
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Rounds</label>
                  <select value={rounds} onChange={e => setRounds(Number(e.target.value))} className="input-field" style={{ colorScheme: 'dark' }}>
                    {ROUNDS.map(r => <option key={r} value={r} className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>{r} rounds</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Search Engine</label>
                  <select value={searchEngine} onChange={e => setSearchEngine(e.target.value)} className="input-field" style={{ colorScheme: 'dark' }}>
                    <option value="auto" className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>Auto</option>
                    <option value="searxng" className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>SearXNG</option>
                    <option value="serpapi" className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>SerpAPI</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Model</label>
                  <select value={model} onChange={e => setModel(e.target.value)} className="input-field" style={{ colorScheme: 'dark' }}>
                    <option value="" className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>Default</option>
                    {models.map(m => <option key={m.id || m} value={m.id || m} className="text-text-primary" style={{ background: 'var(--bg-elevated)' }}>{m.name || m.id || m}</option>)}
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Active */}
          {queue.length > 0 && (
            <div className="animate-slide-up">
              <h3 className="text-xs text-text-muted uppercase tracking-wider mb-3 font-medium">Active Research</h3>
              <div className="space-y-2">
                {queue.map((item, i) => (
                  <div key={item.id || i} className="glass rounded-xl p-3 flex items-center gap-3">
                    {item.status === 'running' ? (
                      <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse shadow-lg shadow-green-500/50" />
                    ) : (
                      <span className="w-4 h-4 border-2 border-accent/50 border-t-accent rounded-full animate-spin" />
                    )}
                    <div className="flex-1">
                      <span className="text-sm text-text-primary">{item.topic || item.title}</span>
                      <span className="ml-2 text-xs text-text-muted capitalize">{item.mode || 'auto'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Report Reader */}
          {selectedRun && hasReport && (
            <div className="glass-glow-border overflow-hidden animate-slide-up">
              <div className="px-5 pt-5 pb-3 border-b" style={{ borderColor: 'var(--border-subtle)' }}>
                <div className="flex items-start justify-between mb-1">
                  <h2 className="text-lg font-brand font-semibold text-text-primary leading-tight">{selectedRun.topic || selectedRun.title}</h2>
                  <Button isIconOnly variant="light" onPress={() => setSelectedRun(null)} aria-label="Close report" className="p-1.5 rounded-xl text-text-muted hover:text-text-primary hover:bg-bg-surface transition-all ml-3 flex-shrink-0">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </Button>
                </div>
                <div className="flex items-center gap-3 text-xs text-text-muted">
                  <span className="px-2 py-0.5 rounded-full capitalize font-medium" style={{
                    backgroundColor: (MODES.find(m => m.id === selectedRun.mode)?.color || 'var(--accent)') + '20',
                    color: MODES.find(m => m.id === selectedRun.mode)?.color || 'var(--accent)'
                  }}>{selectedRun.mode || 'auto'}</span>
                  <span>{selectedRun.sources_count || extractSections(selectedRun.report).sources.length || 0} sources</span>
                  <span>{new Date(selectedRun.created_at || selectedRun.timestamp).toLocaleDateString()}</span>
                  {selectedRun.report_docx_path && (
                    <a href={downloadDeepResearchDocx(selectedRun.id)} target="_blank" rel="noopener noreferrer"
                      className="ml-auto inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium transition-all"
                      style={{ background: '#a78bfa20', color: '#a78bfa' }}>
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Download DOCX
                    </a>
                  )}
                </div>
              </div>

              <div className="px-5 pt-3">
                <CapsuleTabs tabs={REPORT_TABS} active={reportTab} onChange={setReportTab} />
              </div>

              <ReportView report={selectedRun.report} reportHtml={selectedRun.report_html} activeTab={reportTab} />

              <div className="px-5 pb-4 pt-2 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={discussMsg}
                    onChange={e => setDiscussMsg(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleDiscuss(selectedRun.id)}
                    placeholder="Ask about this research..."
                    className="input-field flex-1"
                  />
                  <Button variant="light" onPress={() => handleDiscuss(selectedRun.id)} className="btn-primary">
                    Send
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Past Research List */}
          <div>
            <h3 className="text-xs text-text-muted uppercase tracking-wider mb-3 font-medium">Past Research</h3>
            {runs.length === 0 ? (
              <div className="text-center py-12 text-text-muted text-sm">No research runs yet</div>
            ) : (
              <div className="space-y-2">
                {runs.map((run) => {
                  const isSelected = selectedRun?.id === run.id
                  const runHasReport = run.report || run.report_html
                  return (
                    <div
                      key={run.id}
                      className={`card-hover p-4 cursor-pointer ${
                        isSelected ? '!border-glow !shadow-glow' : ''
                      }`}
                      onClick={() => { if (isSelected) { setSelectedRun(null) } else { setSelectedRun(run); setReportTab('summary') } }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium text-text-primary">{run.topic || run.title}</span>
                            <span className="px-2 py-0.5 rounded-full text-xs capitalize" style={{
                              backgroundColor: (MODES.find(m => m.id === run.mode)?.color || 'var(--accent)') + '20',
                              color: MODES.find(m => m.id === run.mode)?.color || 'var(--accent)'
                            }}>{run.mode || 'auto'}</span>
                            {run.type === 'deep' && <span className="status-pill text-xs" style={{ background: '#a78bfa20', color: '#a78bfa' }}>DEEP</span>}
                            {runHasReport && <span className="status-pill status-pill-success text-xs">REPORT</span>}
                          </div>
                          <div className="text-xs text-text-muted">
                            {run.sources_count || 0} sources · {new Date(run.created_at || run.timestamp).toLocaleDateString()}
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5" onClick={e => e.stopPropagation()}>
                          {run.status === 'queued' && <span className="w-2.5 h-2.5 rounded-full bg-yellow-400 animate-pulse shadow-[0_0_6px_rgba(250,204,21,0.6)]" title="Queued" />}
                          {run.status === 'running' && <span className="w-2.5 h-2.5 rounded-full bg-green-400 animate-pulse shadow-[0_0_6px_rgba(74,222,128,0.6)]" title="Running" />}
                          {run.status === 'completed' && <span className="w-2.5 h-2.5 rounded-full bg-green-500 shadow-[0_0_4px_rgba(34,197,94,0.4)]" title="Completed" />}
                          {run.status === 'failed' && <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-[0_0_4px_rgba(239,68,68,0.4)]" title="Failed" />}
                          {run.report_docx_path && (
                            <a href={downloadDeepResearchDocx(run.id)} target="_blank" rel="noopener noreferrer"
                              className="p-1.5 rounded-xl hover:bg-bg-surface text-text-muted hover:text-green-400 transition-all"
                              title="Download DOCX">
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </a>
                          )}
                          <Button isIconOnly variant="light" onPress={() => handleDelete(run.id)} aria-label="Delete research run" className="p-1.5 rounded-xl hover:bg-bg-surface text-text-muted hover:text-red-400 transition-all">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </Button>
                        </div>
                      </div>

                      {isSelected && !runHasReport && (
                        <div className="mt-3 pt-3 border-t animate-fade-in" style={{ borderColor: 'var(--border-subtle)' }}>
                          <p className="text-xs text-text-muted italic">Report not available yet. Still processing.</p>
                          <div className="flex gap-2 mt-3">
                            <input type="text" value={discussMsg} onChange={e => setDiscussMsg(e.target.value)}
                              onKeyDown={e => e.key === 'Enter' && handleDiscuss(run.id)} placeholder="Discuss this research..." className="input-field flex-1 text-xs" />
                            <Button variant="light" onPress={() => handleDiscuss(run.id)} className="btn-primary !text-xs !px-3">Send</Button>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
