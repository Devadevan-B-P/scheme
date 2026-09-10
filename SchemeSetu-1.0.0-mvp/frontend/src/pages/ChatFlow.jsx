import { useState, useEffect, useRef, useCallback } from 'react'
import { Send, Bot, Loader2, RefreshCw, ShieldAlert, Upload } from 'lucide-react'
import ChatBubble from '../components/ChatBubble'
import DocumentUpload from '../components/DocumentUpload'
import ConsentModal from '../components/ConsentModal'
import useChatStore from '../store/chatStore'

const STARTER_HINTS = [
  'I am 28 years old, SC category, annual income ₹2.5 lakh, want to start tailoring business in Lucknow',
  'I am a woman entrepreneur, 32 years old, OBC, annual income 1.8 lakh, seeking micro-loan for grocery shop',
  'I am 35 years old with 40% certified physical disability, looking for 5 lakh loan for a cyber cafe',
]

export default function ChatFlow() {
  const [input, setInput] = useState('')
  const {
    messages,
    isLoading,
    sendMessage,
    sessionId,
    language,
    setLanguage,
    completeness,
    backendStatus,
    checkBackendHealth,
    uploadState,
    resetChat,
  } = useChatStore()
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-scroll to the latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Health check on mount
  useEffect(() => {
    checkBackendHealth()
  }, [checkBackendHealth])

  const handleSubmit = useCallback(
    (e) => {
      e?.preventDefault()
      const text = input.trim()
      if (!text || isLoading) return
      setInput('')
      sendMessage(text)
    },
    [input, isLoading, sendMessage]
  )

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleHint = (hint) => {
    if (isLoading) return
    sendMessage(hint)
  }

  return (
    <div className="flex flex-col h-screen bg-[#0f1117]">
      <ConsentModal />


      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header className="shrink-0 border-b border-slate-800 bg-[#0f1117]/80 backdrop-blur-sm px-4 py-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-amber-500 flex items-center justify-center text-white text-[10px] font-bold">
            सेतु
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-semibold text-slate-100">SchemeSetu AI</h1>
              <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                MoSJE PS 26092
              </span>
            </div>
            <p className="text-[10px] text-slate-500">
              AI Extracts • Deterministic Engine Decides • PII Shield Active
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Audit indicator */}
          {messages.length > 0 && (
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-900/30 text-xs border border-indigo-500/20 mr-1" title="Decisions audited cryptographically">
              <ShieldAlert size={12} className="text-indigo-400" />
              <span className="text-indigo-300 text-[11px] font-medium">Audited</span>
            </div>
          )}

          {/* Backend status */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 text-xs border border-slate-700">
            <span
              className={`w-2 h-2 rounded-full ${
                backendStatus === 'connected'
                  ? 'bg-emerald-500 animate-pulse'
                  : backendStatus === 'checking'
                  ? 'bg-amber-500 animate-pulse'
                  : 'bg-red-500'
              }`}
            />
            <span className="text-slate-300 text-[11px]">
              {backendStatus === 'connected' ? 'API Connected' : backendStatus === 'checking' ? 'Connecting…' : 'Offline'}
            </span>
          </div>

          {/* Language selector */}
          <div className="flex items-center border border-slate-700 rounded-lg overflow-hidden text-xs">
            <button
              onClick={() => setLanguage('en')}
              className={`px-2.5 py-1 font-medium transition-colors ${
                language === 'en'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              EN
            </button>
            <button
              onClick={() => setLanguage('hi')}
              className={`px-2.5 py-1 font-medium transition-colors ${
                language === 'hi'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              हिन्दी
            </button>
          </div>

          {/* Go to Dashboard */}
          <button
            onClick={() => useChatStore.getState().setActiveTab('dashboard')}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-colors hidden sm:block"
          >
            Dashboard →
          </button>

          {/* Reset */}
          <button
            onClick={resetChat}
            title="Reset conversation"
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </header>

      {/* ── Profile Completeness Bar ───────────────────────────────────────── */}
      {completeness > 0 && (
        <div className="shrink-0 px-4 py-2 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
            <span>Profile Completeness</span>
            <span className="font-mono">{completeness}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5">
            <div
              className="h-1.5 rounded-full bg-gradient-to-r from-indigo-600 to-emerald-500 transition-all duration-500"
              style={{ width: `${completeness}%` }}
            />
          </div>
        </div>
      )}


      {/* ── Message List ────────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto px-4 py-6 space-y-4">

        {/* Empty state */}
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-600/30 flex items-center justify-center">
              <Bot size={28} className="text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-200 mb-1">
                Namaste! Tell me about yourself
              </h2>
              <p className="text-sm text-slate-500 max-w-sm">
                Share your age, income, category, and business idea — I'll find the right
                MoSJE government schemes for you.
              </p>
            </div>

            {/* Hint chips */}
            <div className="flex flex-col gap-2 w-full max-w-md">
              {STARTER_HINTS.map((hint) => (
                <button
                  key={hint}
                  onClick={() => handleHint(hint)}
                  className="text-left text-xs text-slate-400 border border-slate-700 hover:border-indigo-600/60 hover:text-slate-200 hover:bg-slate-800/50 rounded-xl px-4 py-2.5 transition-all duration-150"
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Bubbles */}
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}

        {/* Upload indicator */}
        {uploadState === 'uploading' && (
          <div className="flex justify-start">
            <div className="shrink-0 w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-white text-[10px] font-bold mr-2 mt-1">
              AI
            </div>
            <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-2 text-xs text-slate-400">
              <Upload size={14} className="animate-pulse text-indigo-400" />
              Processing document with PaddleOCR…
            </div>
          </div>
        )}

        {/* Typing indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="shrink-0 w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-white text-[10px] font-bold mr-2 mt-1">
              AI
            </div>
            <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      {/* ── Input Bar ───────────────────────────────────────────────────────── */}
      <footer className="shrink-0 border-t border-slate-800 bg-[#0f1117] px-4 py-3">
        <form onSubmit={handleSubmit} className="flex items-end gap-2 max-w-3xl mx-auto">
          <DocumentUpload />
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder={
              language === 'hi'
                ? 'अपना प्रश्न या व्यवसाय विवरण यहाँ लिखें…'
                : 'Describe your background, income, or business idea…'
            }
            className="flex-1 resize-none rounded-2xl bg-slate-800 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed leading-relaxed"
            style={{ maxHeight: '120px', overflowY: 'auto' }}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="shrink-0 w-10 h-10 rounded-2xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            {isLoading ? (
              <Loader2 size={16} className="text-white animate-spin" />
            ) : (
              <Send size={16} className="text-white" />
            )}
          </button>
        </form>
        {/* Footer privacy banner */}
        <div className="flex items-center justify-between text-[10px] text-slate-600 mt-2 px-1 max-w-3xl mx-auto">
          <span className="flex items-center gap-1">
            <ShieldAlert size={10} className="text-emerald-500" />
            PII Shield: Aadhaar & PAN redacted before AI processing
          </span>
          <span>Verified MoSJE Data • PaddleOCR Local</span>
        </div>
      </footer>

    </div>
  )
}
