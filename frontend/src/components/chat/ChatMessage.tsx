import React from 'react'
import { useTheme } from '@/contexts/ThemeContext'

interface ChatMessageProps {
  message: {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
  }
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const { theme } = useTheme()
  const isUser = message.role === 'user'

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '16px',
      }}
    >
      <div
        style={{
          maxWidth: '70%',
          padding: '12px 16px',
          borderRadius: theme.borderRadius.md,
          backgroundColor: isUser ? theme.colors.accentPrimary : theme.colors.bgSecondary,
          color: theme.colors.textPrimary,
          border: `1px solid ${isUser ? theme.colors.accentPrimary : theme.colors.border}`,
        }}
      >
        <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.5' }}>
          {message.content}
        </p>
        <p
          style={{
            margin: '8px 0 0 0',
            fontSize: '12px',
            color: theme.colors.textSecondary,
          }}
        >
          {message.timestamp.toLocaleTimeString()}
        </p>
      </div>
    </div>
  )
}