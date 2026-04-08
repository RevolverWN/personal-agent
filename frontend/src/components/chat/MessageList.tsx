import MessageItem from './MessageItem'
import type { Message } from '../../stores/chatStore'

interface MessageListProps {
  messages: Message[]
  streamingMessageId?: string | null
}

export default function MessageList({ messages, streamingMessageId }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <p className="text-lg font-medium mb-2">Start a conversation</p>
          <p className="text-sm">Send a message to begin chatting with your AI assistant</p>
          <div className="mt-6 text-xs text-gray-400">
            <p>Try asking:</p>
            <ul className="mt-2 space-y-1">
              <li>&quot;Search for the latest AI news&quot;</li>
              <li>&quot;Calculate 15 * 23 + 100&quot;</li>
              <li>&quot;What time is it now?&quot;</li>
              <li>&quot;Execute: print(&apos;Hello World&apos;)&quot;</li>
            </ul>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          role={message.role === 'tool' ? 'assistant' : message.role}
          content={message.content}
          timestamp={message.timestamp}
          toolCalls={message.toolCalls?.map(tc => ({
            tool: tc.name,
            arguments: tc.arguments,
            result: tc.result as { success: boolean; data: unknown; error?: string }
          }))}
          isStreaming={message.id === streamingMessageId}
          model={message.model}
        />
      ))}
    </div>
  )
}
