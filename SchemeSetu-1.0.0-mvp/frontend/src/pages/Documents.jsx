import { useState, useRef } from 'react'
import { 
  FileCheck, 
  Upload, 
  CheckCircle2, 
  Loader2, 
  Edit3, 
  ShieldCheck, 
  Eye, 
  Sparkles,
  AlertCircle,
  FileText
} from 'lucide-react'
import useChatStore from '../store/chatStore'

export default function Documents() {
  const { documents, ocrState, simulatePaddleOCRUpload, confirmOcrData, resetOcrState } = useChatStore()
  const fileInputRef = useRef(null)

  // Editable fields during OCR confirm step
  const [editFields, setEditFields] = useState({})

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    simulatePaddleOCRUpload(file)
  }

  const handleStartConfirm = () => {
    setEditFields(ocrState.extractedData || {})
  }

  const handleFieldChange = (key, value) => {
    setEditFields((prev) => ({ ...prev, [key]: value }))
  }

  const handleFinalSubmit = () => {
    confirmOcrData(editFields)
  }

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-semibold mb-2">
            <Sparkles size={14} />
            <span>PaddleOCR Engine v2.7 Active</span>
          </div>
          <h1 className="text-xl md:text-2xl font-black text-white">MY DOCUMENTS & OCR VERIFICATION</h1>
          <p className="text-xs text-slate-400">
            Upload certificates to extract key fields automatically using PaddleOCR with mandatory user Edit/Confirm verification.
          </p>
        </div>

        <button
          onClick={() => fileInputRef.current?.click()}
          className="shrink-0 px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-colors"
        >
          <Upload size={16} />
          <span>Upload Document</span>
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {/* ── Active Documents Grid ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {documents.map((doc) => {
          const isVerified = doc.status === 'verified'

          return (
            <div
              key={doc.id}
              className={`rounded-2xl p-5 border transition-all space-y-3 flex flex-col justify-between ${
                isVerified
                  ? 'bg-slate-900/90 border-slate-800'
                  : 'bg-slate-900/50 border-dashed border-slate-700 hover:border-indigo-500/50'
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-indigo-400">
                    <FileText size={18} />
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                      isVerified
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {isVerified ? '✓ Verified' : '+ Pending'}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white">{doc.name}</h3>

                {doc.extractedData ? (
                  <div className="space-y-1 p-3 rounded-xl bg-slate-800/60 border border-slate-700/50 text-xs text-slate-300 font-mono">
                    {Object.entries(doc.extractedData).slice(0, 2).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-slate-400 capitalize">{k}:</span>
                        <span className="font-semibold text-indigo-300 truncate max-w-[120px]">{v}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">Not uploaded yet</p>
                )}
              </div>

              {isVerified ? (
                <div className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium pt-2 border-t border-slate-800">
                  <CheckCircle2 size={13} />
                  <span>Information extracted</span>
                </div>
              ) : (
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-colors"
                >
                  + Upload Document
                </button>
              )}
            </div>
          )
        })}
      </div>

      {/* ── PaddleOCR Upload & Verification Modal / Workflow ─────────────── */}
      {ocrState.step !== 'idle' && ocrState.step !== 'confirmed' && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full p-6 space-y-5 shadow-2xl">
            
            {/* Modal Title */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Sparkles size={18} className="text-amber-400" />
                <h3 className="text-base font-bold text-white">PaddleOCR Field Extraction</h3>
              </div>
              <button onClick={resetOcrState} className="text-slate-400 hover:text-white">✕</button>
            </div>

            {/* Stepper Status */}
            {ocrState.isProcessing ? (
              <div className="py-12 text-center space-y-4">
                <Loader2 size={36} className="text-indigo-400 animate-spin mx-auto" />
                <div className="space-y-1">
                  <h4 className="text-base font-bold text-white">Processing Document with PaddleOCR...</h4>
                  <p className="text-xs text-slate-400">Detecting text regions & masking sensitive PII attributes</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Notice */}
                <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-800/40 text-xs text-indigo-200 flex items-start gap-2">
                  <AlertCircle size={16} className="text-indigo-400 shrink-0 mt-0.5" />
                  <span>
                    <strong>PaddleOCR Step:</strong> Please review the auto-extracted attributes below. You can edit any field before confirming to ensure 100% accuracy.
                  </span>
                </div>

                {/* Extracted Fields Form */}
                <div className="space-y-3 p-4 rounded-xl bg-slate-800/60 border border-slate-700 max-h-60 overflow-y-auto">
                  <h4 className="text-xs font-bold text-slate-300 uppercase">Extracted Fields Preview:</h4>

                  {Object.entries(editFields.length ? editFields : ocrState.extractedData || {}).map(([key, val]) => (
                    <div key={key} className="space-y-1">
                      <label className="text-[11px] font-medium text-slate-400 uppercase">{key}</label>
                      <input
                        type="text"
                        value={editFields[key] !== undefined ? editFields[key] : val}
                        onChange={(e) => handleFieldChange(key, e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs font-semibold text-slate-100 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  ))}
                </div>

                {/* Buttons */}
                <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-3">
                  <button
                    onClick={resetOcrState}
                    className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                  >
                    Cancel
                  </button>

                  <button
                    onClick={handleFinalSubmit}
                    className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-indigo-600/30"
                  >
                    <CheckCircle2 size={16} />
                    <span>Confirm & Update Profile</span>
                  </button>
                </div>
              </div>
            )}

          </div>
        </div>
      )}
    </div>
  )
}
