import ReactMarkdown from 'react-markdown';
import type { Message } from '../hooks/useChat'
import { SourcesList } from './SourcesList';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isUser = message.role === 'user';

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: '16px',
      gap: '10px',
      alignItems: 'flex-start',
    }}>
      {!isUser && (
            <img
                src="/chat.png"
                alt="Asistente"
                style={{ width: '36px', height: '36px', borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }}
            />
      )}

      <div style={{
        maxWidth: '75%',
        backgroundColor: isUser ? '#000000' : '#FFFFFF',
        color: isUser ? '#FFFFFF' : '#333333',
        padding: '12px 16px',
        borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
        fontSize: '14px',
        lineHeight: '1.6',
      }}>
        {isUser ? (
          <p style={{ margin: 0 }}>{message.content}</p>
        ) : (
          <>
            <ReactMarkdown
              components={{
                p: ({ children }) => <p style={{ margin: '0 0 8px 0' }}>{children}</p>,
                ul: ({ children }) => <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>{children}</ul>,
                ol: ({ children }) => <ol style={{ margin: '8px 0', paddingLeft: '20px' }}>{children}</ol>,
                li: ({ children }) => <li style={{ marginBottom: '4px' }}>{children}</li>,
                strong: ({ children }) => <strong style={{ fontWeight: 600 }}>{children}</strong>,
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer"
                    style={{ color: '#0066CC', textDecoration: 'none' }}>
                    {children}
                  </a>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
            <SourcesList sources={message.sources} />
          </>
        )}
        <p style={{
          fontSize: '10px',
          color: isUser ? 'rgba(255,255,255,0.6)' : '#999',
          margin: '6px 0 0 0',
          textAlign: 'right',
        }}>
          {message.timestamp.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>

      {isUser && (
        <img
            src="/usuario.png"
            alt="Asistente"
            style={{ width: '36px', height: '36px', borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }}
        />
      )}
    </div>
  );
};