import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuthStore } from '../stores/authStore'

export interface WebSocketMessage {
  type: string
  [key: string]: unknown
}

export interface UseWebSocketOptions {
  conversationId?: string
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

export interface UseWebSocketReturn {
  isConnected: boolean
  isConnecting: boolean
  sendMessage: (message: WebSocketMessage) => boolean
  connect: () => void
  disconnect: () => void
  error: string | null
}

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { conversationId, onMessage, onConnect, onDisconnect, onError } = options
  const { token } = useAuthStore()
  
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const MAX_RECONNECT_ATTEMPTS = 5
  const RECONNECT_DELAY = 3000

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setIsConnected(false)
    setIsConnecting(false)
    reconnectAttemptsRef.current = 0
  }, [])

  const connect = useCallback(() => {
    if (!token) {
      setError('No authentication token')
      return
    }
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }
    
    setIsConnecting(true)
    setError(null)
    
    // Build WebSocket URL with token
    const params = new URLSearchParams({ token })
    if (conversationId) {
      params.append('conversation_id', conversationId)
    }
    
    const wsUrl = `${WS_BASE_URL}/ws/chat?${params.toString()}`
    
    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws
      
      ws.onopen = () => {
        setIsConnected(true)
        setIsConnecting(false)
        setError(null)
        reconnectAttemptsRef.current = 0
        onConnect?.()
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          onMessage?.(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }
      
      ws.onclose = (event) => {
        setIsConnected(false)
        setIsConnecting(false)
        onDisconnect?.()
        
        // Attempt reconnection if not closed cleanly and has token
        if (!event.wasClean && token && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current++
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, RECONNECT_DELAY * reconnectAttemptsRef.current)
        }
      }
      
      ws.onerror = (event) => {
        setError('WebSocket error occurred')
        setIsConnecting(false)
        onError?.(event)
      }
    } catch (err) {
      setError('Failed to create WebSocket connection')
      setIsConnecting(false)
    }
  }, [token, conversationId, onConnect, onDisconnect, onError, onMessage])

  const sendMessage = useCallback((message: WebSocketMessage): boolean => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      return false
    }
    
    try {
      wsRef.current.send(JSON.stringify(message))
      return true
    } catch (err) {
      console.error('Failed to send WebSocket message:', err)
      return false
    }
  }, [])

  // Auto-connect when token is available
  useEffect(() => {
    if (token && !isConnected && !isConnecting) {
      connect()
    }
    
    return () => {
      disconnect()
    }
  }, [token, conversationId])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    isConnected,
    isConnecting,
    sendMessage,
    connect,
    disconnect,
    error,
  }
}
