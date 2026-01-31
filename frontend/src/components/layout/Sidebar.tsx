/**
 * Left Sidebar Component
 * Contains model selection and configuration options
 */
import React, { useState } from 'react'
import { useTheme } from '@/contexts/ThemeContext'
import { ChevronDown, Settings } from 'lucide-react'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const { theme } = useTheme()
  const [selectedModel, setSelectedModel] = useState('openai-gpt4')

  return (
    <aside
      style={{
        width: isOpen ? '280px' : '0px',
        height: 'calc(100vh - 60px)',
        backgroundColor: theme.colors.bgSecondary,
        borderRight: isOpen ? `1px solid ${theme.colors.border}` : 'none',
        position: 'fixed',
        top: '60px',
        left: 0,
        overflow: 'hidden',
        transition: 'width 0.3s ease',
        zIndex: 100,
      }}
    >
      {isOpen && (
        <div style={{ padding: '24px' }}>
          {/* Model Selection Section */}
          <Section title="MODEL SELECTION" theme={theme}>
            <ModelSelector
              value={selectedModel}
              onChange={setSelectedModel}
              theme={theme}
            />
          </Section>

          {/* Configuration Section */}
          <Section title="CONFIGURATION" theme={theme}>
            <ConfigOptions theme={theme} />
          </Section>
        </div>
      )}
    </aside>
  )
}

// Section component
const Section: React.FC<{
  title: string
  theme: any
  children: React.ReactNode
}> = ({ title, theme, children }) => {
  const [isExpanded, setIsExpanded] = useState(true)

  return (
    <div style={{ marginBottom: '24px' }}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px',
          backgroundColor: theme.colors.bgTertiary,
          color: theme.colors.textPrimary,
          border: 'none',
          borderRadius: theme.borderRadius.md,
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: 600,
          marginBottom: '8px',
        }}
      >
        {title}
        <ChevronDown
          size={16}
          style={{
            transform: isExpanded ? 'rotate(0deg)' : 'rotate(-90deg)',
            transition: 'transform 0.2s',
          }}
        />
      </button>

      {isExpanded && (
        <div style={{ padding: '8px 0' }}>
          {children}
        </div>
      )}
    </div>
  )
}

// Model selector component
const ModelSelector: React.FC<{
  value: string
  onChange: (value: string) => void
  theme: any
}> = ({ value, onChange, theme }) => {
  const models = [
    { value: 'openai-gpt4', label: 'OpenAI GPT-4' },
    { value: 'openai-gpt35', label: 'OpenAI GPT-3.5' },
    { value: 'anthropic-claude', label: 'Anthropic Claude 3.5' },
  ]

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{
        width: '100%',
        padding: '10px',
        backgroundColor: theme.colors.bgPrimary,
        color: theme.colors.textPrimary,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius.md,
        fontSize: '14px',
        cursor: 'pointer',
        outline: 'none',
      }}
      title="Select LLM model"
    >
      {models.map((model) => (
        <option key={model.value} value={model.value}>
          {model.label}
        </option>
      ))}
    </select>
  )
}

// Configuration options component
const ConfigOptions: React.FC<{ theme: any }> = ({ theme }) => {
  const [options, setOptions] = useState({
    includeDetails: true,
    minConfidence: 'MEDIUM',
    topN: 10,
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Include Details Toggle */}
      <label
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: theme.colors.textSecondary,
          fontSize: '14px',
          cursor: 'pointer',
        }}
        title="Include comprehensive product details in results"
      >
        <input
          type="checkbox"
          checked={options.includeDetails}
          onChange={(e) =>
            setOptions({ ...options, includeDetails: e.target.checked })
          }
          style={{ cursor: 'pointer' }}
        />
        Include Detailed Info
      </label>

      {/* Minimum Confidence */}
      <div>
        <label
          style={{
            display: 'block',
            color: theme.colors.textSecondary,
            fontSize: '12px',
            marginBottom: '4px',
          }}
          title="Minimum confidence level for results"
        >
          Min Confidence
        </label>
        <select
          value={options.minConfidence}
          onChange={(e) =>
            setOptions({ ...options, minConfidence: e.target.value })
          }
          style={{
            width: '100%',
            padding: '8px',
            backgroundColor: theme.colors.bgPrimary,
            color: theme.colors.textPrimary,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.borderRadius.sm,
            fontSize: '14px',
            cursor: 'pointer',
          }}
        >
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      {/* Top N Results */}
      <div>
        <label
          style={{
            display: 'block',
            color: theme.colors.textSecondary,
            fontSize: '12px',
            marginBottom: '4px',
          }}
          title="Number of results to return"
        >
          Top N Results: {options.topN}
        </label>
        <input
          type="range"
          min="5"
          max="20"
          value={options.topN}
          onChange={(e) =>
            setOptions({ ...options, topN: parseInt(e.target.value) })
          }
          style={{
            width: '100%',
            cursor: 'pointer',
          }}
        />
      </div>
    </div>
  )
}