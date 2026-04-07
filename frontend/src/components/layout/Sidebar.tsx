import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PlusIcon, TrashIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline'
import { format } from 'date-fns'

interface Conversation {
  id: string
  title: string | null
  updated_at: string
  message_count: number
}

interface SidebarProps {
  conversations: Conversation[]
  currentConversationId?: string
  onNewChat: () => void
  onDeleteChat: (id: string) => void
  isLoading: boolean
}

export default function Sidebar({
  conversations,
  currentConversationId,
  onNewChat,
  onDeleteChat,
  isLoading,
}: SidebarProps) {
  const navigate = useNavigate()
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      {/* New Chat Button */}
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={onNewChat}
          disabled={isLoading}
          className="w-full flex items-center justify-center space-x-2 btn-primary py-3"
        >
          <PlusIcon className="w-5 h-5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <ChatBubbleLeftIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No conversations yet</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => navigate(`/chat/${conversation.id}`)}
                onMouseEnter={() => setHoveredId(conversation.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={`p-4 cursor-pointer transition-colors group ${
                  currentConversationId === conversation.id
                    ? 'bg-primary-50 border-l-4 border-primary-600'
                    : 'hover:bg-gray-50 border-l-4 border-transparent'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {conversation.title || 'New Conversation'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {format(new Date(conversation.updated_at), 'MMM d, h:mm a')} · {conversation.message_count} messages
                    </p>
                  </div>
                  {hoveredId === conversation.id && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onDeleteChat(conversation.id)
                      }}
                      className="text-gray-400 hover:text-red-600 p-1"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
