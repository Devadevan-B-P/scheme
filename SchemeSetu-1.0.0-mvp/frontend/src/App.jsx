import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import useChatStore from './store/chatStore'

import ChatFlow from './pages/ChatFlow'
import Dashboard from './pages/Dashboard'
import SchemeResults from './pages/SchemeResults'
import SchemeDetails from './pages/SchemeDetails'
import FinancialCalculator from './pages/FinancialCalculator'
import PartnerFinder from './pages/PartnerFinder'
import Documents from './pages/Documents'
import Applications from './pages/Applications'
import Profile from './pages/Profile'
import AdminDashboard from './pages/AdminDashboard'
import Auth from './pages/Auth'
import { ShieldX } from 'lucide-react'

// ── Role-guard: shown when a non-admin tries to reach /admin ──────────────────
function AccessDenied() {
  const { setActiveTab, userProfile } = useChatStore()
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] gap-5 p-8 text-center">
      <div className="w-16 h-16 rounded-2xl bg-rose-950/40 border border-rose-500/40 flex items-center justify-center shadow-lg shadow-rose-950/50">
        <ShieldX size={32} className="text-rose-400" />
      </div>
      <div className="space-y-1.5 max-w-sm">
        <h2 className="text-xl font-black text-white">Access Restricted</h2>
        <p className="text-sm text-slate-400">
          The Admin Portal requires an <span className="font-bold text-slate-200">admin</span> role.
          Your current role is{' '}
          <span className="font-bold text-rose-400">{userProfile?.role || 'beneficiary'}</span>.
        </p>
        <p className="text-xs text-slate-500 mt-1">
          If you require administrative access to the scheme ingestion pipeline, contact your MoSJE administrator.
        </p>
      </div>
      <button
        onClick={() => setActiveTab('dashboard')}
        className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02]"
      >
        Return to Dashboard
      </button>
    </div>
  )
}

export default function App() {
  const { activeTab, userProfile } = useChatStore()

  const isAuthenticated = Boolean(userProfile?.isAuthenticated)
  const isAdmin = userProfile?.role === 'admin'

  const renderActivePage = () => {
    if (!isAuthenticated) {
      return <Auth />
    }

    switch (activeTab) {
      case 'auth':
        return isAdmin ? <AdminDashboard /> : <Dashboard />
      case 'ai-onboarding':
        return <ChatFlow />
      case 'dashboard':
        return <Dashboard />
      case 'scheme-results':
        return <SchemeResults />
      case 'scheme-details':
        return <SchemeDetails />
      case 'calculator':
        return <FinancialCalculator />
      case 'partner-finder':
        return <PartnerFinder />
      case 'documents':
        return <Documents />
      case 'applications':
        return <Applications />
      case 'profile':
        return <Profile />
      case 'admin':
        return isAdmin ? <AdminDashboard /> : <AccessDenied />
      default:
        return isAdmin ? <AdminDashboard /> : <Dashboard />
    }
  }

  return (
    <div className="min-h-screen bg-[#0f1117] text-slate-100 flex font-sans antialiased selection:bg-indigo-500 selection:text-white">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <div className={`flex-1 flex flex-col min-w-0 ${isAuthenticated ? 'lg:pl-64' : ''}`}>
        {/* Top Navbar */}
        <Navbar />

        {/* Dynamic Page Container */}
        <main className="flex-1 min-h-0 overflow-y-auto">
          {renderActivePage()}
        </main>
      </div>
    </div>
  )
}
