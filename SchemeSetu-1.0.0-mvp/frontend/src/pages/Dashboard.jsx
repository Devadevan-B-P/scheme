import { 
  CheckCircle2, 
  ArrowRight, 
  Calculator, 
  MapPin, 
  Award, 
  TrendingUp, 
  Sparkles, 
  ShieldAlert,
  ChevronRight
} from 'lucide-react'
import useChatStore from '../store/chatStore'

export default function Dashboard() {
  const { 
    userProfile, 
    schemes, 
    setActiveTab, 
    setSelectedScheme 
  } = useChatStore()

  const eligibleSchemes = schemes.filter(s => s.eligible)

  const handleViewScheme = (scheme) => {
    setSelectedScheme(scheme)
    setActiveTab('scheme-details')
  }

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* ── Welcome Banner ─────────────────────────────────────────────────── */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-900/60 via-slate-900 to-indigo-950/80 border border-indigo-500/30 p-6 md:p-8">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-xs font-semibold">
              <Sparkles size={14} />
              <span>AI Onboarding Completed</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Welcome, {userProfile.name}! 👋
            </h1>
            <p className="text-sm text-slate-300 max-w-xl">
              Based on your profile as an <span className="text-indigo-300 font-semibold">{userProfile.category} category</span> applicant with annual income of <span className="text-indigo-300 font-semibold">₹{(userProfile.income / 100000).toFixed(2)} Lakh</span>, we have analyzed government schemes for you.
            </p>
          </div>

          <button
            onClick={() => setActiveTab('scheme-results')}
            className="self-start md:self-center shrink-0 px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02]"
          >
            <span>View All Matched Schemes</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* ── Status Grid & Summary ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Eligibility Checklist Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Eligibility Status</h3>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-semibold border border-emerald-500/20">
              Verified
            </span>
          </div>

          <div className="space-y-3 pt-1">
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/60 border border-slate-700/50">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />
                <span className="text-xs font-medium text-slate-200">Profile completed</span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">100%</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/60 border border-slate-700/50">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />
                <span className="text-xs font-medium text-slate-200">Documents verified</span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">3 / 3</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/60 border border-slate-700/50">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />
                <span className="text-xs font-medium text-slate-200">4 schemes matched</span>
              </div>
              <span className="text-[11px] text-emerald-400 font-bold font-mono">4 Total</span>
            </div>
          </div>
        </div>

        {/* Big Stat Cards */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-indigo-950/60 via-slate-900 to-slate-900 border border-indigo-500/20 rounded-2xl p-6 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider">Total Schemes Matched</span>
              <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <Award size={20} />
              </div>
            </div>
            <div className="mt-4">
              <div className="text-3xl font-black text-white">{schemes.length} Schemes</div>
              <p className="text-xs text-slate-400 mt-1">Evaluated by deterministic rule engine</p>
            </div>
          </div>

          <div className="bg-gradient-to-br from-emerald-950/50 via-slate-900 to-slate-900 border border-emerald-500/20 rounded-2xl p-6 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-300 uppercase tracking-wider">Directly Eligible</span>
              <div className="w-10 h-10 rounded-xl bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <TrendingUp size={20} />
              </div>
            </div>
            <div className="mt-4">
              <div className="text-3xl font-black text-emerald-400">{eligibleSchemes.length} Eligible</div>
              <p className="text-xs text-slate-400 mt-1">Satisfying 100% of ministry guidelines</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Recommended for You ────────────────────────────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Recommended for You</h3>
            <p className="text-xs text-slate-400">Top government schemes matching your profile parameters</p>
          </div>
          <button 
            onClick={() => setActiveTab('scheme-results')}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
          >
            <span>View All</span>
            <ChevronRight size={14} />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {eligibleSchemes.slice(0, 2).map((scheme) => (
            <div 
              key={scheme.id}
              className="bg-slate-900/90 border border-slate-800 hover:border-indigo-500/40 rounded-2xl p-5 transition-all duration-200 flex flex-col justify-between gap-4"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">{scheme.ministry}</span>
                    <h4 className="text-base font-bold text-white mt-0.5">{scheme.name}</h4>
                  </div>
                  <span className="shrink-0 px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 text-[10px] font-bold border border-emerald-500/20">
                    Eligible ✓
                  </span>
                </div>

                <div className="mt-4 p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] text-slate-400 uppercase">Potential benefit</p>
                    <p className="text-base font-extrabold text-slate-100">{scheme.maxLoanText}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-slate-400 uppercase">Interest Rate</p>
                    <p className="text-xs font-bold text-emerald-400">{scheme.interestRate}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
                <button
                  onClick={() => handleViewScheme(scheme)}
                  className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-colors flex items-center justify-center gap-1.5"
                >
                  <span>View Scheme</span>
                  <ArrowRight size={14} />
                </button>
                <button
                  onClick={() => {
                    setSelectedScheme(scheme)
                    setActiveTab('calculator')
                  }}
                  className="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
                  title="Calculate EMI"
                >
                  <Calculator size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Quick Action Toolbar ────────────────────────────────────────── */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-bold text-slate-200">Next Recommended Steps</h4>
          <p className="text-xs text-slate-400">Calculate financial costs or locate channel partners to begin your application</p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button
            onClick={() => setActiveTab('calculator')}
            className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs flex items-center justify-center gap-2 border border-slate-700 transition-colors"
          >
            <Calculator size={16} className="text-indigo-400" />
            <span>Calculate Finance</span>
          </button>
          
          <button
            onClick={() => setActiveTab('partner-finder')}
            className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-2 transition-colors shadow-md shadow-indigo-600/20"
          >
            <MapPin size={16} />
            <span>Find Partner</span>
          </button>
        </div>
      </div>
    </div>
  )
}
