import { useState, useRef, useCallback } from 'react'
import { PaperClipIcon, XMarkIcon, DocumentIcon, PhotoIcon, CodeBracketIcon } from '@heroicons/react/24/outline'

export interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  content?: string
  blob?: Blob
}

interface FileUploadProps {
  onFilesSelected: (files: UploadedFile[]) => void
  maxFiles?: number
  maxSizeMB?: number
  acceptedTypes?: string[]
}

const MAX_FILE_SIZE_MB = 10
const ACCEPTED_TYPES = [
  'image/*',
  'text/*',
  'application/pdf',
  'application/json',
  'application/javascript',
  'application/typescript',
  '.js',
  '.ts',
  '.jsx',
  '.tsx',
  '.py',
  '.java',
  '.cpp',
  '.c',
  '.h',
  '.go',
  '.rs',
  '.md',
  '.txt',
  '.csv',
  '.yaml',
  '.yml',
  '.xml',
  '.html',
  '.css',
  '.sql',
]

export default function FileUpload({
  onFilesSelected,
  maxFiles = 5,
  maxSizeMB = MAX_FILE_SIZE_MB,
  acceptedTypes = ACCEPTED_TYPES,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<UploadedFile[]>([])
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    if (file.size > maxSizeMB * 1024 * 1024) {
      return `File ${file.name} exceeds ${maxSizeMB}MB limit`
    }
    return null
  }

  const processFiles = useCallback(async (files: FileList | null) => {
    if (!files) return

    setError(null)
    const newFiles: UploadedFile[] = []

    if (selectedFiles.length + files.length > maxFiles) {
      setError(`Maximum ${maxFiles} files allowed`)
      return
    }

    for (const file of Array.from(files)) {
      const validationError = validateFile(file)
      if (validationError) {
        setError(validationError)
        continue
      }

      const uploadedFile: UploadedFile = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        name: file.name,
        size: file.size,
        type: file.type,
        blob: file,
      }

      // Read text files
      if (file.type.startsWith('text/') || 
          file.name.match(/\.(js|ts|jsx|tsx|py|java|cpp|c|h|go|rs|md|txt|csv|yaml|yml|xml|html|css|sql|json)$/)) {
        try {
          const text = await file.text()
          uploadedFile.content = text
        } catch {
          // If reading fails, keep as blob only
        }
      }

      newFiles.push(uploadedFile)
    }

    const updatedFiles = [...selectedFiles, ...newFiles]
    setSelectedFiles(updatedFiles)
    onFilesSelected(updatedFiles)
  }, [selectedFiles, maxFiles, maxSizeMB, onFilesSelected])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    processFiles(e.dataTransfer.files)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    processFiles(e.target.files)
    // Reset input to allow selecting same files again
    e.target.value = ''
  }

  const removeFile = (id: string) => {
    const updatedFiles = selectedFiles.filter(f => f.id !== id)
    setSelectedFiles(updatedFiles)
    onFilesSelected(updatedFiles)
  }

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return <PhotoIcon className="w-5 h-5" />
    if (type.startsWith('text/') || type.includes('json') || type.includes('javascript')) {
      return <CodeBracketIcon className="w-5 h-5" />
    }
    return <DocumentIcon className="w-5 h-5" />
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-2">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-lg p-4 cursor-pointer
          transition-colors duration-200
          ${isDragging 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleInputChange}
          className="hidden"
        />
        
        <div className="flex items-center justify-center space-x-2 text-gray-600">
          <PaperClipIcon className="w-5 h-5" />
          <span className="text-sm">
            {isDragging ? 'Drop files here' : 'Click or drag files to upload'}
          </span>
        </div>
        
        <p className="text-xs text-gray-400 text-center mt-1">
          Max {maxFiles} files, {maxSizeMB}MB each
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          {selectedFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center justify-between bg-gray-50 rounded-lg p-2"
            >
              <div className="flex items-center space-x-2 min-w-0">
                <div className="text-gray-500">
                  {getFileIcon(file.type)}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-700 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.size)}
                    {file.content && ' · Text readable'}
                  </p>
                </div>
              </div>
              
              <button
                onClick={() => removeFile(file.id)}
                className="p-1 hover:bg-gray-200 rounded text-gray-500"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
