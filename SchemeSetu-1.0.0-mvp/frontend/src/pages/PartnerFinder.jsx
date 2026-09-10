import { useState } from 'react'
import { MapPin, Navigation, Phone, CheckCircle2, AlertCircle, ExternalLink, Filter } from 'lucide-react'
import useChatStore from '../store/chatStore'

export default function PartnerFinder() {
  const { partners, selectedScheme, userProfile, setSelectedPartner, setActiveTab } = useChatStore()
  const [sortBy, setSortBy] = useState('match') // 'match' | 'distance' | 'availability'
  const [routeModalPartner, setRouteModalPartner] = useState(null)

  const sortedPartners = [...partners].sort((a, b) => {
    if (sortBy === 'distance') {
      return parseFloat(a.distance) - parseFloat(b.distance)
    }
    if (sortBy === 'availability') {
      return (b.available ? 1 : 0) - (a.available ? 1 : 0)
    }
    return b.rating - a.rating
  })

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* ── Selection Header ─────────────────────────────────────────────── */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="text-[10px] font-extrabold text-indigo-400 uppercase tracking-wider">RECOMMENDED CHANNEL PARTNERS</span>
          <h1 className="text-xl md:text-2xl font-black text-white">Find Nearest Channelizing Agency</h1>
          <div className="flex flex-wrap items-center gap-3 text-xs pt-1">
            <span className="text-slate-400">Target Scheme: <strong className="text-indigo-300">{selectedScheme ? selectedScheme.name : 'NSFDC Term Loan'}</strong></span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400">Location: <strong className="text-indigo-300">{userProfile.district}, {userProfile.state} ({userProfile.pinCode})</strong></span>
          </div>
        </div>

        {/* Sort Filter */}
        <div className="flex items-center gap-2 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs">
          <Filter size={14} className="text-indigo-400" />
          <span className="text-slate-400">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-transparent font-bold text-white focus:outline-none cursor-pointer"
          >
            <option value="match" className="bg-slate-900">Best Match</option>
            <option value="distance" className="bg-slate-900">Distance</option>
            <option value="availability" className="bg-slate-900">Availability</option>
          </select>
        </div>
      </div>

      {/* ── Partners Cards Grid ───────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {sortedPartners.map((partner) => (
          <div
            key={partner.id}
            className="bg-slate-900/90 border border-slate-800 hover:border-indigo-500/40 rounded-2xl p-6 transition-all duration-200 flex flex-col justify-between space-y-4"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="text-[10px] font-bold text-indigo-400 uppercase">{partner.type}</span>
                  <h3 className="text-base font-bold text-white leading-snug">{partner.name}</h3>
                </div>
                <span className="shrink-0 px-2 py-1 rounded-lg bg-indigo-500/10 text-indigo-300 text-[10px] font-bold border border-indigo-500/20 flex items-center gap-1">
                  <MapPin size={12} />
                  <span>{partner.distance}</span>
                </span>
              </div>

              <p className="text-xs text-slate-400 flex items-start gap-1.5">
                <span className="shrink-0 font-medium">📍</span>
                <span>{partner.address}</span>
              </p>

              {/* Supported Features */}
              <div className="space-y-1.5 pt-2 border-t border-slate-800/80 text-xs">
                <div className="flex items-center gap-2 text-emerald-400 font-medium">
                  <CheckCircle2 size={14} className="shrink-0" />
                  <span>Scheme supported ({selectedScheme ? selectedScheme.name : 'NSFDC'})</span>
                </div>

                <div className="flex items-center justify-between">
                  <div className={`flex items-center gap-2 text-xs font-medium ${partner.available ? 'text-emerald-400' : 'text-slate-400'}`}>
                    <CheckCircle2 size={14} className="shrink-0" />
                    <span>{partner.available ? 'Applications available' : 'Fund status demo/sample'}</span>
                  </div>

                  <span className={`text-[10px] px-2 py-0.5 rounded-md font-semibold ${
                    partner.available ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                  }`}>
                    {partner.lastUpdated}
                  </span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 pt-3 border-t border-slate-800">
              <button
                onClick={() => setRouteModalPartner(partner)}
                className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-md shadow-indigo-600/20"
              >
                <Navigation size={14} />
                <span>View Route</span>
              </button>

              <button
                onClick={() => {
                  setSelectedPartner(partner)
                  setActiveTab('applications')
                }}
                className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
              >
                Apply Here
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Demo Data Notice */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 flex items-center gap-3">
        <AlertCircle size={18} className="text-amber-400 shrink-0" />
        <span>
          <strong>Sample/Demo Data Notice:</strong> Channelizing agency availability and real-time quota allocations are simulated for preview purposes. Official submissions route directly through verified SCAs.
        </span>
      </div>

      {/* Route Modal */}
      {routeModalPartner && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <MapPin size={18} className="text-indigo-400" />
                <h3 className="text-base font-bold text-white">Channel Partner Location</h3>
              </div>
              <button onClick={() => setRouteModalPartner(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <div className="space-y-3">
              <h4 className="text-sm font-bold text-white">{routeModalPartner.name}</h4>
              <p className="text-xs text-slate-300">📍 {routeModalPartner.address}</p>

              <div className="p-4 rounded-xl bg-slate-800/80 border border-slate-700 text-center space-y-2">
                <span className="text-xs text-slate-400 block">Distance from {userProfile.pinCode}:</span>
                <span className="text-2xl font-black text-indigo-400">{routeModalPartner.distance}</span>
                <p className="text-[11px] text-slate-400">Estimated travel time: 12 mins via Highway 66</p>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-indigo-950/40 border border-indigo-800/40 text-xs text-indigo-300">
                <Phone size={15} />
                <span className="font-mono font-bold">{routeModalPartner.phone}</span>
              </div>
            </div>

            <div className="pt-2 flex gap-2">
              <button
                onClick={() => setRouteModalPartner(null)}
                className="flex-1 py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
              >
                Close
              </button>
              <a
                href={`https://maps.google.com/?q=${encodeURIComponent(routeModalPartner.address)}`}
                target="_blank"
                rel="noreferrer"
                className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-1.5"
              >
                <span>Google Maps</span>
                <ExternalLink size={14} />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
