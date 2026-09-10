import { useState } from 'react'
import { 
  CheckCircle2, 
  XCircle, 
  ArrowRight, 
  HelpCircle, 
  Info, 
  ShieldCheck, 
  AlertTriangle,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import useChatStore from '../store/chatStore'

export default function SchemeResults() {
  const { userProfile, schemes, setSelectedScheme, setActiveTab } = useChatStore()
  const [whyModalScheme, setWhyModalScheme] = useState(null)

  const handleViewScheme = (scheme) => {
    setSelectedScheme(scheme)
    setActiveTab('scheme-details')
  }

  const eligibleSchemes = schemes.filter((s) => s.eligible)
  const ineligibleSchemes = schemes.filter((s) => !s.eligible)

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* ── Match Summary Header ─────────────────────────────────────────── */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="text-[10px] font-extrabold text-indigo-400 uppercase tracking-wider">Deterministic Engine Output</span>
            <h1 className="text-xl md:text-2xl font-black text-white">YOUR MATCHED SCHEMES</h1>
          </div>
          <span className="self-start sm:self-center px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold">
            Rule Engine Evaluation v1.4
          </span>
        </div>

        {/* Profile Criteria Badge Strip */}
        <div className="pt-2 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-400">Based on your profile:</span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 font-medium border border-slate-700">
            Category: <strong className="text-indigo-300">{userProfile.category}</strong>
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 font-medium border border-slate-700">
            Income: <strong className="text-indigo-300">₹{(userProfile.income / 100000).toFixed(2)} Lakh</strong>
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 font-medium border border-slate-700">
            Sector: <strong className="text-indigo-300">{userProfile.businessType}</strong>
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 font-medium border border-slate-700">
            Age: <strong className="text-indigo-300">{userProfile.age} Years</strong>
          </span>
        </div>
      </div>

      {/* ── Eligible Schemes Section ────────────────────────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <CheckCircle2 size={20} className="text-emerald-400" />
          <h2 className="text-lg font-bold text-white">Eligible Schemes ({eligibleSchemes.length})</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {eligibleSchemes.map((scheme) => (
            <div
              key={scheme.id}
              className="bg-slate-900/90 border border-emerald-500/30 hover:border-emerald-500/50 rounded-2xl p-6 transition-all shadow-lg shadow-emerald-950/10 flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase">{scheme.ministry}</span>
                    <h3 className="text-lg font-bold text-white">{scheme.name}</h3>
                  </div>
                  <span className="shrink-0 px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 text-xs font-bold border border-emerald-500/40 flex items-center gap-1">
                    <span>Eligible</span>
                    <span>✓</span>
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Loan Facility:</span>
                  <span className="font-extrabold text-white text-sm">{scheme.maxLoanText}</span>
                </div>

                {/* Rules Checklist */}
                <div className="space-y-1.5 pt-1">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase">Satisfied Rule Checkpoints:</p>
                  {scheme.matchedRules.map((rule, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                      <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
                      <span>{rule}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-3 border-t border-slate-800">
                <button
                  onClick={() => setWhyModalScheme(scheme)}
                  className="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <HelpCircle size={14} className="text-indigo-400" />
                  <span>Why am I eligible?</span>
                </button>
                <button
                  onClick={() => handleViewScheme(scheme)}
                  className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-md shadow-indigo-600/20"
                >
                  <span>View Scheme</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Ineligible Schemes Section ──────────────────────────────────── */}
      <div className="space-y-4 pt-4">
        <div className="flex items-center gap-2">
          <XCircle size={20} className="text-rose-400" />
          <h2 className="text-lg font-bold text-white">Ineligible Schemes ({ineligibleSchemes.length})</h2>
          <span className="text-xs text-slate-500">(Showing exact failed rules)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {ineligibleSchemes.map((scheme) => (
            <div
              key={scheme.id}
              className="bg-slate-900/80 border border-rose-500/30 rounded-2xl p-6 space-y-4 opacity-95"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase">{scheme.ministry}</span>
                  <h3 className="text-base font-bold text-slate-200">{scheme.name}</h3>
                </div>
                <span className="shrink-0 px-2.5 py-1 rounded-lg bg-rose-500/20 text-rose-300 text-xs font-bold border border-rose-500/40 flex items-center gap-1">
                  <span>Not Eligible</span>
                  <span>❌</span>
                </span>
              </div>

              {/* Exact Failed Rules Callout */}
              <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/40 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-rose-300">
                  <AlertTriangle size={15} className="text-rose-400 shrink-0" />
                  <span>Rule Engine Rejection Criteria:</span>
                </div>

                {scheme.failedRules.map((failed, idx) => (
                  <div key={idx} className="space-y-1 pl-2 border-l-2 border-rose-500/50 text-xs">
                    <p className="font-semibold text-rose-200">❌ {failed.rule}</p>
                    <div className="text-[11px] text-slate-400 grid grid-cols-1 gap-0.5 pl-2">
                      <span>Required: <strong className="text-slate-300">{failed.required}</strong></span>
                      <span>Your Profile: <strong className="text-rose-300">{failed.actual}</strong></span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-2 flex items-center justify-between text-xs text-slate-500">
                <span>Rule Engine Code: REJ_LIMIT_EXCEEDED</span>
                <button
                  onClick={() => handleViewScheme(scheme)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                >
                  View Requirements →
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── "Why Am I Eligible?" Modal ────────────────────────────────────── */}
      {whyModalScheme && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldCheck size={20} className="text-emerald-400" />
                <h3 className="text-base font-bold text-white">Rule Verification Breakdown</h3>
              </div>
              <button
                onClick={() => setWhyModalScheme(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <h4 className="text-sm font-bold text-indigo-300">{whyModalScheme.name}</h4>
              <p className="text-xs text-slate-300">
                The SchemeSetu deterministic rule engine verified your profile against the official government notification guidelines.
              </p>

              <div className="space-y-2 pt-2">
                {whyModalScheme.matchedRules.map((rule, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-start gap-2.5 text-xs text-slate-200">
                    <CheckCircle2 size={16} className="text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-slate-100">{rule}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">Matched from extracted profile attributes</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setWhyModalScheme(null)}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
