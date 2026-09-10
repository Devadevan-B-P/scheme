import { useState, useEffect, useCallback } from 'react'
import { 
  Building2, 
  ShieldCheck, 
  Database, 
  Globe, 
  RefreshCw, 
  FileText, 
  FolderCheck, 
  CheckCircle2, 
  AlertTriangle, 
  Terminal,
  ExternalLink,
  Lock,
  Plus,
  Eye,
  XCircle,
  History,
  Cpu,
  Zap,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  ShieldAlert,
  Sliders,
} from 'lucide-react'
import useChatStore from '../store/chatStore'
import {
  triggerScrape,
  getScraperJobs,
  getScraperJob,
  getScrapedSchemes,
  getSchemeVersions,
  publishScrapedScheme,
  rejectScrapedScheme,
  getSources,
  createSource,
  approveSource,
  getScraperChanges,
  getAuditLogs,
} from '../api/client'

// ── Status badge styling ──────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const map = {
    published:         'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    draft:             'bg-slate-800 text-slate-300 border-slate-700',
    review_required:   'bg-amber-500/20 text-amber-300 border-amber-500/30',
    validated:         'bg-blue-500/20 text-blue-300 border-blue-500/30',
    reviewed:          'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
    validation_failed: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
    rejected:          'bg-rose-900/30 text-rose-400 border-rose-700/50',
    superseded:        'bg-purple-500/20 text-purple-300 border-purple-500/30',
    archived:          'bg-slate-800 text-slate-400 border-slate-700',
    conflict:          'bg-orange-500/20 text-orange-300 border-orange-500/30',
    queued:            'bg-slate-800 text-slate-400 border-slate-700',
    running:           'bg-blue-500/20 text-blue-300 border-blue-500/30',
    success:           'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    failed:            'bg-rose-500/20 text-rose-300 border-rose-500/30',
  }
  const cls = map[status] || 'bg-slate-800 text-slate-300 border-slate-700'
  return (
    <span className={`px-2.5 py-1 rounded-md text-[10px] font-extrabold border uppercase tracking-wider ${cls}`}>
      {status?.replace(/_/g, ' ')}
    </span>
  )
}

function ExtractionBadge({ method }) {
  if (!method) return null
  const isFirecrawl = method === 'firecrawl'
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border ${
      isFirecrawl 
        ? 'bg-violet-500/20 text-violet-300 border-violet-500/30' 
        : 'bg-slate-800 text-slate-300 border-slate-700'
    }`}>
      {isFirecrawl ? <Zap size={10} className="text-violet-400" /> : <Cpu size={10} className="text-slate-400" />}
      {isFirecrawl ? 'Firecrawl' : 'httpx fallback'}
    </span>
  )
}

export default function AdminDashboard() {
  const { adminTab, setAdminTab } = useChatStore()

  // ── Scraper state ───────────────────────────────────────────────────────────
  const [scrapeUrl, setScrapeUrl] = useState('https://nsfdc.nic.in/faqs')
  const [scraperRunning, setScraperRunning] = useState(false)
  const [scrapeError, setScrapeError] = useState('')
  const [activeJobId, setActiveJobId] = useState(null)

  // ── Data state ──────────────────────────────────────────────────────────────
  const [jobs, setJobs] = useState([])
  const [schemes, setSchemes] = useState([])
  const [sources, setSources] = useState([])
  const [changes, setChanges] = useState([])
  const [auditLogs, setAuditLogs] = useState([])

  // ── Source registration form ────────────────────────────────────────────────
  const [showSourceForm, setShowSourceForm] = useState(false)
  const [sourceForm, setSourceForm] = useState({
    domain: '', authority: '', display_name: '', base_url: '',
    allowed_topics: '', source_type: 'official_scheme_page', priority: 'medium',
  })

  // ── Scheme detail panel ─────────────────────────────────────────────────────
  const [expandedScheme, setExpandedScheme] = useState(null)
  const [schemeVersions, setSchemeVersions] = useState({})

  // ── Fetch helpers ───────────────────────────────────────────────────────────
  const fetchJobs = useCallback(async () => {
    try {
      const data = await getScraperJobs()
      setJobs(data)
    } catch {}
  }, [])

  const fetchSchemes = useCallback(async () => {
    try {
      const data = await getScrapedSchemes()
      setSchemes(data)
    } catch {}
  }, [])

  const fetchSources = useCallback(async () => {
    try {
      const data = await getSources()
      setSources(data)
    } catch {}
  }, [])

  const fetchChanges = useCallback(async () => {
    try {
      const data = await getScraperChanges()
      setChanges(data)
    } catch {}
  }, [])

  const fetchAuditLogs = useCallback(async () => {
    try {
      const data = await getAuditLogs()
      setAuditLogs(data)
    } catch {}
  }, [])

  // Load data on tab switch
  useEffect(() => {
    if (adminTab === 'scraper') fetchJobs()
    if (adminTab === 'schemes') fetchSchemes()
    if (adminTab === 'sources') fetchSources()
    if (adminTab === 'changes') fetchChanges()
    if (adminTab === 'audit-logs') fetchAuditLogs()
  }, [adminTab, fetchJobs, fetchSchemes, fetchSources, fetchChanges, fetchAuditLogs])

  // Poll active job
  useEffect(() => {
    if (!activeJobId) return
    const interval = setInterval(async () => {
      try {
        const job = await getScraperJob(activeJobId)
        setJobs(prev => {
          const idx = prev.findIndex(j => j.job_id === activeJobId)
          if (idx >= 0) { const n = [...prev]; n[idx] = job; return n }
          return [job, ...prev]
        })
        if (job.status === 'success' || job.status === 'failed') {
          setActiveJobId(null)
          setScraperRunning(false)
          if (job.status === 'success') fetchSchemes()
        }
      } catch {}
    }, 2000)
    return () => clearInterval(interval)
  }, [activeJobId, fetchSchemes])

  // ── Actions ─────────────────────────────────────────────────────────────────
  const handleTriggerScraper = async () => {
    setScrapeError('')
    setScraperRunning(true)
    try {
      const data = await triggerScrape(scrapeUrl, 'admin')
      setActiveJobId(data.job_id)
      setJobs(prev => [{ job_id: data.job_id, url: scrapeUrl, status: 'queued', created_at: new Date().toISOString() }, ...prev])
    } catch (e) {
      setScrapeError(e.message || 'Scrape failed')
      setScraperRunning(false)
    }
  }

  const handlePublish = async (schemeId) => {
    try {
      await publishScrapedScheme(schemeId, 'admin')
      fetchSchemes()
    } catch (e) {
      alert(e.message || 'Failed to publish scheme')
    }
  }

  const handleReject = async (schemeId) => {
    const reason = prompt('Rejection reason:')
    if (!reason) return
    try {
      await rejectScrapedScheme(schemeId, reason, 'admin')
      fetchSchemes()
    } catch (e) {
      alert(e.message || 'Failed to reject scheme')
    }
  }

  const handleApproveSource = async (sourceId) => {
    try {
      await approveSource(sourceId)
      fetchSources()
    } catch (e) {
      alert(e.message || 'Failed to approve source')
    }
  }

  const handleRegisterSource = async () => {
    const body = {
      ...sourceForm,
      allowed_topics: sourceForm.allowed_topics.split(',').map(t => t.trim()).filter(Boolean),
    }
    try {
      await createSource(body)
      fetchSources()
      setShowSourceForm(false)
    } catch (e) {
      alert(e.message || 'Failed to register source')
    }
  }

  const loadVersions = async (schemeId) => {
    try {
      const versions = await getSchemeVersions(schemeId)
      setSchemeVersions(prev => ({ ...prev, [schemeId]: versions }))
    } catch {}
  }

  const tabs = [
    { id: 'scraper', label: 'Firecrawl Pipeline' },
    { id: 'schemes', label: `Scheme Registry${schemes.length ? ` (${schemes.length})` : ''}` },
    { id: 'sources', label: 'Source Registry' },
    { id: 'changes', label: `Pending Changes${changes.length ? ` (${changes.length})` : ''}` },
    { id: 'audit-logs', label: 'Audit Trail' },
  ]

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">

      {/* ── Header ───────────────────────────────────────────────────────────── */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur-md">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 text-xs font-bold mb-2 border border-amber-500/20">
            <Lock size={13} />
            <span>Ministry Administration Portal</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black tracking-tight">SchemeSetu Governance & Ingestion</h1>
          <p className="text-xs text-slate-400 mt-1">
            Firecrawl web scraping · Whitelisted Source Registry · Versioned scheme rules · Complete audit trail
          </p>
        </div>
        <button
          onClick={() => { setAdminTab('scraper'); handleTriggerScraper() }}
          disabled={scraperRunning}
          className="shrink-0 px-5 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-xs flex items-center gap-2 shadow-lg shadow-amber-500/20 transition-all hover:scale-[1.02] disabled:opacity-50"
        >
          <RefreshCw size={15} className={scraperRunning ? 'animate-spin' : ''} />
          <span>{scraperRunning ? 'Scraper Running...' : 'Run Firecrawl Pipeline'}</span>
        </button>
      </div>

      {/* ── Tabs ─────────────────────────────────────────────────────────────── */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-1.5 shadow-sm flex flex-wrap items-center gap-1 text-xs font-bold text-slate-400">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setAdminTab(tab.id)}
            className={`px-4 py-2.5 rounded-lg transition-all ${
              adminTab === tab.id 
                ? 'bg-indigo-600 text-white font-extrabold shadow-md shadow-indigo-600/30' 
                : 'hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Firecrawl Pipeline ───────────────────────────────────────────── */}
      {adminTab === 'scraper' && (
        <div className="space-y-6">

          {/* Pipeline Architecture */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-3 flex items-center gap-2">
              <Database size={16} className="text-indigo-400" />
              <span>Automated Government Ingestion Pipeline Architecture</span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 text-center text-xs">
              {[
                { step: '1', title: 'Gov Source', sub: '.gov.in / .nic.in' },
                { step: '2', title: 'Domain Check', sub: 'Layer 1 whitelist' },
                { step: '3', title: 'Source Registry', sub: 'Authority check' },
                { step: '4', title: 'Firecrawl', sub: '→ httpx fallback' },
                { step: '5', title: 'PDF Routing', sub: 'text/scanned OCR' },
                { step: '6', title: 'Gemini Extract', sub: 'Evidence-backed' },
                { step: '7', title: 'Admin Review', sub: 'Manual signoff' },
                { step: '8', title: 'Versioned Rules', sub: 'Rule v2026.x' },
              ].map(node => (
                <div key={node.step} className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-1">
                  <span className="w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px] font-bold mx-auto flex items-center justify-center shadow-xs">
                    {node.step}
                  </span>
                  <p className="font-bold text-slate-200 text-[11px] mt-1">{node.title}</p>
                  <p className="text-[10px] text-slate-400">{node.sub}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Trigger Form */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Trigger Scrape Job</h3>
            <div className="space-y-3 text-xs">
              <div className="space-y-1.5">
                <label className="text-slate-300 font-bold">Government Source URL</label>
                <input
                  type="text"
                  value={scrapeUrl}
                  onChange={e => setScrapeUrl(e.target.value)}
                  className="w-full bg-slate-800/90 border border-slate-700 rounded-xl px-4 py-3 font-mono font-bold text-indigo-300 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  placeholder="https://nsfdc.nic.in/..."
                />
              </div>
              {scrapeError && (
                <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 flex items-start gap-2.5">
                  <AlertCircle size={16} className="mt-0.5 shrink-0 text-rose-400" />
                  <span>{scrapeError}</span>
                </div>
              )}
              <div className="p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-indigo-200 text-xs">
                <strong>Anti-hallucination guarantee:</strong> Only values explicitly verified in the government source text or official PDF attachments are extracted. Every candidate rule carries verbatim evidence quotes.
              </div>
              <button
                onClick={handleTriggerScraper}
                disabled={scraperRunning}
                className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.01] disabled:opacity-50"
              >
                {scraperRunning ? `Running Job ${activeJobId?.slice(0, 8)}...` : 'Start Firecrawl Ingestion'}
              </button>
            </div>
          </div>

          {/* Job List */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-md space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Scrape Jobs History</h3>
              <button onClick={fetchJobs} className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                <RefreshCw size={12} /> Refresh
              </button>
            </div>
            {jobs.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-6">No jobs yet. Trigger a scrape above.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-bold uppercase text-[10px]">
                      <th className="p-3 text-left">Job ID</th>
                      <th className="p-3 text-left">URL</th>
                      <th className="p-3 text-left">Status</th>
                      <th className="p-3 text-left">Method</th>
                      <th className="p-3 text-left">Schemes</th>
                      <th className="p-3 text-left">PDFs</th>
                      <th className="p-3 text-left">Started</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {jobs.map(job => (
                      <tr key={job.job_id} className="hover:bg-slate-800/40">
                        <td className="p-3 font-mono text-[11px] text-slate-400">{job.job_id?.slice(0, 8)}…</td>
                        <td className="p-3 max-w-[220px] truncate text-slate-200 font-medium">
                          <a href={job.url} target="_blank" rel="noreferrer" className="hover:underline hover:text-indigo-400 flex items-center gap-1">
                            {job.url?.replace('https://', '')} <ExternalLink size={10} />
                          </a>
                        </td>
                        <td className="p-3"><StatusBadge status={job.status} /></td>
                        <td className="p-3"><ExtractionBadge method={job.extraction_method} /></td>
                        <td className="p-3 font-bold text-white">{job.schemes_found ?? 0}</td>
                        <td className="p-3 text-slate-400">{job.pdfs_processed ?? 0}</td>
                        <td className="p-3 font-mono text-[10px] text-slate-500">
                          {job.started_at ? new Date(job.started_at).toLocaleTimeString() : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Tab: Scheme Registry ──────────────────────────────────────────────── */}
      {adminTab === 'schemes' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Scraped Scheme Candidates ({schemes.length})
            </h3>
            <button onClick={fetchSchemes} className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              <RefreshCw size={12} /> Refresh
            </button>
          </div>
          {schemes.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-8">No schemes scraped yet. Run a Firecrawl job first.</p>
          ) : (
            <div className="space-y-3">
              {schemes.map(scheme => (
                <div key={scheme.scheme_id} className="border border-slate-800 rounded-xl overflow-hidden bg-slate-850/50">
                  <div
                    className="p-4 flex items-center justify-between gap-3 cursor-pointer hover:bg-slate-800/50 transition-colors"
                    onClick={() => setExpandedScheme(expandedScheme === scheme.scheme_id ? null : scheme.scheme_id)}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      {expandedScheme === scheme.scheme_id ? <ChevronDown size={16} className="text-indigo-400" /> : <ChevronRight size={16} className="text-slate-500" />}
                      <div className="min-w-0">
                        <p className="font-bold text-white text-sm truncate">{scheme.name || '(Unnamed scheme)'}</p>
                        <p className="text-xs text-slate-400 truncate">{scheme.ministry || scheme.source_authority}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <ExtractionBadge method={scheme.extraction_method} />
                      <span className="text-[10px] text-slate-400 font-mono">v{scheme.version}</span>
                      <StatusBadge status={scheme.status} />
                      {scheme.status !== 'published' && scheme.status !== 'rejected' && (
                        <>
                          <button
                            onClick={e => { e.stopPropagation(); handlePublish(scheme.scheme_id) }}
                            className="px-3 py-1 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 font-bold text-[11px] border border-emerald-500/40 transition-colors"
                          >
                            Approve
                          </button>
                          <button
                            onClick={e => { e.stopPropagation(); handleReject(scheme.scheme_id) }}
                            className="px-3 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 font-bold text-[11px] border border-rose-500/40 transition-colors"
                          >
                            Reject
                          </button>
                        </>
                      )}
                      <button
                        onClick={e => { e.stopPropagation(); loadVersions(scheme.scheme_id) }}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-[11px] border border-slate-700 flex items-center gap-1 transition-colors"
                      >
                        <History size={11} /> Versions
                      </button>
                    </div>
                  </div>

                  {expandedScheme === scheme.scheme_id && (
                    <div className="border-t border-slate-800 p-4 bg-slate-900/60 space-y-3 text-xs">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div>
                          <span className="text-slate-400 font-bold">Source</span><br />
                          <a href={scheme.source_url} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline font-mono text-[11px] truncate block">
                            {scheme.source_url?.replace('https://', '')}
                          </a>
                        </div>
                        <div>
                          <span className="text-slate-400 font-bold">Rules Extracted</span><br />
                          <span className="font-bold text-white">{scheme.candidate_rules_count}</span>
                          <span className="text-slate-500 ml-1">(candidate)</span>
                        </div>
                        <div>
                          <span className="text-slate-400 font-bold">Conflicts</span><br />
                          <span className={scheme.has_conflicts ? 'text-orange-400 font-bold' : 'text-slate-500'}>
                            {scheme.has_conflicts ? '⚠ Has conflicts' : 'None'}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 font-bold">Scraped At</span><br />
                          <span className="font-mono text-[11px] text-slate-300">{scheme.scraped_at ? new Date(scheme.scraped_at).toLocaleDateString() : '—'}</span>
                        </div>
                      </div>

                      {scheme.validation_warnings?.length > 0 && (
                        <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-200">
                          <strong>Warnings:</strong> {scheme.validation_warnings.join(' · ')}
                        </div>
                      )}

                      {scheme.validation_errors?.length > 0 && (
                        <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-200">
                          <strong>Errors:</strong> {scheme.validation_errors.join(' · ')}
                        </div>
                      )}

                      {schemeVersions[scheme.scheme_id] && (
                        <div className="space-y-1.5 pt-2 border-t border-slate-800">
                          <p className="font-bold text-slate-300">Version History</p>
                          {schemeVersions[scheme.scheme_id].map(v => (
                            <div key={v.version_id} className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
                              <span className="font-bold text-white">v{v.version}</span>
                              <span>Published {new Date(v.published_at).toLocaleDateString()}</span>
                              {v.published_by && <span>by {v.published_by}</span>}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Source Registry ──────────────────────────────────────────────── */}
      {adminTab === 'sources' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Approved Source Registry</h3>
              <p className="text-xs text-slate-400 mt-0.5">Government domains must be registered AND approved before scraping is permitted.</p>
            </div>
            <button
              onClick={() => setShowSourceForm(!showSourceForm)}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-colors"
            >
              <Plus size={14} /> Register Source
            </button>
          </div>

          {showSourceForm && (
            <div className="p-4 bg-slate-800/80 border border-slate-700 rounded-xl space-y-3 text-xs">
              <h4 className="font-bold text-white">Register New Government Source</h4>
              {[
                { key: 'domain', label: 'Hostname (e.g. nsfdc.nic.in)', ph: 'nsfdc.nic.in' },
                { key: 'authority', label: 'Authority (e.g. NSFDC)', ph: 'NSFDC' },
                { key: 'display_name', label: 'Display Name', ph: 'National SC Finance & Dev Corp' },
                { key: 'base_url', label: 'Base URL', ph: 'https://nsfdc.nic.in' },
                { key: 'allowed_topics', label: 'Allowed Topics (comma-separated)', ph: 'credit schemes, education loans' },
              ].map(f => (
                <div key={f.key}>
                  <label className="text-slate-300 font-bold">{f.label}</label>
                  <input
                    type="text"
                    value={sourceForm[f.key]}
                    onChange={e => setSourceForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 mt-1 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    placeholder={f.ph}
                  />
                </div>
              ))}
              <div className="flex gap-2 pt-1">
                <button onClick={handleRegisterSource} className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs">Register</button>
                <button onClick={() => setShowSourceForm(false)} className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 font-bold text-xs">Cancel</button>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sources.length === 0 ? (
              <p className="text-xs text-slate-500 col-span-2 text-center py-6">No sources registered. Add one above.</p>
            ) : sources.map(src => (
              <div key={src.source_id} className="p-4 rounded-xl border border-slate-800 bg-slate-800/40 space-y-2 text-xs">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold text-indigo-400 uppercase">{src.source_type}</span>
                    <h4 className="font-bold text-white text-sm">{src.display_name}</h4>
                    <p className="font-mono text-slate-400">{src.domain}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold border ${src.approved ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border-amber-500/30'}`}>
                      {src.approved ? '✓ Approved' : 'Pending Approval'}
                    </span>
                    {!src.approved && (
                      <button
                        onClick={() => handleApproveSource(src.source_id)}
                        className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-bold"
                      >
                        Approve
                      </button>
                    )}
                  </div>
                </div>
                <div>
                  <span className="text-slate-400 font-bold">Authority:</span> <span className="text-slate-200">{src.authority}</span>
                </div>
                {src.allowed_topics?.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {src.allowed_topics.map(t => (
                      <span key={t} className="px-2 py-0.5 rounded-md bg-slate-700/60 text-slate-300 text-[10px] border border-slate-700">{t}</span>
                    ))}
                  </div>
                )}
                <div className="text-slate-400 font-mono text-[10px]">Priority: {src.priority}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Tab: Pending Changes ──────────────────────────────────────────────── */}
      {adminTab === 'changes' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Pending Field Changes ({changes.length})</h3>
            <button onClick={fetchChanges} className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              <RefreshCw size={12} /> Refresh
            </button>
          </div>
          {changes.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-6">No pending changes requiring review.</p>
          ) : changes.map(change => (
            <div key={change.change_id} className="border border-slate-800 rounded-xl p-4 space-y-3 text-xs bg-slate-800/40">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-indigo-300">Scheme: {change.scheme_id}</span>
                <span className="text-slate-400 font-mono">{change.old_version} → {change.new_version}</span>
              </div>
              {change.changes?.map((fc, i) => (
                <div key={i} className="p-3 bg-amber-950/20 border border-amber-500/30 rounded-lg space-y-1">
                  <p className="font-bold text-amber-300">{fc.field}</p>
                  <div className="flex gap-4">
                    <span className="text-rose-400">OLD: {String(fc.old_value)}</span>
                    <span className="text-emerald-400">NEW: {String(fc.new_value)}</span>
                  </div>
                </div>
              ))}
              {change.conflicts?.length > 0 && (
                <div className="p-3 bg-orange-950/20 border border-orange-500/30 rounded-lg">
                  <p className="font-bold text-orange-300">⚠ {change.conflicts.length} conflict(s) — officer resolution required</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── Tab: Audit Trail ─────────────────────────────────────────────────── */}
      {adminTab === 'audit-logs' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">System Audit Trail</h3>
            <button onClick={fetchAuditLogs} className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              <RefreshCw size={12} /> Refresh
            </button>
          </div>
          {auditLogs.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-6">No audit events logged yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-bold uppercase text-[10px]">
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Actor</th>
                    <th className="p-3">Action</th>
                    <th className="p-3">Target</th>
                    <th className="p-3">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium text-slate-300">
                  {auditLogs.map(log => (
                    <tr key={log.log_id} className="hover:bg-slate-800/40">
                      <td className="p-3 font-mono text-[11px] text-slate-400">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : '—'}
                      </td>
                      <td className="p-3 font-bold text-indigo-400">{log.actor}</td>
                      <td className="p-3 font-mono text-slate-200">{log.action}</td>
                      <td className="p-3 text-slate-400 font-mono text-[11px]">{log.target_id?.slice(0, 12)}…</td>
                      <td className="p-3 text-slate-400 max-w-xs truncate">
                        {log.details?.url || log.details?.scheme_name || log.details?.domain || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

    </div>
  )
}
