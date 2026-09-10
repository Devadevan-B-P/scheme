import { 
  Bot, 
  LayoutDashboard, 
  Target, 
  FileText, 
  Calculator, 
  MapPin, 
  FolderCheck, 
  FileCheck, 
  User, 
  X, 
  Sparkles,
  Lock,
  LogOut,
  ShieldCheck
} from 'lucide-react'
import useChatStore from '../store/chatStore'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, badge: null },
  { id: 'ai-onboarding', label: 'AI Assistant', icon: Bot, badge: 'Live AI' },
  { id: 'scheme-results', label: 'Scheme Results', icon: Target, badge: 'Matched' },
  { id: 'scheme-details', label: 'Scheme Details', icon: FileText, badge: null },
  { id: 'calculator', label: 'Financial Calculator', icon: Calculator, badge: null },
  { id: 'partner-finder', label: 'Find Channel Partner', icon: MapPin, badge: 'Nearby' },
  { id: 'documents', label: 'Documents & OCR', icon: FileCheck, badge: 'PaddleOCR' },
  { id: 'applications', label: 'My Applications', icon: FolderCheck, badge: 'Active' },
  { id: 'profile', label: 'My Profile', icon: User, badge: null },
  { id: 'admin', label: 'Admin Portal', icon: Lock, badge: 'Gov Admin' },
]

export default function Sidebar() {
  const { activeTab, setActiveTab, sidebarOpen, setSidebarOpen, userProfile, logoutUser } = useChatStore()

  if (!userProfile?.isAuthenticated) {
    return null
  }

  const isAdmin = userProfile?.role === 'admin'

  return (
    <>
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div 
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 lg:hidden" 
        />
      )}

      <aside 
        className={`fixed top-0 left-0 bottom-0 w-64 bg-[#12151e] border-r border-slate-800 z-50 flex flex-col transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="shrink-0 h-16 px-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-600/20">
              <Sparkles size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">SchemeSetu</h1>
              <p className="text-[10px] text-indigo-400 font-semibold uppercase">MoSJE Digital Portal</p>
            </div>
          </div>
          <button 
            onClick={() => setSidebarOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden"
          >
            <X size={18} />
          </button>
        </div>

        {/* User Mini Card */}
        <div className="p-3 mx-3 my-3 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-sm text-white ${
            isAdmin ? 'bg-amber-600' : 'bg-indigo-600'
          }`}>
            {userProfile?.name ? userProfile.name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-slate-200 truncate">{userProfile?.name || 'Beneficiary'}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded uppercase tracking-wider ${
                isAdmin 
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              }`}>
                {userProfile?.role || 'beneficiary'}
              </span>
              {userProfile?.state && (
                <span className="text-[10px] text-slate-400 truncate">• {userProfile.state}</span>
              )}
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          {NAV_ITEMS.filter((item) => item.id !== 'admin' || isAdmin).map((item) => {
            const Icon = item.icon
            const isActive = activeTab === item.id

            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Icon size={16} className={isActive ? 'text-white' : 'text-slate-400'} />
                <span className="flex-1 text-left truncate">{item.label}</span>
                {item.badge && (
                  <span 
                    className={`px-1.5 py-0.5 text-[9px] font-bold rounded-md ${
                      isActive 
                        ? 'bg-indigo-700 text-white' 
                        : item.badge.includes('Gov')
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : item.badge.includes('Live') 
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                        : item.badge.includes('Paddle')
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Footer Support Info & Sign Out */}
        <div className="shrink-0 p-3 border-t border-slate-800/80 space-y-2">
          <div className="p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-800/40 text-left">
            <div className="flex items-center gap-1.5 font-bold text-indigo-300 text-[11px]">
              <ShieldCheck size={13} className="text-emerald-400" />
              <span>Deterministic Rule Engine</span>
            </div>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Verified against MoSJE 2026 gazette criteria.
            </p>
          </div>

          <button
            onClick={logoutUser}
            className="w-full py-2 px-3 rounded-xl bg-slate-800/80 hover:bg-rose-950/40 border border-slate-700 hover:border-rose-500/40 text-slate-300 hover:text-rose-300 text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  )
}
