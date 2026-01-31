import React, { useState } from 'react'
import { useTheme } from '@/contexts/ThemeContext'
import { Send } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend }) => {
  const { theme } = useTheme()
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (input.trim()) {
      onSend(input.trim())
      setInput('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div
      style={{
        height: '80px',
        backgroundColor: theme.colors.bgSecondary,
        borderTop: `1px solid ${theme.colors.border}`,
        padding: '16px',
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
      }}
    >
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Type your message here... (e.g., 'Find EPD for Concrete_C12/15')"
        style={{
          flex: 1,
          padding: '12px 16px',
          backgroundColor: theme.colors.bgPrimary,
          color: theme.colors.textPrimary,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.borderRadius.md,
          fontSize: '14px',
          outline: 'none',
        }}
      />
      <button
        onClick={handleSend}
        disabled={!input.trim()}
        title="Send message"
        style={{
          padding: '12px 24px',
          backgroundColor: input.trim() ? theme.colors.accentPrimary : theme.colors.bgTertiary,
          color: '#fff',
          border: 'none',
          borderRadius: theme.borderRadius.md,
          cursor: input.trim() ? 'pointer' : 'not-allowed',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '14px',
          fontWeight: 500,
          opacity: input.trim() ? 1 : 0.5,
        }}
      >
        <Send size={16} />
        Send
      </button>
    </div>
  )
}