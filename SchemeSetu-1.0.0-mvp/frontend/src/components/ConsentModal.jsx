import { useState, useEffect } from 'react'
import { ShieldCheck, Lock, CheckCircle2 } from 'lucide-react'

export default function ConsentModal() {
  const [hasConsent, setHasConsent] = useState(true) // assume true to prevent flicker
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const consent = localStorage.getItem('schemesetu_consent')
    if (consent !== 'true') {
      setHasConsent(false)
      setIsVisible(true)
    }
  }, [])

  const handleAccept = () => {
    localStorage.setItem('schemesetu_consent', 'true')
    setHasConsent(true)
    setTimeout(() => setIsVisible(false), 300) // fade out
  }

  if (hasConsent && !isVisible) return null

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${hasConsent ? 'opacity-0' : 'opacity-100'}`}>
      <div className="bg-[#1a1d27] border border-slate-700 rounded-2xl w-full max-w-md p-6 shadow-2xl mx-4 transform transition-transform duration-300 scale-100">
        
        <div className="w-12 h-12 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center mb-5">
          <ShieldCheck size={24} className="text-indigo-400" />
        </div>
        
        <h2 className="text-xl font-bold text-slate-100 mb-2">
          Your Privacy & Data Consent
        </h2>
        
        <p className="text-sm text-slate-400 mb-5 leading-relaxed">
          Welcome to SchemeSetu. Before we proceed, please review how we handle your data in compliance with the DPDP Act.
        </p>
        
        <ul className="space-y-4 mb-6">
          <li className="flex gap-3">
            <Lock size={18} className="text-slate-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-slate-200">Local Processing Only</p>
              <p className="text-xs text-slate-500">Your documents (like Income Certificates) are processed using our secure on-device PaddleOCR engine. Images are never sent to external AI providers.</p>
            </div>
          </li>
          <li className="flex gap-3">
            <ShieldCheck size={18} className="text-slate-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-slate-200">PII Shielding</p>
              <p className="text-xs text-slate-500">Sensitive information like Aadhaar and PAN numbers are redacted before any conversational AI processing happens.</p>
            </div>
          </li>
          <li className="flex gap-3">
            <CheckCircle2 size={18} className="text-slate-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-slate-200">Cryptographic Audit Logs</p>
              <p className="text-xs text-slate-500">All eligibility decisions are recorded in an immutable hash chain for transparency.</p>
            </div>
          </li>
        </ul>
        
        <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
          <button
            onClick={handleAccept}
            className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors"
          >
            I Understand & Agree
          </button>
        </div>
      </div>
    </div>
  )
}
