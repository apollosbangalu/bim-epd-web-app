/**
 * Chat Window Component
 * Main chat interface with message display
 */
import React, { useRef, useEffect } from 'react'
import { useTheme } from '@/contexts/ThemeContext'
import { ChatMessage } from './ChatMessage'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatWindowProps {
  messages: Message[]
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ messages }) => {
  const { theme } = useTheme()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div
      style={{
        flex: 1,
        overflow: 'auto',
        padding: '24px',
        backgroundColor: theme.colors.bgPrimary,
      }}
    >
      {messages.length === 0 ? (
        <EmptyState theme={theme} />
      ) : (
        <div
          style={{
            maxWidth: '1200px',
            margin: '0 auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  )
}

// Empty state component
const EmptyState: React.FC<{ theme: any }> = ({ theme }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        textAlign: 'center',
      }}
    >
      <h2
        style={{
          color: theme.colors.textPrimary,
          fontSize: '32px',
          fontWeight: 600,
          marginBottom: '16px',
        }}
      >
        Welcome
      </h2>
      <p
        style={{
          color: theme.colors.textSecondary,
          fontSize: '18px',
          marginBottom: '32px',
        }}
      >
        What can I help you with today?
      </p>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          maxWidth: '600px',
        }}
      >
        <ExampleQuery
          text="Find EPD products for Concrete_C12/15"
          theme={theme}
        />
        <ExampleQuery
          text="Search for steel beam materials"
          theme={theme}
        />
        <ExampleQuery
          text="What materials are in the BIM database?"
          theme={theme}
        />
      </div>
    </div>
  )
}

// Example query component
const ExampleQuery: React.FC<{ text: string; theme: any }> = ({ text, theme }) => {
  return (
    <div
      style={{
        padding: '12px 16px',
        backgroundColor: theme.colors.bgSecondary,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius.md,
        color: theme.colors.textSecondary,
        fontSize: '14px',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = theme.colors.accentPrimary
        e.currentTarget.style.color = theme.colors.textPrimary
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = theme.colors.border
        e.currentTarget.style.color = theme.colors.textSecondary
      }}
    >
      {text}
    </div>
  )
}