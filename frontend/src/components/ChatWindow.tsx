import { useRef, useEffect, useState, useCallback } from 'react'
import type { KeyboardEvent } from 'react'
import { useChat } from '../hooks/useChat'
import { MessageBubble } from './MessageBubble'
import type { Message } from '../hooks/useChat'

const SUGGESTED_QUESTIONS = [
  '¿Qué opciones de crédito de vivienda tiene Bancolombia?',
  '¿Cuáles son las cuentas de ahorro disponibles?',
  '¿Qué tarjetas de crédito ofrece Bancolombia?',
  '¿Cómo puedo invertir mi dinero con Bancolombia?',
  '¿Qué seguros ofrece Bancolombia?',
]

interface SavedConversation {
  id: string
  title: string
  date: string
  messages: Message[]
}

const CONVERSATIONS_KEY = 'bancolombia_conversations'
 

export const ChatWindow = () => {
  const { messages, isLoading, error, sendQuery, clearChat, conversationId, loadConversation } = useChat()
  const [input, setInput] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeConvId, setActiveConvId] = useState<string | undefined>(undefined)
  const [savedConversations, setSavedConversations] = useState<SavedConversation[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(CONVERSATIONS_KEY) || '[]')
    } catch { return [] }
  })
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const isViewingHistory = useRef(false)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Actualiza activeConvId solo cuando viene del agente (no de historial)
  useEffect(() => {
    if (conversationId && !isViewingHistory.current) {
      setActiveConvId(conversationId)
    }
  }, [conversationId])

  // Guarda conversación en historial solo cuando NO estamos viendo historial : 20mb
  const MAX_CONVERSATIONS = 20
  useEffect(() => {
    if (isViewingHistory.current) return
    if (messages.length > 0 && conversationId) {
      const firstUserMsg = messages.find(m => m.role === 'user')
      const title = (firstUserMsg?.content.slice(0, 40) || 'Conversación') + '...'
      setSavedConversations(prev => {
        const updated = prev.some(c => c.id === conversationId)
          ? prev.map(c => c.id === conversationId ? { ...c, messages } : c)
          : [{ id: conversationId, title, date: new Date().toLocaleDateString('es-CO'), messages }, ...prev]
        const trimmed = updated.slice(0, MAX_CONVERSATIONS)
        localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(trimmed))
        return trimmed
      })
    }
  }, [messages, conversationId])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return
    // Si estamos viendo historial, salimos del modo historial
    if (isViewingHistory.current) {
      isViewingHistory.current = false
    }
    const query = input.trim()
    setInput('')
    await sendQuery(query)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    isViewingHistory.current = false
    clearChat()
    setInput('')
    setActiveConvId(undefined)
  }

  const handleLoadConversation = useCallback((conv: SavedConversation) => {
    isViewingHistory.current = true
    // Carga los mensajes exactos de esta conversación desde el localStorage
    const stored = JSON.parse(localStorage.getItem(CONVERSATIONS_KEY) || '[]')
    const found = stored.find((c: SavedConversation) => c.id === conv.id)
    const msgs = found ? found.messages : conv.messages
    loadConversation(msgs.map((m: Message) => ({ ...m, timestamp: new Date(m.timestamp) })), conv.id)
    setActiveConvId(conv.id)
  }, [loadConversation])

  const deleteConversation = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setSavedConversations(prev => {
      const updated = prev.filter(c => c.id !== id)
      localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(updated))
      return updated
    })
    if (activeConvId === id) {
      isViewingHistory.current = false
      clearChat()
      setActiveConvId(undefined)
    }
  }, [activeConvId, clearChat])

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      fontFamily: "'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif",
      backgroundColor: '#F5F5F5',
    }}>

      {/* ── SIDEBAR ── */}
      <div style={{
        width: sidebarOpen ? '260px' : '0px',
        minWidth: sidebarOpen ? '260px' : '0px',
        backgroundColor: '#2C2C2C',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.3s ease',
        overflow: 'hidden',
        flexShrink: 0,
      }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #333' }}>
          <img src="/bancolombia-logo.png" alt="Grupo Cibest" style={{ width: '140px', height: 'auto' }} />
        </div>

        <div style={{ padding: '12px' }}>
          <button
            onClick={handleNewChat}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#FDDA24',
              color: '#000',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              justifyContent: 'center',
            }}
          >
            + Nueva conversación
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px' }}>

          {savedConversations.length === 0 ? (
            <p style={{ color: '#666', fontSize: '12px', textAlign: 'center', padding: '20px 10px' }}>
              Tus conversaciones aparecerán aquí
            </p>
          ) : (
            <>
              <p style={{ color: '#666', fontSize: '11px', padding: '8px 8px 4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Recientes
              </p>
              {savedConversations.map(conv => (
                <div
                  key={conv.id}
                  onClick={() => handleLoadConversation(conv)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    marginBottom: '4px',
                    backgroundColor: activeConvId === conv.id ? '#333' : 'transparent',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '8px',
                    borderLeft: activeConvId === conv.id ? '3px solid #FDDA24' : '3px solid transparent',
                  }}
                  onMouseOver={e => {
                    if (activeConvId !== conv.id) e.currentTarget.style.backgroundColor = '#222'
                  }}
                  onMouseOut={e => {
                    if (activeConvId !== conv.id) e.currentTarget.style.backgroundColor = 'transparent'
                  }}
                >
                  <div style={{ overflow: 'hidden', flex: 1 }}>
                    <p style={{
                      color: activeConvId === conv.id ? '#FDDA24' : '#FFF',
                      fontSize: '13px',
                      margin: 0,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      fontWeight: activeConvId === conv.id ? 600 : 400,
                    }}>
                      {conv.title}
                    </p>
                    <p style={{ color: '#666', fontSize: '11px', margin: '2px 0 0' }}>
                      {conv.date} · {conv.messages.length} mensajes
                    </p>
                  </div>
                  <button
                    onClick={(e) => deleteConversation(conv.id, e)}
                    style={{
                      backgroundColor: 'transparent',
                      border: 'none',
                      color: '#555',
                      cursor: 'pointer',
                      fontSize: '16px',
                      flexShrink: 0,
                      padding: '2px 6px',
                      borderRadius: '4px',
                    }}
                    onMouseOver={e => (e.currentTarget.style.color = '#FF4444')}
                    onMouseOut={e => (e.currentTarget.style.color = '#555')}
                    title="Eliminar conversación"
                  >
                    ×
                  </button>
                </div>
              ))}
            </>
          )}
        </div>
      </div>

      {/* ── MAIN CHAT ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Header */}
        <div style={{
          backgroundColor: '#000000',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '64px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                color: '#FFF',
                cursor: 'pointer',
                fontSize: '20px',
                padding: '4px 8px',
              }}
            >
              ☰
            </button>
            {!sidebarOpen && (
              <img
                src="/bancolombia-logo.png"
                alt="Bancolombia"
                style={{ width: '100px', height: '40px', objectFit: 'contain' }}
              />
            )}
            <div>
              <p style={{ margin: 0, color: '#FFFFFF', fontWeight: 700, fontSize: '16px' }}>
                Asistente Bancolombia
              </p>
              <p style={{ margin: 0, color: '#FDDA24', fontSize: '12px' }}>
                ● En línea
              </p>
            </div>
          </div>
          {activeConvId && (
            <span style={{ color: '#666', fontSize: '11px' }}>
              ID: {activeConvId.slice(0, 8)}...
            </span>
          )}
        </div>

        {/* Conversation ID bar */}
        {activeConvId && (
          <div style={{
            backgroundColor: '#FDDA24',
            padding: '4px 24px',
            fontSize: '11px',
            color: '#000',
            fontWeight: 500,
          }}>
            Conversación: {activeConvId.slice(0, 8)}...
          </div>
        )}
  
        {/* Messages */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '24px',
          backgroundColor: '#F5F5F5',
          position: 'relative',
        }}>
          {/* Imagen de fondo sutil */}
          <div style={{
            position: 'fixed',
            top: '64px',
            left: sidebarOpen ? '260px' : '0px',
            right: 0,
            bottom: '80px',
            backgroundImage: 'url(/trazo-onda-1.png)',
            backgroundSize: '100%',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
            opacity: 0.10,
            pointerEvents: 'none',
            zIndex: 0,
            transition: 'left 0.3s ease',
          }} />

          {/* Contenido encima de la imagen */}
          <div style={{ position: 'relative', zIndex: 1 }}>
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', marginTop: '40px' }}>
                <img
                  src="/logo.png"
                  alt="Bancolombia"
                  style={{ width: '100px', height: 'auto', margin: '0 auto 20px', display: 'block' }}
                />
                <h2 style={{ color: '#000', margin: '0 0 8px', fontSize: '22px', fontWeight: 700 }}>
                  ¡Hola! Soy el asistente de Bancolombia
                </h2>
                <p style={{ color: '#666', margin: '0 0 32px', fontSize: '14px' }}>
                  Puedo ayudarte con información sobre productos y servicios de Bancolombia
                </p>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: '10px',
                  maxWidth: '700px',
                  margin: '0 auto',
                }}>
                  {SUGGESTED_QUESTIONS.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => sendQuery(q)}
                      style={{
                        backgroundColor: '#FFF',
                        border: '2px solid #FDDA24',
                        borderRadius: '12px',
                        padding: '12px 16px',
                        cursor: 'pointer',
                        fontSize: '13px',
                        color: '#333',
                        textAlign: 'left',
                        transition: 'all 0.2s',
                        fontWeight: 500,
                      }}
                      onMouseOver={e => (e.currentTarget.style.backgroundColor = '#FDDA24')}
                      onMouseOut={e => (e.currentTarget.style.backgroundColor = '#FFF')}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map(message => (
              <MessageBubble key={message.id} message={message} />
            ))}

            {isLoading && (
              <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', marginBottom: '16px' }}>
                <img
                  src="/chat.png"
                  alt="Asistente"
                  style={{ width: '36px', height: '36px', borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }}
                />
                <div style={{
                  backgroundColor: '#FFF', padding: '12px 16px',
                  borderRadius: '18px 18px 18px 4px',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
                  display: 'flex', gap: '6px', alignItems: 'center',
                }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{
                      width: '8px', height: '8px', borderRadius: '50%',
                      backgroundColor: '#FDDA24',
                      animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                    }} />
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div style={{
                backgroundColor: '#FFF3CD', border: '1px solid #FDDA24',
                borderRadius: '8px', padding: '12px 16px',
                color: '#856404', fontSize: '14px', marginBottom: '16px',
              }}>
                ⚠️ {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div style={{
          backgroundColor: '#FFF',
          borderTop: '1px solid #E5E5E5',
          padding: '16px 24px',
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
          flexShrink: 0,
        }}>
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu pregunta sobre productos y servicios de Bancolombia..."
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '12px 16px',
              borderRadius: '24px',
              border: '2px solid #E5E5E5',
              fontSize: '14px',
              outline: 'none',
              backgroundColor: '#F9F9F9',
              color: '#333',
            }}
            onFocus={e => (e.target.style.borderColor = '#FDDA24')}
            onBlur={e => (e.target.style.borderColor = '#E5E5E5')}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            style={{
              backgroundColor: input.trim() && !isLoading ? '#FDDA24' : '#E5E5E5',
              color: '#000',
              border: 'none',
              borderRadius: '50%',
              width: '48px',
              height: '48px',
              cursor: input.trim() && !isLoading ? 'pointer' : 'not-allowed',
              fontSize: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              transition: 'background-color 0.2s',
            }}
          >
            ➤
          </button>
        </div>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-8px); }
        }
      `}</style>
    </div>
  )
}