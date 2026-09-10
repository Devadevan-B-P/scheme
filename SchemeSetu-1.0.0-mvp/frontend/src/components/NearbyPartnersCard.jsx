import { useState } from 'react'
import { MapPin, Navigation, Phone, CheckCircle2, ExternalLink, Building2, ChevronRight } from 'lucide-react'
import useChatStore from '../store/chatStore'
import { getNearbyPartnersForScheme } from '../utils/partnerUtils'

export default function NearbyPartnersCard({ scheme, limit = null, showHeader = true, compact = false }) {
  const { partners, userProfile, setSelectedPartner, setSelectedScheme, setActiveTab } = useChatStore()
  const [routeModalPartner, setRouteModalPartner] = useState(null)

  const nearbyPartners = getNearbyPartnersForScheme(partners, scheme, userProfile)
  const displayPartners = limit ? nearbyPartners.slice(0, limit) : nearbyPartners

  const userLocationLabel = userProfile.district
    ? `${userProfile.district}${userProfile.pinCode ? ` (${userProfile.pinCode})` : ''}`
    : 'Your Location'

  const handleApplyWithPartner = (partner) => {
    if (scheme) {
      setSelectedScheme?.(scheme)
    }
    setSelectedPartner?.(partner)
    setActiveTab('applications')
  }

  const handleViewAllPartners = () => {
    if (scheme) {
      setSelectedScheme?.(scheme)
    }
    setActiveTab('partner-finder')
  }

  if (displayPartners.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 text-xs text-slate-400 text-center">
        No specific channel partner found for this scheme near {userLocationLabel}.
      </div>
    )
  }

  if (compact) {
    return (
      <div className="space-y-2.5 pt-2 border-t border-slate-800">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-slate-200 flex items-center gap-1">
            <MapPin size={13} className="text-indigo-400 shrink-0" />
            <span>Nearby Authorized Partners ({nearbyPartners.length})</span>
          </span>
          <button
            onClick={handleViewAllPartners}
            className="text-[11px] font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-0.5"
          >
            <span>View All</span>
            <ChevronRight size={12} />
          </button>
        </div>

        <div className="space-y-2">
          {displayPartners.map((partner) => (
            <div
              key={partner.partner_id || partner.id}
              className="p-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-900 border border-slate-800 flex items-center justify-between gap-3 text-xs transition-colors"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <h4 className="font-bold text-slate-100 truncate">{partner.name}</h4>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-950/60 text-indigo-300 font-semibold border border-indigo-800/50">
                    {partner.calculatedDistanceText || partner.distance_formatted || partner.distance}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 truncate mt-0.5">📍 {partner.address}</p>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={() => setRouteModalPartner(partner)}
                  className="p-1.5 rounded-md bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-200 transition-colors"
                  title="View Directions"
                >
                  <Navigation size={13} />
                </button>
                <button
                  onClick={() => handleApplyWithPartner(partner)}
                  className="px-2.5 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[11px] transition-colors"
                >
                  Select
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Directions Modal */}
        {routeModalPartner && (
          <DirectionsModal partner={routeModalPartner} onClose={() => setRouteModalPartner(null)} />
        )}
      </div>
    )
  }

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xs space-y-4">
      {showHeader && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-indigo-950/60 border border-indigo-800/50 text-indigo-300 text-[11px] font-bold mb-1">
              <Building2 size={12} />
              <span>Public Channelizing Network</span>
            </div>
            <h3 className="text-base font-bold text-white">
              Nearby Authorized Partners & Channelizers
            </h3>
            <p className="text-xs text-slate-400">
              Showing partner centers near <strong className="text-slate-200">{userLocationLabel}</strong> supporting{' '}
              <span className="text-indigo-400 font-semibold">{scheme?.name || 'this scheme'}</span>.
            </p>
          </div>

          <button
            onClick={handleViewAllPartners}
            className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 self-start sm:self-auto"
          >
            <span>Full Partner Map</span>
            <ChevronRight size={14} />
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {displayPartners.map((partner) => (
          <div
            key={partner.partner_id || partner.id}
            className="p-4 rounded-xl bg-slate-900/50 hover:bg-slate-800/60 border border-slate-800 flex flex-col justify-between space-y-3 transition-colors"
          >
            <div className="space-y-1.5">
              <div className="flex items-start justify-between gap-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  {partner.type}
                </span>
                <span className="px-2 py-0.5 rounded-md bg-indigo-950/80 text-indigo-300 text-xs font-extrabold flex items-center gap-1 border border-indigo-800/60 shrink-0">
                  <MapPin size={12} className="text-indigo-400" />
                  <span>{partner.calculatedDistanceText || partner.distance_formatted || partner.distance}</span>
                </span>
              </div>

              <h4 className="text-sm font-bold text-white">{partner.name}</h4>
              <p className="text-xs text-slate-400 flex items-start gap-1">
                <span>📍</span>
                <span>{partner.address}</span>
              </p>

              <div className="flex items-center justify-between text-[11px] pt-1 text-slate-400">
                <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                  <CheckCircle2 size={13} />
                  <span>Authorized for {scheme?.name ? scheme.name.split(' ')[0] : 'Scheme'}</span>
                </span>
                <span className="font-medium text-slate-300">{partner.contact_phone || partner.phone}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setRouteModalPartner(partner)}
                className="flex-1 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center justify-center gap-1.5 transition-colors"
              >
                <Navigation size={13} className="text-indigo-400" />
                <span>Directions</span>
              </button>

              <button
                onClick={() => handleApplyWithPartner(partner)}
                className="flex-1 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-1 transition-colors"
              >
                <span>Apply Here</span>
                <ChevronRight size={13} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {routeModalPartner && (
        <DirectionsModal partner={routeModalPartner} onClose={() => setRouteModalPartner(null)} />
      )}
    </div>
  )
}

function DirectionsModal({ partner, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-xs z-50 flex items-center justify-center p-4">
      <div className="bg-[#161a26] border border-slate-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <MapPin size={18} className="text-indigo-400" />
            <h3 className="text-base font-bold text-white">Partner Directions & Contact</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-sm font-bold">
            ✕
          </button>
        </div>

        <div className="space-y-3 text-xs">
          <h4 className="text-sm font-bold text-white">{partner.name}</h4>
          <p className="text-slate-400">📍 {partner.address}</p>

          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-slate-400 block">Distance & Travel Estimate:</span>
            <span className="text-lg font-black text-indigo-400">
              {partner.calculatedDistanceText || partner.distance_formatted || partner.distance}
            </span>
            <p className="text-[11px] text-slate-500">Estimated ~10-15 mins drive from your current location</p>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-white font-mono font-bold">
            <Phone size={15} />
            <span>{partner.contact_phone || partner.phone}</span>
          </div>
        </div>

        <div className="pt-2 flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold"
          >
            Close
          </button>
          <a
            href={`https://maps.google.com/?q=${encodeURIComponent(partner.name + ' ' + partner.address)}`}
            target="_blank"
            rel="noreferrer"
            className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-1.5"
          >
            <span>Open Google Maps</span>
            <ExternalLink size={14} />
          </a>
        </div>
      </div>
    </div>
  )
}
