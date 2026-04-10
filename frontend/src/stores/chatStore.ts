import { create } from 'zustand'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  isStreaming?: boolean
  timestamp: Date
  model?: string
  tokensUsed?: number
  toolCalls?: ToolCall[]
  error?: string
}

export interface ToolCall {
  id: string
  name: string
  arguments: Record<string, unknown>
  result?: unknown
}

export interface Conversation {
  id: string
  title: string | null
  createdAt: Date
  updatedAt: Date
  messages: Message[]
}

interface ChatState {
  // Current conversation
  currentConversationId: string | null
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  streamingMessageId: string | null

  // Conversation list
  conversations: Conversation[]
  conversationsLoading: boolean

  // Actions
  setCurrentConversation: (id: string | null) => void
  loadConversations: () => Promise<void>
  loadMessages: (conversationId: string) => Promise<void>
  createConversation: () => Promise<string | null>
  deleteConversation: (id: string) => Promise<void>

  // Message actions
  addMessage: (message: Message) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  removeMessage: (id: string) => void
  appendToStreamingMessage: (content: string) => void
  startStreaming: (messageId: string) => void
  stopStreaming: () => void
  clearMessages: () => void

  // UI state
  setLoading: (loading: boolean) => void
}

import { api } from '../services/api'

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  currentConversationId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingMessageId: null,
  conversations: [],
  conversationsLoading: false,

  // Conversation actions
  setCurrentConversation: (id) => {
    set({ currentConversationId: id })
    if (id) {
      get().loadMessages(id)
    } else {
      set({ messages: [] })
    }
  },

  loadConversations: async () => {
    set({ conversationsLoading: true })
    try {
      const response = await api.get('/chat/conversations')
      const conversations = response.data.map((c: Record<string, unknown>) => ({
        ...c,
        createdAt: new Date(c.created_at as string),
        updatedAt: new Date(c.updated_at as string),
      }))
      set({ conversations })
    } catch (error) {
      console.error('Failed to load conversations:', error)
    } finally {
      set({ conversationsLoading: false })
    }
  },

  loadMessages: async (conversationId) => {
    set({ isLoading: true })
    try {
      const response = await api.get(`/chat/conversations/${conversationId}/messages`)
      const messages = response.data.map((m: Record<string, unknown>) => ({
        id: String(m.id),
        role: m.role as Message['role'],
        content: String(m.content),
        timestamp: new Date(m.created_at as string),
        model: m.model as string | undefined,
        tokensUsed: m.tokens_used as number | undefined,
      }))
      set({ messages })
    } catch (error) {
      console.error('Failed to load messages:', error)
    } finally {
      set({ isLoading: false })
    }
  },

  createConversation: async () => {
    try {
      const response = await api.post('/chat/conversations')
      const newConversation = {
        ...response.data,
        createdAt: new Date(response.data.created_at),
        updatedAt: new Date(response.data.updated_at),
        messages: [],
      }
      set((state) => ({
        conversations: [newConversation, ...state.conversations],
        currentConversationId: newConversation.id,
      }))
      return newConversation.id
    } catch (error) {
      console.error('Failed to create conversation:', error)
      return null
    }
  },

  deleteConversation: async (id) => {
    try {
      await api.delete(`/chat/conversations/${id}`)
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== id),
        currentConversationId:
          state.currentConversationId === id ? null : state.currentConversationId,
        messages: state.currentConversationId === id ? [] : state.messages,
      }))
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  },

  // Message actions
  addMessage: (message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }))
  },

  updateMessage: (id, updates) => {
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, ...updates } : m
      ),
    }))
  },

  removeMessage: (id) => {
    set((state) => ({
      messages: state.messages.filter((m) => m.id !== id),
    }))
  },

  startStreaming: (messageId) => {
    set({
      isStreaming: true,
      streamingMessageId: messageId,
    })
  },

  stopStreaming: () => {
    set((state) => ({
      isStreaming: false,
      streamingMessageId: null,
      messages: state.messages.map((m) =>
        m.id === state.streamingMessageId
          ? { ...m, isStreaming: false }
          : m
      ),
    }))
  },

  appendToStreamingMessage: (content) => {
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === state.streamingMessageId
          ? { ...m, content: m.content + content }
          : m
      ),
    }))
  },

  clearMessages: () => {
    set({ messages: [], streamingMessageId: null, isStreaming: false })
  },

  setLoading: (loading) => {
    set({ isLoading: loading })
  },
}))
