import { useState, useCallback, useRef } from 'react'
import { sendMessage } from '../services/agentApi'
import type { ChatResponse, Source } from '../services/agentApi'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources: Source[]
  timestamp: Date
}

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [conversationId, setConversationId] = useState<string | undefined>(undefined)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const currentConvId = useRef<string | undefined>(undefined)

  const sendQuery = useCallback(async (query: string) => {
    if (!query.trim()) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
      sources: [],
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    try {
      const response: ChatResponse = await sendMessage({
        query,
        conversation_id: currentConvId.current,
      })

      currentConvId.current = response.conversation_id
      setConversationId(response.conversation_id)

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.response,
        sources: response.sources,
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch {
      setError('Error al conectar con el asistente. Verifica que los servicios estén activos.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const clearChat = useCallback(() => {
    setMessages([])
    setConversationId(undefined)
    currentConvId.current = undefined
    setError(null)
  }, [])

  const loadConversation = useCallback((savedMessages: Message[], savedConvId: string) => {
    setMessages(savedMessages.map(m => ({ ...m, timestamp: new Date(m.timestamp) })))
    setConversationId(savedConvId)
    // No restauramos currentConvId para que preguntas nuevas
    // inicien una nueva sesión en el agente sin el historial viejo
    currentConvId.current = undefined
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendQuery,
    clearChat,
    conversationId,
    loadConversation,
  }
}