import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import ChatWindow from '../components/chat/ChatWindow'
import Sidebar from '../components/layout/Sidebar'

interface Conversation {
  id: string
  title: string | null
  updated_at: string
  message_count: number
}

export default function Chat() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      const response = await api.get('/chat/conversations')
      setConversations(response.data)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }

  const createNewConversation = async () => {
    setIsLoading(true)
    try {
      const response = await api.post('/chat/conversations')
      const newConversation = response.data
      setConversations([newConversation, ...conversations])
      navigate(`/chat/${newConversation.id}`)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const deleteConversation = async (id: string) => {
    try {
      await api.delete(`/chat/conversations/${id}`)
      setConversations(conversations.filter(c => c.id !== id))
      if (conversationId === id) {
        navigate('/chat')
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] -mx-8 -my-8">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        currentConversationId={conversationId}
        onNewChat={createNewConversation}
        onDeleteChat={deleteConversation}
        isLoading={isLoading}
      />

      {/* Chat Window */}
      <div className="flex-1">
        {conversationId ? (
          <ChatWindow conversationId={conversationId} />
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Start a Conversation
              </h2>
              <p className="text-gray-600 mb-6">
                Select a conversation from the sidebar or create a new one
              </p>
              <button
                onClick={createNewConversation}
                disabled={isLoading}
                className="btn-primary"
              >
                {isLoading ? 'Creating...' : 'New Chat'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
