import { useState } from 'react'
import { Menu, ShieldCheck, UserCheck, Globe, ChevronDown, LogOut, Lock } from 'lucide-react'
import useChatStore from '../store/chatStore'

const PAGE_TITLES = {
  'auth': { title: 'SchemeSetu Authentication', sub: 'Sign in to access personalized scheme matching' },
  'ai-onboarding': { title: 'AI Conversational Onboarding', sub: 'Collect beneficiary details conversationally' },
  'dashboard': { title: 'Beneficiary Dashboard', sub: 'Overview of your matched schemes & verification status' },
  'scheme-results': { title: 'Matched Scheme Results', sub: 'Deterministic rule evaluation breakdown' },
  'scheme-details': { title: 'Scheme Details & Application Journey', sub: 'In-depth criteria, benefits, & steps' },
  'calculator': { title: 'Financial Calculator', sub: 'Calculate loan EMI, interest, & project funding' },
  'partner-finder': { title: 'Channel Partner Finder', sub: 'Locate nearest government SCAs & bank branches' },
  'documents': { title: 'Documents Hub (PaddleOCR)', sub: 'Upload & verify certificates with OCR field extraction' },
  'applications': { title: 'Application Tracking', sub: 'Track your live scheme application status' },
  'profile': { title: 'Beneficiary Profile', sub: 'View & update extracted personal information' },
  'admin': { title: 'MoSJE Governance & Ingestion Portal', sub: 'Firecrawl pipeline, scheme verification, & source management' },
}

const LANGUAGES = ['English', 'हिंदी', 'മലയാളം', 'தமிழ்', 'తెలుగు']

export default function Navbar() {
  const { activeTab, setActiveTab, setSidebarOpen, userProfile, language, setLanguage, logoutUser } = useChatStore()
  const [langMenuOpen, setLangMenuOpen] = useState(false)

  const pageInfo = PAGE_TITLES[activeTab] || { title: 'SchemeSetu', sub: 'Government Scheme Portal' }
  const isAuthenticated = Boolean(userProfile?.isAuthenticated)
  const isAdmin = userProfile?.role === 'admin'

  return (
    <header className="h-16 shrink-0 bg-[#12151e]/90 border-b border-slate-800 px-4 flex items-center justify-between sticky top-0 z-30 backdrop-blur-md">
      <div className="flex items-center gap-3">
        {isAuthenticated && (
          <button 
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white lg:hidden"
          >
            <Menu size={18} />
          </button>
        )}
        <div>
          <h2 className="text-sm font-bold text-slate-100">{pageInfo.title}</h2>
          <p className="text-[11px] text-slate-400 hidden sm:block">{pageInfo.sub}</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Language Selector */}
        <div className="relative">
          <button
            onClick={() => setLangMenuOpen(!langMenuOpen)}
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white transition-colors py-1.5 px-2.5 rounded-lg bg-slate-800/80 border border-slate-700/80"
          >
            <Globe size={13} className="text-indigo-400" />
            <span className="font-semibold">{language || 'English'}</span>
            <ChevronDown size={12} />
          </button>

          {langMenuOpen && (
            <div className="absolute right-0 mt-1.5 w-32 bg-slate-800 border border-slate-700 rounded-xl shadow-xl py-1 z-50 text-slate-200 text-xs">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang}
                  onClick={() => {
                    setLanguage(lang)
                    setLangMenuOpen(false)
                  }}
                  className={`w-full text-left px-3.5 py-2 hover:bg-slate-700 transition-colors ${
                    language === lang ? 'font-bold text-indigo-400 bg-indigo-950/40' : ''
                  }`}
                >
                  {lang}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Verification / Admin Pill */}
        {isAuthenticated && (
          <div className={`hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border ${
            isAdmin
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}>
            {isAdmin ? <Lock size={13} /> : <ShieldCheck size={13} />}
            <span>{isAdmin ? 'MoSJE Admin' : 'Profile Verified'}</span>
          </div>
        )}

        {/* Account Info & Logout / Login */}
        {isAuthenticated ? (
          <div className="flex items-center gap-2.5 pl-2 border-l border-slate-800">
            <button
              onClick={() => setActiveTab('profile')}
              className="flex items-center gap-2 p-1 rounded-lg hover:bg-slate-800 transition-colors text-left"
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-sm ${
                isAdmin ? 'bg-amber-600' : 'bg-indigo-600'
              }`}>
                {userProfile?.name ? userProfile.name.charAt(0).toUpperCase() : 'U'}
              </div>
              <span className="text-xs font-medium text-slate-200 hidden sm:inline max-w-[100px] truncate">
                {userProfile?.name || 'User'}
              </span>
            </button>

            <button
              onClick={logoutUser}
              title="Sign Out"
              className="p-2 rounded-xl text-slate-400 hover:text-rose-300 hover:bg-rose-950/30 border border-transparent hover:border-rose-500/30 transition-all"
            >
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <button
            onClick={() => setActiveTab('auth')}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-indigo-600/30 transition-all"
          >
            <UserCheck size={14} />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  )
}
