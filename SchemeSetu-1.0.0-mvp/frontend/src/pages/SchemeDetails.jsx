import { 
  Building2, 
  Coins, 
  CheckCircle2, 
  Circle, 
  Calculator, 
  MapPin, 
  FileCheck, 
  ArrowLeft,
  ChevronRight,
  ShieldCheck
} from 'lucide-react'
import useChatStore from '../store/chatStore'

export default function SchemeDetails() {
  const { selectedScheme, setActiveTab, setSelectedPartner, userProfile } = useChatStore()

  if (!selectedScheme) {
    return (
      <div className="p-8 text-center text-slate-400 space-y-4">
        <p>No scheme selected.</p>
        <button
          onClick={() => setActiveTab('scheme-results')}
          className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold"
        >
          View Matched Schemes
        </button>
      </div>
    )
  }

  const handleCalculate = () => {
    setActiveTab('calculator')
  }

  const handleFindPartner = () => {
    setActiveTab('partner-finder')
  }

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => setActiveTab('scheme-results')}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft size={16} />
        <span>Back to Scheme Results</span>
      </button>

      {/* ── Header Banner ────────────────────────────────────────────────── */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">{selectedScheme.ministry}</span>
            <h1 className="text-2xl md:text-3xl font-black text-white">{selectedScheme.name}</h1>
            <p className="text-xs md:text-sm text-slate-300 max-w-3xl">{selectedScheme.purpose}</p>
          </div>

          <div className="shrink-0 flex flex-col items-start md:items-end gap-2">
            <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-bold border border-emerald-500/30 flex items-center gap-1.5">
              <ShieldCheck size={14} />
              <span>Verified Eligible</span>
            </span>
            <span className="text-[11px] text-slate-400 font-mono">Code: {selectedScheme.id.toUpperCase()}</span>
          </div>
        </div>

        {/* Quick Buttons */}
        <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-slate-800">
          <button
            onClick={handleCalculate}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-2 transition-colors shadow-lg shadow-indigo-600/20"
          >
            <Calculator size={16} />
            <span>Calculate Loan</span>
          </button>
          
          <button
            onClick={handleFindPartner}
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs flex items-center gap-2 border border-slate-700 transition-colors"
          >
            <MapPin size={16} className="text-indigo-400" />
            <span>Find Nearest Partner</span>
          </button>
        </div>
      </div>

      {/* ── Main 2-Column Grid ───────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Financial Benefits & Target Beneficiaries */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Financial Benefits Box */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-indigo-400">
              <Coins size={20} />
              <h3 className="text-base font-bold text-white">Financial Benefits</h3>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2">
              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/50 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Maximum Loan</span>
                <p className="text-base font-black text-emerald-400">{selectedScheme.maxLoanText}</p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/50 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Interest Rate</span>
                <p className="text-base font-black text-slate-100">{selectedScheme.interestRate}</p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/50 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Moratorium</span>
                <p className="text-base font-black text-slate-100">{selectedScheme.moratorium}</p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/50 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Repayment Period</span>
                <p className="text-base font-black text-slate-100">{selectedScheme.repaymentPeriod}</p>
              </div>

              <div className="col-span-2 p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-800/40 space-y-1">
                <span className="text-[10px] text-indigo-300 uppercase font-semibold">Subsidy / Margin Money</span>
                <p className="text-xs font-bold text-indigo-200">{selectedScheme.subsidy}</p>
              </div>
            </div>
          </div>

          {/* Scheme Criteria & Eligibility Breakdown */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Eligibility Criteria Match</h3>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 text-xs">
                <span className="text-slate-400">Category Requirement:</span>
                <span className="font-semibold text-emerald-400 flex items-center gap-1">
                  <span>✓ {userProfile.category} Verified</span>
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 text-xs">
                <span className="text-slate-400">Income Limit:</span>
                <span className="font-semibold text-emerald-400 flex items-center gap-1">
                  <span>✓ Annual Income ₹{(userProfile.income/100000).toFixed(2)}L ≤ ₹3.00L Limit</span>
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 text-xs">
                <span className="text-slate-400">Age Bracket:</span>
                <span className="font-semibold text-emerald-400 flex items-center gap-1">
                  <span>✓ Age {userProfile.age} Satisfies 18-50 Years</span>
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 text-xs">
                <span className="text-slate-400">Business Activity:</span>
                <span className="font-semibold text-emerald-400 flex items-center gap-1">
                  <span>✓ {userProfile.businessType} Eligible</span>
                </span>
              </div>
            </div>
          </div>

          {/* Application Journey Timeline */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Application Journey</h3>

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 relative pt-2">
              {[
                { step: '1', label: 'Profile', active: true },
                { step: '2', label: 'Documents', active: true },
                { step: '3', label: 'Partner', active: true },
                { step: '4', label: 'Application', active: true },
                { step: '5', label: 'Approval', active: false },
              ].map((item, idx, arr) => (
                <div key={item.step} className="flex items-center gap-3 sm:flex-col sm:items-center text-center flex-1">
                  <div 
                    className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold z-10 ${
                      item.active 
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 ring-4 ring-indigo-950' 
                        : 'bg-slate-800 text-slate-500 border border-slate-700'
                    }`}
                  >
                    {item.step}
                  </div>
                  <span className={`text-xs font-medium ${item.active ? 'text-slate-100' : 'text-slate-500'}`}>
                    {item.label}
                  </span>
                  {idx < arr.length - 1 && (
                    <div className="hidden sm:block absolute top-6 h-0.5 bg-slate-800 -z-0" style={{ left: `${(idx + 0.5) * 20}%`, width: '15%' }} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 1 Col: Required Documents Status */}
        <div className="space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-indigo-400">
              <FileCheck size={20} />
              <h3 className="text-base font-bold text-white">Required Documents</h3>
            </div>

            <div className="space-y-3">
              {selectedScheme.documentsNeeded.map((docName, idx) => {
                const isReady = idx < 3
                return (
                  <div 
                    key={docName}
                    className={`p-3 rounded-xl border text-xs flex items-center justify-between ${
                      isReady 
                        ? 'bg-slate-800/70 border-slate-700 text-slate-200' 
                        : 'bg-slate-900 border-slate-800 text-slate-400'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      {isReady ? (
                        <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
                      ) : (
                        <Circle size={16} className="text-slate-500 shrink-0" />
                      )}
                      <span className="font-medium">{docName}</span>
                    </div>

                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                      isReady ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {isReady ? 'Ready ✓' : 'Pending'}
                    </span>
                  </div>
                )
              })}
            </div>

            <button
              onClick={() => setActiveTab('documents')}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-300 font-bold text-xs border border-slate-700 transition-colors"
            >
              Manage / Upload Documents →
            </button>
          </div>
        </div>

      </div>
    </div>
  )
}
