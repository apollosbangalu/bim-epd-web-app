/**
 * Top Navigation Component
 * Fixed header with navigation buttons and theme selector
 */
import React from 'react'
import { useTheme } from '@/contexts/ThemeContext'

interface TopNavProps {
  // Top nav button callbacks
  onSemanticClick: () => void
  onGNNClick: () => void
  onBDClick: () => void
  onAPIDocClick: () => void
}

export const TopNav: React.FC<TopNavProps> = ({
  onSemanticClick,
  onGNNClick,
  onBDClick,
  onAPIDocClick,
}) => {
  const { theme, themeName, setTheme } = useTheme()

  return (
    <nav
      style={{
        height: '60px',
        backgroundColor: theme.colors.bgSecondary,
        borderBottom: `1px solid ${theme.colors.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
      }}
    >
      {/* Logo and Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div
          style={{
            width: '40px',
            height: '40px',
            background: `linear-gradient(135deg, ${theme.colors.accentPrimary}, ${theme.colors.accentSecondary})`,
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 'bold',
            fontSize: '20px',
          }}
        >
          BIM
        </div>
        <h1
          style={{
            margin: 0,
            fontSize: '18px',
            fontWeight: 600,
            color: theme.colors.textPrimary,
          }}
        >
          BIM-EPD Graph RAG
        </h1>
      </div>

      {/* Navigation Buttons */}
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        <NavButton
          onClick={onSemanticClick}
          label="Semantic Based Material"
          tooltip="Search materials using semantic AI matching"
          theme={theme}
        />
        
        <NavButton
          onClick={onGNNClick}
          label="GNN Based Material"
          tooltip="Future: Graph Neural Network based search"
          theme={theme}
          disabled
        />
        
        <NavButton
          onClick={onBDClick}
          label="BD OPTION"
          tooltip="Future: Building Data options"
          theme={theme}
          disabled
        />
        
        <NavButton
          onClick={onAPIDocClick}
          label="API DOC"
          tooltip="View API documentation"
          theme={theme}
        />

        {/* Theme Selector */}
        <select
          value={themeName}
          onChange={(e) => setTheme(e.target.value as 'darkGray' | 'darkNavy')}
          style={{
            padding: '8px 12px',
            backgroundColor: theme.colors.bgTertiary,
            color: theme.colors.textPrimary,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.borderRadius.md,
            cursor: 'pointer',
            outline: 'none',
          }}
          title="Switch theme"
        >
          <option value="darkGray">Dark Gray</option>
          <option value="darkNavy">Dark Navy</option>
        </select>
      </div>
    </nav>
  )
}

// Helper component for nav buttons
const NavButton: React.FC<{
  onClick: () => void
  label: string
  tooltip: string
  theme: any
  disabled?: boolean
}> = ({ onClick, label, tooltip, theme, disabled = false }) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={tooltip}
      style={{
        padding: '8px 16px',
        backgroundColor: disabled ? theme.colors.bgTertiary : 'transparent',
        color: disabled ? theme.colors.textSecondary : theme.colors.textPrimary,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius.md,
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontSize: '14px',
        fontWeight: 500,
        transition: 'all 0.2s',
        opacity: disabled ? 0.5 : 1,
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          e.currentTarget.style.backgroundColor = theme.colors.bgTertiary
          e.currentTarget.style.borderColor = theme.colors.accentPrimary
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled) {
          e.currentTarget.style.backgroundColor = 'transparent'
          e.currentTarget.style.borderColor = theme.colors.border
        }
      }}
    >
      {label}
    </button>
  )
}