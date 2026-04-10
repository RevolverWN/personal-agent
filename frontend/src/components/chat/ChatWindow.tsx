import { useEffect, useRef } from 'react'
import { useWebSocket, type WebSocketMessage } from '../../hooks/useWebSocket'
import { useChatStore } from '../../stores/chatStore'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import { v4 as uuidv4 } from 'uuid'
import type { UploadedFile } from './FileUpload'

interface ChatWindowProps {
  conversationId: string
}

export default function ChatWindow({ conversationId }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const {
    messages,
    isStreaming,
    streamingMessageId,
    loadMessages,
    addMessage,
    startStreaming,
    stopStreaming,
    appendToStreamingMessage,
  } = useChatStore()

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load messages when conversation changes
  useEffect(() => {
    loadMessages(conversationId)
  }, [conversationId, loadMessages])

  // Handle WebSocket messages
  const handleWebSocketMessage = (wsMessage: WebSocketMessage) => {
    switch (wsMessage.type) {
      case 'connected':
        console.log('WebSocket connected:', wsMessage.client_id)
        break

      case 'ack':
        // Server acknowledged our message
        console.log('Message acknowledged:', wsMessage.message_id)
        break

      case 'stream_chunk':
        // Append streaming content
        appendToStreamingMessage(wsMessage.content as string)
        break

      case 'stream_end':
        // Streaming finished
        stopStreaming()
        break

      case 'response':
        // Non-streaming response
        addMessage({
          id: uuidv4(),
          role: 'assistant',
          content: wsMessage.content as string,
          timestamp: new Date(),
          model: wsMessage.model as string,
          tokensUsed: wsMessage.tokens_used as number,
        })
        break

      case 'error':
        console.error('WebSocket error:', wsMessage.message)
        stopStreaming()
        addMessage({
          id: uuidv4(),
          role: 'assistant',
          content: `Error: ${wsMessage.message}`,
          timestamp: new Date(),
          error: wsMessage.message as string,
        })
        break
    }
  }

  // WebSocket connection
  const { isConnected, isConnecting, sendMessage } = useWebSocket({
    conversationId,
    onMessage: handleWebSocketMessage,
    onConnect: () => console.log('WebSocket connected'),
    onDisconnect: () => console.log('WebSocket disconnected'),
    onError: (error) => console.error('WebSocket error:', error),
  })

  const handleSendMessage = async (content: string, _files?: UploadedFile[]) => {
    if (!content.trim() || !isConnected) return

    // Add user message to UI
    const userMessageId = uuidv4()
    addMessage({
      id: userMessageId,
      role: 'user',
      content,
      timestamp: new Date(),
    })

    // Create assistant message placeholder
    const assistantMessageId = uuidv4()
    addMessage({
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    })

    // Start streaming
    startStreaming(assistantMessageId)

    // Send via WebSocket
    const sent = sendMessage({
      type: 'chat',
      message: content,
      conversation_id: conversationId,
      stream: true,
    })

    if (!sent) {
      stopStreaming()
      addMessage({
        id: uuidv4(),
        role: 'assistant',
        content: 'Failed to send message. Please check your connection.',
        timestamp: new Date(),
        error: 'Send failed',
      })
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Connection Status */}
      {isConnecting && (
        <div className="bg-yellow-50 text-yellow-700 px-4 py-1 text-sm text-center">
          Connecting...
        </div>
      )}
      {!isConnected && !isConnecting && (
        <div className="bg-red-50 text-red-700 px-4 py-1 text-sm text-center">
          Disconnected. Messages will not be sent.
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList
          messages={messages}
          streamingMessageId={streamingMessageId}
        />
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <MessageInput
          onSend={handleSendMessage}
          isLoading={isStreaming}
          disabled={!isConnected}
          placeholder={isConnected ? 'Type a message...' : 'Waiting for connection...'}
        />
      </div>
    </div>
  )
}
