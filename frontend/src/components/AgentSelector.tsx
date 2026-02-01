/**
 * Agent Selector Component - FIXED VERSION
 * Allows users to select which agent type and LLM provider to use
 * 
 * FIXES APPLIED:
 * - Removed theme.colors.textTertiary (doesn't exist in theme)
 * - Using theme.colors.textSecondary instead
 * - Properly exported AgentConfig interface with displayName
 */
import React, { useState, useEffect } from 'react'
import { useTheme } from '@/contexts/ThemeContext'

export type AgentType = 
  | 'cross_match'      // Cross-ontology matching (5-step workflow)
  | 'bim_materials'    // BIM materials queries
  | 'epd_products'     // EPD products queries
  | 'thesaurus'        // Thesaurus navigation

export type LLMProvider = 'openai' | 'anthropic'

export interface AgentConfig {
  agentType: AgentType
  provider: LLMProvider
  agentName: string      // e.g., "CrossMatch_Openai", "BIMTool_Anthropic"
  displayName: string    // e.g., "Cross-Match (OpenAI GPT-4)"
}

interface AgentSelectorProps {
  onAgentChange: (config: AgentConfig) => void
  defaultAgentType?: AgentType
  defaultProvider?: LLMProvider
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({ 
  onAgentChange,
  defaultAgentType = 'cross_match',
  defaultProvider = 'openai'
}) => {
  const { theme } = useTheme()
  const [agentType, setAgentType] = useState<AgentType>(defaultAgentType)
  const [provider, setProvider] = useState<LLMProvider>(defaultProvider)

  // Agent type definitions matching Python backend
  const agentTypes = [
    {
      value: 'cross_match' as AgentType,
      label: 'Cross-Match Agent',
      description: 'Find EPD products for BIM materials',
      details: '5-step workflow: Extract → Navigate → Search → Evaluate → Rank',
      icon: '🔗'
    },
    {
      value: 'bim_materials' as AgentType,
      label: 'BIM Materials Chat',
      description: 'Query BIM materials database',
      details: 'Direct SPARQL queries on building materials',
      icon: '🏗️'
    },
    {
      value: 'epd_products' as AgentType,
      label: 'EPD Products Chat',
      description: 'Query EPD products database',
      details: 'Search environmental product declarations',
      icon: '🌍'
    },
    {
      value: 'thesaurus' as AgentType,
      label: 'Thesaurus Navigator',
      description: 'Explore concept mappings',
      details: 'Navigate SKOS semantic relationships between BIM and EPD',
      icon: '📚'
    }
  ]

  const providers = [
    { 
      value: 'openai' as LLMProvider, 
      label: 'OpenAI GPT-4',
      model: 'gpt-4-turbo-preview'
    },
    { 
      value: 'anthropic' as LLMProvider, 
      label: 'Anthropic Claude',
      model: 'claude-3-5-sonnet-20241022'
    }
  ]

  // Update agent configuration when selection changes
  useEffect(() => {
    const config = createAgentConfig(agentType, provider)
    onAgentChange(config)
  }, [agentType, provider])

  const createAgentConfig = (type: AgentType, prov: LLMProvider): AgentConfig => {
    let agentName: string
    let displayName: string

    if (type === 'cross_match') {
      // Cross-matching agents: CrossMatch_Openai, CrossMatch_Anthropic
      const providerName = prov.charAt(0).toUpperCase() + prov.slice(1)
      agentName = `CrossMatch_${providerName}`
      displayName = `Cross-Match (${providers.find(p => p.value === prov)?.label})`
    } else {
      // Graph RAG agents: BIMTool_Openai, EPD_Anthropic, etc.
      const ontologyMap = {
        'bim_materials': 'BIMTool',
        'epd_products': 'EPD',
        'thesaurus': 'Thesaurus'
      }
      const ontology = ontologyMap[type]
      const providerName = prov.charAt(0).toUpperCase() + prov.slice(1)
      agentName = `${ontology}_${providerName}`
      displayName = `${agentTypes.find(t => t.value === type)?.label} (${providers.find(p => p.value === prov)?.label})`
    }

    return {
      agentType: type,
      provider: prov,
      agentName,
      displayName
    }
  }

  const currentAgentType = agentTypes.find(t => t.value === agentType)!
  const currentProvider = providers.find(p => p.value === provider)!
  const currentConfig = createAgentConfig(agentType, provider)

  return (
    <div style={{ padding: '16px' }}>
      {/* Agent Type Selection */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ 
          display: 'block',
          color: theme.colors.textSecondary,
          fontSize: '12px',
          fontWeight: 700,
          letterSpacing: '0.5px',
          marginBottom: '10px',
          textTransform: 'uppercase'
        }}>
          Agent Type
        </label>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {agentTypes.map(type => (
            <button
              key={type.value}
              onClick={() => setAgentType(type.value)}
              style={{
                padding: '12px 16px',
                backgroundColor: agentType === type.value 
                  ? `${theme.colors.accentPrimary}20`
                  : theme.colors.bgTertiary,
                border: agentType === type.value
                  ? `2px solid ${theme.colors.accentPrimary}`
                  : `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.md,
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px'
              }}
              onMouseEnter={(e) => {
                if (agentType !== type.value) {
                  e.currentTarget.style.borderColor = theme.colors.accentSecondary
                  e.currentTarget.style.backgroundColor = `${theme.colors.accentSecondary}10`
                }
              }}
              onMouseLeave={(e) => {
                if (agentType !== type.value) {
                  e.currentTarget.style.borderColor = theme.colors.border
                  e.currentTarget.style.backgroundColor = theme.colors.bgTertiary
                }
              }}
            >
              <span style={{ fontSize: '20px' }}>{type.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{
                  color: theme.colors.textPrimary,
                  fontSize: '14px',
                  fontWeight: 600,
                  marginBottom: '4px'
                }}>
                  {type.label}
                </div>
                <div style={{
                  color: theme.colors.textSecondary,
                  fontSize: '12px',
                  marginBottom: '4px'
                }}>
                  {type.description}
                </div>
                <div style={{
                  color: theme.colors.textSecondary,
                  fontSize: '11px',
                  fontStyle: 'italic',
                  opacity: 0.8
                }}>
                  {type.details}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* LLM Provider Selection */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{
          display: 'block',
          color: theme.colors.textSecondary,
          fontSize: '12px',
          fontWeight: 700,
          letterSpacing: '0.5px',
          marginBottom: '10px',
          textTransform: 'uppercase'
        }}>
          LLM Provider
        </label>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {providers.map(prov => (
            <button
              key={prov.value}
              onClick={() => setProvider(prov.value)}
              style={{
                padding: '12px 16px',
                backgroundColor: provider === prov.value
                  ? `${theme.colors.accentPrimary}20`
                  : theme.colors.bgTertiary,
                border: provider === prov.value
                  ? `2px solid ${theme.colors.accentPrimary}`
                  : `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.md,
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                if (provider !== prov.value) {
                  e.currentTarget.style.borderColor = theme.colors.accentSecondary
                  e.currentTarget.style.backgroundColor = `${theme.colors.accentSecondary}10`
                }
              }}
              onMouseLeave={(e) => {
                if (provider !== prov.value) {
                  e.currentTarget.style.borderColor = theme.colors.border
                  e.currentTarget.style.backgroundColor = theme.colors.bgTertiary
                }
              }}
            >
              <div style={{
                color: theme.colors.textPrimary,
                fontSize: '14px',
                fontWeight: 600,
                marginBottom: '4px'
              }}>
                {prov.label}
              </div>
              <div style={{
                color: theme.colors.textSecondary,
                fontSize: '11px',
                fontFamily: 'monospace',
                opacity: 0.8
              }}>
                Model: {prov.model}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Active Agent Display */}
      <div style={{
        padding: '16px',
        backgroundColor: theme.colors.bgTertiary,
        borderRadius: theme.borderRadius.md,
        border: `2px solid ${theme.colors.accentPrimary}`
      }}>
        <div style={{ 
          color: theme.colors.textSecondary, 
          fontSize: '11px',
          fontWeight: 600,
          letterSpacing: '0.5px',
          marginBottom: '8px',
          textTransform: 'uppercase',
          opacity: 0.8
        }}>
          Active Agent
        </div>
        <div style={{ 
          color: theme.colors.accentPrimary,
          fontSize: '16px',
          fontWeight: 700,
          fontFamily: 'monospace',
          marginBottom: '8px',
          wordBreak: 'break-all'
        }}>
          {currentConfig.agentName}
        </div>
        <div style={{
          color: theme.colors.textSecondary,
          fontSize: '12px'
        }}>
          {currentAgentType.icon} {currentAgentType.label}
        </div>
        <div style={{
          color: theme.colors.textSecondary,
          fontSize: '11px',
          marginTop: '4px',
          opacity: 0.8
        }}>
          Powered by {currentProvider.label}
        </div>
      </div>

      {/* Workflow Steps (only for Cross-Match agent) */}
      {agentType === 'cross_match' && (
        <div style={{
          marginTop: '16px',
          padding: '16px',
          backgroundColor: `${theme.colors.accentSecondary}10`,
          borderRadius: theme.borderRadius.md,
          border: `1px solid ${theme.colors.accentSecondary}`
        }}>
          <div style={{
            color: theme.colors.textSecondary,
            fontSize: '12px',
            fontWeight: 600,
            marginBottom: '12px'
          }}>
            5-Step Workflow:
          </div>
          <ol style={{
            color: theme.colors.textSecondary,
            fontSize: '11px',
            paddingLeft: '20px',
            margin: 0,
            lineHeight: '1.6',
            opacity: 0.9
          }}>
            <li>Extract BIM material (9+ fields)</li>
            <li>Navigate thesaurus (semantic mapping)</li>
            <li>Find EPD products (50+ candidates)</li>
            <li>Evaluate similarity (5 dimensions)</li>
            <li>Rank results (exact → close → score)</li>
          </ol>
        </div>
      )}
    </div>
  )
}