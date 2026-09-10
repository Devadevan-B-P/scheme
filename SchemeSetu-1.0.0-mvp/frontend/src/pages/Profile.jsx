import { useState } from 'react'
import { User, Edit3, Save, CheckCircle2, ShieldCheck, RefreshCw } from 'lucide-react'
import useChatStore from '../store/chatStore'

export default function Profile() {
  const { userProfile, updateProfile, setActiveTab } = useChatStore()

  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({ ...userProfile })
  const [savedSuccess, setSavedSuccess] = useState(false)

  const handleChange = (key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = (e) => {
    e.preventDefault()
    updateProfile(formData)
    setIsEditing(false)
    setSavedSuccess(true)
    setTimeout(() => setSavedSuccess(false), 3000)
  }

  return (
    <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-2">
            <ShieldCheck size={14} />
            <span>Extracted Beneficiary Profile</span>
          </div>
          <h1 className="text-xl md:text-2xl font-black text-white">MY PROFILE</h1>
          <p className="text-xs text-slate-400">
            View & update information extracted by AI Assistant or PaddleOCR.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isEditing ? (
            <button
              onClick={handleSave}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-600/30 transition-colors"
            >
              <Save size={16} />
              <span>Save Profile</span>
            </button>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-indigo-600/30 transition-colors"
            >
              <Edit3 size={16} />
              <span>Edit Profile</span>
            </button>
          )}
        </div>
      </div>

      {/* Success Notification */}
      {savedSuccess && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 size={16} />
          <span>Profile updated successfully! Scheme matches will automatically re-evaluate.</span>
        </div>
      )}

      {/* Main Profile Form / Cards */}
      <form onSubmit={handleSave} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Personal Details */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3">Personal Information</h3>

          <div className="space-y-3 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400 font-semibold">Full Name</label>
              <input
                type="text"
                disabled={!isEditing}
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 font-semibold text-slate-100 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Age</label>
                <input
                  type="number"
                  disabled={!isEditing}
                  value={formData.age}
                  onChange={(e) => handleChange('age', Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 font-semibold text-slate-100 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Gender</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.gender}
                  onChange={(e) => handleChange('gender', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 font-semibold text-slate-100 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Category</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.category}
                  onChange={(e) => handleChange('category', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 font-semibold text-indigo-300 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Financial Details */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3">Financial Information</h3>

          <div className="space-y-3 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400 font-semibold">Annual Family Income (₹)</label>
              <input
                type="number"
                disabled={!isEditing}
                value={formData.income}
                onChange={(e) => handleChange('income', Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 font-semibold text-emerald-400 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-semibold">Primary Occupation</label>
              <input
                type="text"
                disabled={!isEditing}
                value={formData.occupation}
                onChange={(e) => handleChange('occupation', e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 font-semibold text-slate-100 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Business Venture */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3">Business Venture Details</h3>

          <div className="space-y-3 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400 font-semibold">Business Type / Sector</label>
              <input
                type="text"
                disabled={!isEditing}
                value={formData.businessType}
                onChange={(e) => handleChange('businessType', e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 font-semibold text-slate-100 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Project Cost (₹)</label>
                <input
                  type="number"
                  disabled={!isEditing}
                  value={formData.projectCost}
                  onChange={(e) => handleChange('projectCost', Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 font-semibold text-slate-100 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">Loan Required (₹)</label>
                <input
                  type="number"
                  disabled={!isEditing}
                  value={formData.loanRequirement}
                  onChange={(e) => handleChange('loanRequirement', Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 font-semibold text-slate-100 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Location Details */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3">Location & Address</h3>

          <div className="space-y-3 text-xs">
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">State</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.state}
                  onChange={(e) => handleChange('state', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 font-semibold text-slate-100 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">District</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.district}
                  onChange={(e) => handleChange('district', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 font-semibold text-slate-100 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-semibold">PIN Code</label>
                <input
                  type="text"
                  disabled={!isEditing}
                  value={formData.pinCode}
                  onChange={(e) => handleChange('pinCode', e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 font-semibold text-slate-100 disabled:opacity-80 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          </div>
        </div>

      </form>
    </div>
  )
}
