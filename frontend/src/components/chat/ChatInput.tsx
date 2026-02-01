/**
 * Enhanced Chat Input Component
 * Supports disabled state and custom placeholder
 * 
 * ENHANCEMENTS:
 * - disabled prop to prevent input during processing
 * - placeholder prop for dynamic placeholder text
 * - Visual feedback for disabled state
 */
import React, { useState, KeyboardEvent } from 'react'
import { useTheme } from '@/contexts/ThemeContext'
import { Send } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSend, 
  disabled = false,
  placeholder = 'Type your message...'
}) => {
  const { theme } = useTheme()
  const [message, setMessage] = useState('')

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message)
      setMessage('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div
      style={{
        padding: '16px 24px',
        backgroundColor: theme.colors.bgSecondary,
        borderTop: `1px solid ${theme.colors.border}`,
      }}
    >
      <div
        style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
        }}
      >
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          style={{
            flex: 1,
            padding: '12px 16px',
            backgroundColor: disabled ? theme.colors.bgTertiary : theme.colors.bgPrimary,
            color: disabled ? theme.colors.textSecondary : theme.colors.textPrimary,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.borderRadius.md,
            fontSize: '14px',
            outline: 'none',
            cursor: disabled ? 'not-allowed' : 'text',
            opacity: disabled ? 0.6 : 1,
            transition: 'all 0.2s',
          }}
          onFocus={(e) => {
            if (!disabled) {
              e.target.style.borderColor = theme.colors.accentPrimary
            }
          }}
          onBlur={(e) => {
            e.target.style.borderColor = theme.colors.border
          }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          style={{
            padding: '12px 20px',
            backgroundColor: disabled || !message.trim() 
              ? theme.colors.bgTertiary 
              : theme.colors.accentPrimary,
            color: disabled || !message.trim()
              ? theme.colors.textSecondary
              : 'white',
            border: 'none',
            borderRadius: theme.borderRadius.md,
            cursor: disabled || !message.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '14px',
            fontWeight: 600,
            transition: 'all 0.2s',
            opacity: disabled || !message.trim() ? 0.5 : 1,
          }}
          onMouseEnter={(e) => {
            if (!disabled && message.trim()) {
              e.currentTarget.style.backgroundColor = theme.colors.accentSecondary
            }
          }}
          onMouseLeave={(e) => {
            if (!disabled && message.trim()) {
              e.currentTarget.style.backgroundColor = theme.colors.accentPrimary
            }
          }}
        >
          <Send size={18} />
          Send
        </button>
      </div>
    </div>
  )
}