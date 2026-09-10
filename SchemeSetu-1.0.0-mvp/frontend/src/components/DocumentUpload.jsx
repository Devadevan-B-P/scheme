import { useRef } from 'react'
import { Paperclip, Loader2 } from 'lucide-react'
import useChatStore from '../store/chatStore'

export default function DocumentUpload() {
  const { uploadDocument, isLoading, uploadState } = useChatStore()
  const fileInputRef = useRef(null)

  const isUploading = uploadState === 'uploading'

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Reset input so the same file can be selected again if needed
    e.target.value = ''

    await uploadDocument(file)
  }

  return (
    <div className="flex items-center">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept="image/*"
        disabled={isLoading || isUploading}
      />
      <button
        type="button"
        disabled={isLoading || isUploading}
        onClick={() => fileInputRef.current?.click()}
        className="shrink-0 w-10 h-10 rounded-2xl bg-slate-800 hover:bg-slate-700 disabled:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors border border-slate-700"
        title="Upload Income Certificate (Image)"
      >
        {isUploading ? (
          <Loader2 size={18} className="text-indigo-400 animate-spin" />
        ) : (
          <Paperclip size={18} className="text-slate-400" />
        )}
      </button>
    </div>
  )
}
