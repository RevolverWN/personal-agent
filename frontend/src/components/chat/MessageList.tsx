import MessageItem from './MessageItem'

interface ToolCall {
  tool: string
  arguments: Record<string, any>
  result: {
    success: boolean
    data: any
    error?: string
  }
}

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
  tool_calls?: ToolCall[]
}

interface MessageListProps {
  messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <p className="text-lg font-medium mb-2">Start a conversation</p>
          <p className="text-sm">Send a message to begin chatting with your AI assistant</p>
          <div className="mt-6 text-xs text-gray-400">
            <p>Try asking:</p>
            <ul className="mt-2 space-y-1">
              <li>"Search for the latest AI news"</li>
              <li>"Calculate 15 * 23 + 100"</li>
              <li>"What time is it now?"</li>
              <li>"Execute: print('Hello World')"</li>
            </ul>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {messages.map((message, index) => (
        <MessageItem
          key={index}
          role={message.role}
          content={message.content}
          timestamp={message.timestamp}
          toolCalls={message.tool_calls}
        />
      ))}
    </div>
  )
}
