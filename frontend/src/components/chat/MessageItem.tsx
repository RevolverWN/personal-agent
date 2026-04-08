import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { UserIcon } from '@heroicons/react/24/solid'
import { CpuChipIcon } from '@heroicons/react/24/outline'
import { format } from 'date-fns'
import ToolCallDisplay from './ToolCallDisplay'

interface ToolCall {
  tool: string
  arguments: Record<string, unknown>
  result: {
    success: boolean
    data: unknown
    error?: string
  }
}

interface MessageItemProps {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: Date | string
  toolCalls?: ToolCall[]
  isStreaming?: boolean
  model?: string
}

export default function MessageItem({ 
  role, 
  content, 
  timestamp, 
  toolCalls, 
  isStreaming,
  model 
}: MessageItemProps) {
  const isUser = role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-3xl ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser ? 'bg-primary-600 ml-3' : 'bg-gray-200 mr-3'
          }`}
        >
          {isUser ? (
            <UserIcon className="w-5 h-5 text-white" />
          ) : (
            <CpuChipIcon className="w-5 h-5 text-gray-600" />
          )}
        </div>

        {/* Message Content */}
        <div className="flex-1">
          <div
            className={`rounded-2xl px-4 py-3 ${
              isUser
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-900'
            }`}
          >
            {isUser ? (
              <p className="text-sm whitespace-pre-wrap">{content}</p>
            ) : (
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <ReactMarkdown
                  components={{
                    code({ inline, className, children, ...props }: { inline?: boolean; className?: string; children?: React.ReactNode }) {
                      const match = /language-(\w+)/.exec(className || '')
                      return !inline && match ? (
                        <SyntaxHighlighter
                          style={oneDark}
                          language={match[1]}
                          PreTag="div"
                          {...props}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className="bg-gray-200 text-red-600 px-1 py-0.5 rounded text-sm" {...props}>
                          {children}
                        </code>
                      )
                    },
                  }}
                >
                  {content}
                </ReactMarkdown>
              </div>
            )}

            {/* Streaming Indicator */}
            {isStreaming && !isUser && (
              <span className="inline-flex items-center ml-2">
                <span className="animate-pulse text-gray-400">▊</span>
              </span>
            )}

            {/* Timestamp & Model Info */}
            <div className={`flex items-center gap-2 mt-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
              {timestamp && (
                <span className={`text-xs ${isUser ? 'text-primary-200' : 'text-gray-500'}`}>
                  {format(new Date(timestamp), 'h:mm a')}
                </span>
              )}
              {model && !isUser && (
                <span className="text-xs text-gray-400">
                  · {model}
                </span>
              )}
            </div>
          </div>
          
          {/* Tool Calls Display */}
          {!isUser && toolCalls && toolCalls.length > 0 && (
            <ToolCallDisplay toolCalls={toolCalls} />
          )}
        </div>
      </div>
    </div>
  )
}
