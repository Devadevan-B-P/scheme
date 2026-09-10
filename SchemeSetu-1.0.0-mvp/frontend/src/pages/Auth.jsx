import { useState } from 'react'
import { 
  Lock, 
  Mail, 
  UserCheck, 
  ArrowRight, 
  AlertCircle, 
  Loader2,
  ShieldCheck,
  Sparkles,
  User,
  KeyRound
} from 'lucide-react'
import useChatStore from '../store/chatStore'

export default function Auth() {
  const { loginUser, signupUser } = useChatStore()
  const [mode, setMode] = useState('login') // 'login' | 'signup'

  // Form states
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [category, setCategory] = useState('SC')
  const [stateName, setStateName] = useState('Kerala')
  const [district, setDistrict] = useState('Thiruvananthapuram')
  const [role, setRole] = useState('beneficiary') // 'beneficiary' | 'admin'

  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setErrorMsg('')

    if (mode === 'login') {
      const res = await loginUser(email, password)
      if (!res.success) {
        setErrorMsg(res.error || 'Invalid email or password. Please try again.')
      }
    } else {
      if (!fullName.trim()) {
        setErrorMsg('Full name is required.')
        setLoading(false)
        return
      }
      const res = await signupUser({
        full_name: fullName,
        email,
        password,
        phone_number: phone,
        category,
        state: stateName,
        district,
        role,
      })
      if (!res.success) {
        setErrorMsg(res.error || 'Registration failed. Please try again.')
      }
    }

    setLoading(false)
  }

  // Quick Demo Logins for evaluators
  const handleQuickDemo = async (demoRole) => {
    setLoading(true)
    setErrorMsg('')
    const demoEmail = demoRole === 'admin' ? 'admin@schemesetu.gov.in' : 'rajesh.kumar@example.com'
    const demoPass = 'DemoPass@123'
    const res = await loginUser(demoEmail, demoPass)
    if (!res.success) {
      // If demo user doesn't exist yet in db, create them on the fly
      const signupRes = await signupUser({
        full_name: demoRole === 'admin' ? 'MoSJE Admin Officer' : 'Rajesh Kumar',
        email: demoEmail,
        password: demoPass,
        phone_number: '9876543210',
        category: 'SC',
        state: 'Kerala',
        district: 'Thiruvananthapuram',
        role: demoRole,
      })
      if (!signupRes.success) {
        setErrorMsg(signupRes.error || 'Quick login failed')
      }
    }
    setLoading(false)
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center p-4 sm:p-6">
      <div className="max-w-md w-full bg-slate-900/90 border border-slate-800/80 rounded-2xl shadow-2xl p-6 md:p-8 space-y-6 backdrop-blur-xl relative overflow-hidden">
        
        {/* Glow ambient accent */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header Emblem */}
        <div className="text-center space-y-2 relative z-10">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-indigo-500 text-white text-2xl font-black mx-auto flex items-center justify-center shadow-lg shadow-indigo-600/30">
            🏛️
          </div>
          <div className="space-y-1">
            <h1 className="text-2xl font-black text-white tracking-tight">SchemeSetu Portal</h1>
            <p className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
              Ministry of Social Justice & Empowerment
            </p>
          </div>
        </div>

        {/* Tab Toggle: Login vs Signup */}
        <div className="flex bg-slate-800/70 p-1 rounded-xl border border-slate-700/60 text-xs font-bold relative z-10">
          <button
            type="button"
            onClick={() => { setMode('login'); setErrorMsg('') }}
            className={`flex-1 py-2.5 rounded-lg transition-all ${
              mode === 'login' 
                ? 'bg-indigo-600 text-white font-extrabold shadow-md shadow-indigo-600/30' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Beneficiary Login
          </button>
          <button
            type="button"
            onClick={() => { setMode('signup'); setErrorMsg('') }}
            className={`flex-1 py-2.5 rounded-lg transition-all ${
              mode === 'signup' 
                ? 'bg-indigo-600 text-white font-extrabold shadow-md shadow-indigo-600/30' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            New Registration
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2.5 font-medium relative z-10">
            <AlertCircle size={18} className="text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs relative z-10">
          
          {mode === 'signup' && (
            <div className="space-y-1.5">
              <label className="font-bold text-slate-300">Full Name (As in Aadhaar)</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Rajesh Kumar"
                className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-4 py-3 text-xs font-semibold text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              />
            </div>
          )}

          <div className="space-y-1.5">
            <label className="font-bold text-slate-300">Email Address</label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="beneficiary@schemesetu.gov.in"
                className="w-full bg-slate-800/80 border border-slate-700 rounded-xl pl-10 pr-4 py-3 text-xs font-semibold text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              />
              <Mail size={16} className="absolute left-3.5 top-3.5 text-slate-400" />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="font-bold text-slate-300">Password</label>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-slate-800/80 border border-slate-700 rounded-xl pl-10 pr-4 py-3 text-xs font-semibold text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              />
              <Lock size={16} className="absolute left-3.5 top-3.5 text-slate-400" />
            </div>
          </div>

          {mode === 'signup' && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="font-bold text-slate-300">Phone Number</label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="9876543210"
                    className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="font-bold text-slate-300">Social Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs font-bold text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="SC">Scheduled Caste (SC)</option>
                    <option value="ST">Scheduled Tribe (ST)</option>
                    <option value="OBC">OBC</option>
                    <option value="General">General / EWS</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="font-bold text-slate-300">State</label>
                  <input
                    type="text"
                    value={stateName}
                    onChange={(e) => setStateName(e.target.value)}
                    className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="font-bold text-slate-300">District</label>
                  <input
                    type="text"
                    value={district}
                    onChange={(e) => setDistrict(e.target.value)}
                    className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="font-bold text-slate-300">Account Access Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs font-bold text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="beneficiary">Beneficiary User (Applicant Access)</option>
                  <option value="admin">MoSJE Admin Officer (Admin Scraper & Portal Access)</option>
                </select>
                <p className="text-[11px] text-slate-400">
                  {role === 'admin'
                    ? '🔑 Role saved in MongoDB: Full access to Ingestion Pipeline & Scheme Review'
                    : '👤 Role saved in MongoDB: Access to Beneficiary Dashboard & AI Scheme Finder'}
                </p>
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <>
                <span>{mode === 'login' ? 'Sign In to Portal' : 'Register Beneficiary Account'}</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </form>

        {/* Quick Demo Access Buttons for Evaluators */}
        <div className="pt-3 border-t border-slate-800/80 space-y-2 relative z-10">
          <p className="text-[11px] font-semibold text-slate-400 text-center">
            Instant Demo Logins (No typing required)
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickDemo('beneficiary')}
              disabled={loading}
              className="py-2.5 px-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
            >
              <User size={13} className="text-indigo-400" />
              <span>Demo Beneficiary</span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickDemo('admin')}
              disabled={loading}
              className="py-2.5 px-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-amber-300 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
            >
              <KeyRound size={13} className="text-amber-400" />
              <span>Demo Admin Officer</span>
            </button>
          </div>
        </div>

        {/* Security Notice Footer */}
        <div className="pt-2 text-center relative z-10">
          <p className="text-[10px] text-slate-500">
            Protected by Government Encryption Standard • MoSJE Role-Based Access Control
          </p>
        </div>

      </div>
    </div>
  )
}
