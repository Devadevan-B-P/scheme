/**
 * SchemeSetu API Client
 *
 * Single source of truth for all backend communication.
 * Base URL defaults to local dev server; override with VITE_API_URL.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const HEALTH_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL.replace('/api/v1', '')}/health`
  : 'http://localhost:8000/health'

// ── Health ───────────────────────────────────────────────────────────────────

export async function checkHealth() {
  const res = await fetch(HEALTH_URL)
  if (!res.ok) throw new Error('Health check failed')
  return res.json()
}

// ── Chat ─────────────────────────────────────────────────────────────────────

export async function sendChatMessage(message, sessionId = null, language = 'en') {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      language,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Network error' }))
    throw new Error(err.detail || 'Chat request failed')
  }
  return res.json()
}

// ── Document Upload (PaddleOCR) ──────────────────────────────────────────────

export async function uploadDocument(file, sessionId, language = 'en') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('session_id', sessionId)
  formData.append('language', language)

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(err.detail || 'Document upload failed')
  }
  return res.json()
}

// ── OCR Confirmation ─────────────────────────────────────────────────────────

export async function confirmOcr(confirmationToken, sessionId, confirmedFields) {
  const res = await fetch(`${API_BASE}/documents/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      confirmation_token: confirmationToken,
      session_id: sessionId,
      confirmed_fields: confirmedFields,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Confirmation failed' }))
    throw new Error(err.detail || 'OCR confirmation failed')
  }
  return res.json()
}

// ── Eligibility ──────────────────────────────────────────────────────────────

export async function checkEligibility(userProfile) {
  const res = await fetch(`${API_BASE}/eligibility/check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userProfile),
  })
  if (!res.ok) throw new Error('Eligibility check failed')
  return res.json()
}

// ── Financial Simulation ─────────────────────────────────────────────────────

export async function simulateFinancials(schemeId, loanAmount) {
  const res = await fetch(`${API_BASE}/financial/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scheme_id: schemeId, loan_amount: loanAmount }),
  })
  if (!res.ok) throw new Error('Financial simulation failed')
  return res.json()
}

// ── Partners ─────────────────────────────────────────────────────────────────

export async function getNearestPartners(lat, lng, schemeId = null, limit = 5) {
  const params = new URLSearchParams({
    lat: lat.toString(),
    lng: lng.toString(),
    limit: limit.toString(),
  })
  if (schemeId) params.append('scheme_id', schemeId)

  const res = await fetch(`${API_BASE}/partners/nearest?${params.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch nearest partners')
  return res.json()
}

// ── Schemes ──────────────────────────────────────────────────────────────────

export async function getSchemes() {
  const res = await fetch(`${API_BASE}/schemes`)
  if (!res.ok) throw new Error('Failed to fetch schemes')
  return res.json()
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function login(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Login failed' }))
    throw new Error(err.detail || 'Login failed')
  }
  return res.json()
}

export async function signup(signupData) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(signupData),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Registration failed' }))
    throw new Error(err.detail || 'Registration failed')
  }
  return res.json()
}

export async function getUserProfile(userId) {
  const res = await fetch(`${API_BASE}/auth/profile/${userId}`)
  if (!res.ok) throw new Error('Failed to fetch user profile')
  return res.json()
}

export async function updateUserProfile(userId, data) {
  const res = await fetch(`${API_BASE}/auth/profile/${userId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to update user profile')
  return res.json()
}

// ── Admin Scraper & Ingestion Pipeline ───────────────────────────────────────

const ADMIN_BASE = API_BASE.includes('/api/v1')
  ? API_BASE.replace('/api/v1', '/api/admin')
  : `${API_BASE}/admin`

export async function triggerScrape(url, actor = 'admin') {
  const res = await fetch(`${ADMIN_BASE}/scraper/scrape`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, actor }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Scrape trigger failed' }))
    throw new Error(err.detail || 'Scrape trigger failed')
  }
  return res.json()
}

export async function getScraperJobs() {
  const res = await fetch(`${ADMIN_BASE}/scraper/jobs`)
  if (!res.ok) throw new Error('Failed to fetch scraper jobs')
  return res.json()
}

export async function getScraperJob(jobId) {
  const res = await fetch(`${ADMIN_BASE}/scraper/jobs/${jobId}`)
  if (!res.ok) throw new Error(`Failed to fetch job ${jobId}`)
  return res.json()
}

export async function getScrapedSchemes() {
  const res = await fetch(`${ADMIN_BASE}/scraper/schemes`)
  if (!res.ok) throw new Error('Failed to fetch scraped schemes')
  return res.json()
}

export async function getScrapedScheme(schemeId) {
  const res = await fetch(`${ADMIN_BASE}/scraper/schemes/${schemeId}`)
  if (!res.ok) throw new Error(`Failed to fetch scheme ${schemeId}`)
  return res.json()
}

export async function getSchemeVersions(schemeId) {
  const res = await fetch(`${ADMIN_BASE}/scraper/schemes/${schemeId}/versions`)
  if (!res.ok) throw new Error(`Failed to fetch versions for ${schemeId}`)
  return res.json()
}

export async function publishScrapedScheme(schemeId, actor = 'admin') {
  const res = await fetch(`${ADMIN_BASE}/scraper/schemes/${schemeId}/publish`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Publish failed' }))
    throw new Error(err.detail || 'Publish failed')
  }
  return res.json()
}

export async function rejectScrapedScheme(schemeId, reason, actor = 'admin') {
  const res = await fetch(`${ADMIN_BASE}/scraper/schemes/${schemeId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason, actor }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Rejection failed' }))
    throw new Error(err.detail || 'Rejection failed')
  }
  return res.json()
}

export async function getSources() {
  const res = await fetch(`${ADMIN_BASE}/sources`)
  if (!res.ok) throw new Error('Failed to fetch scheme sources')
  return res.json()
}

export async function createSource(sourceData) {
  const res = await fetch(`${ADMIN_BASE}/sources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sourceData),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Source creation failed' }))
    throw new Error(err.detail || 'Source creation failed')
  }
  return res.json()
}

export async function approveSource(sourceId) {
  const res = await fetch(`${ADMIN_BASE}/sources/${sourceId}/approve`, {
    method: 'PATCH',
  })
  if (!res.ok) throw new Error('Failed to approve source')
  return res.json()
}

export async function getScraperChanges() {
  const res = await fetch(`${ADMIN_BASE}/scraper/changes`)
  if (!res.ok) throw new Error('Failed to fetch scraper changes')
  return res.json()
}

export async function getAuditLogs() {
  const res = await fetch(`${ADMIN_BASE}/scraper/audit-logs`)
  if (!res.ok) throw new Error('Failed to fetch audit logs')
  return res.json()
}

