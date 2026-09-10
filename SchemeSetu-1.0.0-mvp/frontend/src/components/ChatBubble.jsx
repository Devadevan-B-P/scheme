/**
 * ChatBubble — renders a single chat message with optional data cards.
 *
 * Props:
 *   message: { id, role: 'user' | 'agent' | 'system', content, data }
 *
 * data may contain:
 *   - extracted_entities / profile_completeness_pct  → ProfileCard
 *   - eligibility_results                            → EligibilityCard
 *   - financial_summaries                            → FinancialCard
 *   - partner_list                                   → PartnerCard
 *   - ocr_result                                     → OcrConfirmation
 */
import { ShieldCheck } from 'lucide-react'
import useChatStore from '../store/chatStore'

// ── Profile Card ──────────────────────────────────────────────────────────────

const PROFILE_LABELS = {
  age: 'Age',
  gender: 'Gender',
  category: 'Category',
  annual_income: 'Annual Income (₹)',
  loan_required: 'Loan Required (₹)',
  project_cost: 'Project Cost (₹)',
  education_level: 'Education',
  business_type: 'Business Type',
  disability_status: 'Disability',
  state: 'State',
  location: 'Location',
}

function ProfileCard({ entities, completeness }) {
  if (!entities || Object.keys(entities).length === 0) return null

  const entries = Object.entries(entities)
    .filter(([key]) => PROFILE_LABELS[key])
    .map(([key, value]) => ({ key, label: PROFILE_LABELS[key], value }))

  if (entries.length === 0) return null

  return (
    <div className="mt-3 rounded-xl border border-slate-700 bg-slate-800/60 p-3 text-xs">
      <p className="mb-2 font-semibold text-slate-300 uppercase tracking-wide text-[10px]">
        Profile — {completeness ?? 0}% complete
      </p>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        {entries.map(({ key, label, value }) => (
          <div key={key} className="flex justify-between gap-2">
            <span className="text-slate-400 truncate">{label}</span>
            <span className="text-slate-200 font-medium capitalize">
              {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Eligibility Card ──────────────────────────────────────────────────────────

function EligibilityCard({ results }) {
  if (!results || results.length === 0) return null

  return (
    <div className="mt-2 space-y-2">
      {results.map((result) => {
        const isEligible = result.decision === 'eligible'
        const isMissing = result.decision === 'missing_information'

        return (
          <div
            key={result.scheme_id}
            className={`rounded-xl border p-3 text-xs ${
              isEligible
                ? 'border-emerald-700/60 bg-emerald-900/20'
                : isMissing
                ? 'border-amber-700/40 bg-amber-900/10'
                : 'border-red-800/40 bg-red-900/10'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-slate-200">{result.scheme_id}</span>
              <span
                className={`px-2 py-0.5 rounded-full font-semibold text-[10px] ${
                  isEligible
                    ? 'bg-emerald-800 text-emerald-200'
                    : isMissing
                    ? 'bg-amber-800 text-amber-200'
                    : 'bg-red-900 text-red-300'
                }`}
              >
                {isEligible ? '✓ Eligible' : isMissing ? '? More Info Needed' : '✗ Not Eligible'}
              </span>
            </div>

            {/* Match score */}
            {result.match_score !== undefined && (
              <div className="flex items-center gap-2 mt-1">
                <span className="text-slate-400 shrink-0">Match</span>
                <div className="flex-1 bg-slate-700 rounded-full h-1.5">
                  <div
                    className="h-1.5 rounded-full bg-indigo-500"
                    style={{ width: `${Math.round(result.match_score * 100)}%` }}
                  />
                </div>
                <span className="text-slate-300 shrink-0">
                  {Math.round(result.match_score * 100)}%
                </span>
              </div>
            )}

            {/* Failed rules */}
            {result.failed_rules?.length > 0 && (
              <ul className="mt-2 space-y-0.5">
                {result.failed_rules.map((r, i) => (
                  <li key={i} className="text-red-400 flex gap-1 text-[11px]">
                    <span>·</span>
                    <span>{r.explanation || r.rule_name || JSON.stringify(r)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── Financial Summaries Card ──────────────────────────────────────────────────

function FinancialCard({ summaries }) {
  if (!summaries || summaries.length === 0) return null

  return (
    <div className="mt-2 space-y-2">
      {summaries.map((fin, i) => (
        <div key={i} className="rounded-xl border border-indigo-700/40 bg-indigo-900/10 p-3 text-xs">
          <p className="font-semibold text-indigo-300 mb-2 text-[10px] uppercase tracking-wide">
            Financial Summary — {fin.scheme_id}
          </p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {fin.max_loan_amount && (
              <div className="flex justify-between"><span className="text-slate-400">Max Loan</span><span className="text-slate-200">₹{Number(fin.max_loan_amount).toLocaleString('en-IN')}</span></div>
            )}
            {fin.interest_rate && (
              <div className="flex justify-between"><span className="text-slate-400">Interest Rate</span><span className="text-slate-200">{fin.interest_rate}% p.a.</span></div>
            )}
            {fin.repayment_years && (
              <div className="flex justify-between"><span className="text-slate-400">Repayment</span><span className="text-slate-200">{fin.repayment_years} years</span></div>
            )}
            {fin.moratorium_months && (
              <div className="flex justify-between"><span className="text-slate-400">Moratorium</span><span className="text-slate-200">{fin.moratorium_months} months</span></div>
            )}
            {fin.emi_after_moratorium && (
              <div className="flex justify-between"><span className="text-slate-400">EMI</span><span className="text-emerald-400 font-semibold">₹{Number(fin.emi_after_moratorium).toLocaleString('en-IN')}/mo</span></div>
            )}
            {fin.margin_money && (
              <div className="flex justify-between"><span className="text-slate-400">Margin Money</span><span className="text-slate-200">₹{Number(fin.margin_money).toLocaleString('en-IN')}</span></div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Partner List Card ─────────────────────────────────────────────────────────

function PartnerCard({ partners }) {
  if (!partners || partners.length === 0) return null

  return (
    <div className="mt-2 space-y-2">
      <p className="font-semibold text-slate-300 uppercase tracking-wide text-[10px]">
        Nearest Channel Partners
      </p>
      {partners.map((p, i) => (
        <div key={i} className="rounded-xl border border-slate-700 bg-slate-800/60 p-3 text-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold text-slate-200">{p.name}</span>
            <span className="text-slate-400 text-[10px]">{p.distance_km?.toFixed(1)} km</span>
          </div>
          <p className="text-slate-400">{p.type} · {p.address}</p>
          {p.phone && <p className="text-indigo-400 mt-0.5">{p.phone}</p>}
        </div>
      ))}
    </div>
  )
}

// ── OCR Confirmation Card ─────────────────────────────────────────────────────

function OcrConfirmationCard({ ocrResult }) {
  if (!ocrResult || !ocrResult.extracted_fields) return null

  const { confirmOcrFields, dismissOcrConfirmation } = useChatStore.getState()
  const fields = ocrResult.extracted_fields

  const getConfidenceColor = (conf) => {
    if (conf >= 0.85) return 'text-emerald-400'
    if (conf >= 0.6) return 'text-amber-400'
    return 'text-red-400'
  }

  const handleConfirm = () => {
    const confirmedFields = {}
    for (const [key, field] of Object.entries(fields)) {
      confirmedFields[key] = field.extracted_value
    }
    confirmOcrFields(confirmedFields)
  }

  return (
    <div className="mt-3 rounded-xl border border-amber-700/40 bg-amber-900/10 p-3 text-xs">
      <p className="font-semibold text-amber-300 mb-2 text-[10px] uppercase tracking-wide flex items-center gap-1">
        <ShieldCheck size={12} />
        Document Extraction — Pending Confirmation
      </p>
      <div className="space-y-1.5">
        {Object.entries(fields).map(([key, field]) => (
          <div key={key} className="flex items-center justify-between gap-2">
            <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
            <div className="flex items-center gap-2">
              <span className="text-slate-200 font-medium">
                {key.includes('income') ? `₹${Number(field.extracted_value).toLocaleString('en-IN')}` : field.extracted_value}
              </span>
              <span className={`text-[10px] font-mono ${getConfidenceColor(field.extraction_confidence)}`}>
                {Math.round(field.extraction_confidence * 100)}%
              </span>
            </div>
          </div>
        ))}
      </div>
      <div className="flex gap-2 mt-3">
        <button
          onClick={handleConfirm}
          className="flex-1 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors"
        >
          ✓ Confirm
        </button>
        <button
          onClick={dismissOcrConfirmation}
          className="flex-1 px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-semibold transition-colors"
        >
          ✗ Reject
        </button>
      </div>
    </div>
  )
}

// ── Main ChatBubble ───────────────────────────────────────────────────────────

export default function ChatBubble({ message }) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <span className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-1.5">
          {message.content}
        </span>
      </div>
    )
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="shrink-0 w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-white text-[10px] font-bold mr-2 mt-1">
          AI
        </div>
      )}

      <div className={`max-w-[78%] ${isUser ? 'max-w-[65%]' : ''}`}>
        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? 'bg-indigo-600 text-white rounded-br-sm'
              : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-sm'
          }`}
        >
          {message.content}
        </div>

        {/* Data cards (agent only) */}
        {!isUser && message.data && (
          <div className="mt-1 px-1">
            <ProfileCard
              entities={message.data.extracted_entities}
              completeness={message.data.profile_completeness_pct}
            />
            <EligibilityCard results={message.data.eligibility_results} />
            <FinancialCard summaries={message.data.financial_summaries} />
            <PartnerCard partners={message.data.partner_list} />
            <OcrConfirmationCard ocrResult={message.data.ocr_result} />
          </div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="shrink-0 w-7 h-7 rounded-full bg-slate-600 flex items-center justify-center text-white text-[10px] font-bold ml-2 mt-1">
          You
        </div>
      )}
    </div>
  )
}
