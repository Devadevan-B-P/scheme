import { CheckCircle2, Clock, FileText, Building2, AlertCircle } from 'lucide-react'
import useChatStore from '../store/chatStore'

export default function Applications() {
  const { activeApplication, selectedPartner, selectedScheme, documents } = useChatStore()

  const app = activeApplication

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold mb-2">
            <Clock size={14} />
            <span>Live Status: {app.currentStatus}</span>
          </div>
          <h1 className="text-xl md:text-2xl font-black text-white">APPLICATION #{app.applicationId}</h1>
          <p className="text-xs text-slate-400">
            Track your scheme submission through official state channelizing agencies & bank partners.
          </p>
        </div>

        <div className="shrink-0 p-3 rounded-xl bg-slate-800/80 border border-slate-700 text-right text-xs">
          <span className="text-slate-400 block">Submitted On:</span>
          <span className="font-bold text-white font-mono">{app.submissionDate}</span>
        </div>
      </div>

      {/* Stepper Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-6">
        <h3 className="text-base font-bold text-white">Application Journey Lifecycle</h3>

        {/* Stepper Timeline */}
        <div className="relative pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-7 gap-4">
            {app.steps.map((step, idx) => {
              const isCompleted = step.status === 'completed'
              const isCurrent = step.status === 'current'

              return (
                <div
                  key={step.title}
                  className={`p-4 rounded-xl border flex flex-col justify-between space-y-2 relative transition-all ${
                    isCompleted
                      ? 'bg-slate-800/80 border-slate-700 text-slate-200'
                      : isCurrent
                      ? 'bg-indigo-950/60 border-indigo-500/60 text-white ring-2 ring-indigo-500/30'
                      : 'bg-slate-900 border-slate-800 text-slate-500 opacity-60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      isCompleted 
                        ? 'bg-emerald-500 text-slate-950' 
                        : isCurrent 
                        ? 'bg-indigo-600 text-white animate-pulse' 
                        : 'bg-slate-800 text-slate-500'
                    }`}>
                      {isCompleted ? '✓' : idx + 1}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">{step.date}</span>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold">{step.title}</h4>
                    <p className="text-[10px] text-slate-400 capitalize mt-0.5">{step.status}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Application Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Metadata Panel */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3">Application Metadata</h3>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between p-3 rounded-xl bg-slate-800/60 border border-slate-700/50">
              <span className="text-slate-400">Application Reference ID:</span>
              <span className="font-mono font-bold text-indigo-400">{app.applicationId}</span>
            </div>

            <div className="flex justify-between p-3 rounded-xl bg-slate-800/60 border border-slate-700/50">
              <span className="text-slate-400">Scheme Name:</span>
              <span className="font-bold text-white">{selectedScheme ? selectedScheme.name : app.schemeName}</span>
            </div>

            <div className="flex justify-between p-3 rounded-xl bg-slate-800/60 border border-slate-700/50">
              <span className="text-slate-400">Assigned Channel Partner:</span>
              <span className="font-bold text-white text-right max-w-[200px]">{selectedPartner ? selectedPartner.name : app.partnerName}</span>
            </div>

            <div className="flex justify-between p-3 rounded-xl bg-indigo-950/30 border border-indigo-800/40">
              <span className="text-indigo-300 font-semibold">Action Required by Applicant:</span>
              <span className="font-bold text-indigo-200">{app.requiredAction}</span>
            </div>
          </div>
        </div>

        {/* Attached Documents Panel */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3">Attached Documents ({documents.length})</h3>

          <div className="space-y-2.5">
            {documents.map((doc) => (
              <div key={doc.id} className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/50 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <FileText size={16} className="text-indigo-400" />
                  <span className="font-semibold text-slate-200">{doc.name}</span>
                </div>
                <span className="text-[10px] font-bold text-emerald-400 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20">
                  Verified ✓
                </span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
