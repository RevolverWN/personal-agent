import { useState, useRef, useEffect } from 'react'
import { PaperAirplaneIcon } from '@heroicons/react/24/solid'
import FileUpload, { UploadedFile } from './FileUpload'

interface MessageInputProps {
  onSend: (message: string, files?: UploadedFile[]) => void
  isLoading: boolean
  disabled?: boolean
  placeholder?: string
}

export default function MessageInput({ 
  onSend, 
  isLoading, 
  disabled = false,
  placeholder = 'Type your message... (Shift+Enter for new line)'
}: MessageInputProps) {
  const [message, setMessage] = useState('')
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [showFileUpload, setShowFileUpload] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`
    }
  }, [message])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if ((!message.trim() && files.length === 0) || isLoading || disabled) return

    // Include file content in message if present
    let finalMessage = message.trim()
    
    if (files.length > 0) {
      const fileDescriptions = files.map(f => {
        if (f.content) {
          return `[File: ${f.name}]\n\`\`\`\n${f.content.slice(0, 10000)}${f.content.length > 10000 ? '\n... (truncated)' : ''}\n\`\`\``
        }
        return `[File: ${f.name} (${(f.size / 1024).toFixed(1)} KB)]`
      }).join('\n\n')
      
      finalMessage = finalMessage 
        ? `${finalMessage}\n\n${fileDescriptions}`
        : fileDescriptions
    }

    onSend(finalMessage, files)
    setMessage('')
    setFiles([])
    setShowFileUpload(false)

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleFilesSelected = (selectedFiles: UploadedFile[]) => {
    setFiles(selectedFiles)
  }

  return (
    <div className="space-y-2">
      {/* File Upload Area */}
      {showFileUpload && (
        <FileUpload
          onFilesSelected={handleFilesSelected}
          maxFiles={3}
          maxSizeMB={5}
        />
      )}

      {/* Message Input */}
      <form onSubmit={handleSubmit} className="flex items-end space-x-2">
        {/* File Toggle Button */}
        <button
          type="button"
          onClick={() => setShowFileUpload(!showFileUpload)}
          disabled={isLoading || disabled}
          className={`
            p-3 rounded-xl transition-colors
            ${showFileUpload 
              ? 'bg-primary-100 text-primary-600' 
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8 4a3 3 0 00-3 3v4a5 5 0 0010 0V7a1 1 0 112 0v4a7 7 0 11-14 0V7a5 5 0 0110 0v4a3 3 0 11-6 0V7a1 1 0 012 0v4a1 1 0 102 0V7a3 3 0 00-3-3z" clipRule="evenodd" />
          </svg>
        </button>

        {/* Text Input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading || disabled}
            rows={1}
            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl resize-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-gray-100 disabled:text-gray-500"
            style={{ minHeight: '48px', maxHeight: '200px' }}
          />
        </div>

        {/* Send Button */}
        <button
          type="submit"
          disabled={(!message.trim() && files.length === 0) || isLoading || disabled}
          className="btn-primary p-3 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <PaperAirplaneIcon className="w-5 h-5" />
        </button>
      </form>

      {/* File Count Indicator */}
      {files.length > 0 && !showFileUpload && (
        <p className="text-xs text-gray-500">
          {files.length} file{files.length > 1 ? 's' : ''} attached
        </p>
      )}
    </div>
  )
}
