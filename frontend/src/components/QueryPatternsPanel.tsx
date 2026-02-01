import React, { useEffect, useState } from 'react'
import { apiClient } from '@/services/apiClient'
import { useTheme } from '@/contexts/ThemeContext'

interface QueryPattern {
  category: string
  examples: string[]
}

interface AgentInfo {
  agent_name: string
  capabilities: string[]
  example_queries?: string[]
  workflow_steps?: string[]
}

export const QueryPatternsPanel: React.FC<{ agentType: string }> = ({ agentType }) => {
  const { theme } = useTheme()
  const [patterns, setPatterns] = useState<QueryPattern[]>([])
  const [agentInfo, setAgentInfo] = useState<AgentInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAgentInfo()
  }, [agentType])

  const loadAgentInfo = async () => {
    try {
      setLoading(true)
      const config = await apiClient.getAgentConfigurations()
      
      // Find matching agent
      const allAgents = [
        ...config.graph_rag_agents,
        ...config.cross_match_agents
      ]
      const agent = allAgents.find((a: AgentInfo) => 
        a.agent_name.toLowerCase().includes(agentType.toLowerCase())
      )
      
      setAgentInfo(agent || null)
      
      // Load patterns for ontology if applicable
      if (agent && agent.example_queries) {
        // Format as query patterns
        setPatterns([{
          category: 'Example Queries',
          examples: agent.example_queries
        }])
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Failed to load agent info:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div style={{ padding: '16px', color: theme.colors.textSecondary }}>
      Loading agent information...
    </div>
  }

  if (!agentInfo) {
    return null
  }

  return (
    <div style={{ 
      padding: '16px',
      backgroundColor: theme.colors.bgSecondary,
      borderRadius: theme.borderRadius.md,
      marginTop: '16px'
    }}>
      <h3 style={{ 
        color: theme.colors.textPrimary,
        fontSize: '14px',
        fontWeight: 600,
        marginBottom: '12px'
      }}>
        {agentInfo.agent_name} Capabilities
      </h3>

      <ul style={{ 
        color: theme.colors.textSecondary,
        fontSize: '12px',
        marginBottom: '16px',
        paddingLeft: '20px'
      }}>
        {agentInfo.capabilities.map((cap, idx) => (
          <li key={idx} style={{ marginBottom: '4px' }}>{cap}</li>
        ))}
      </ul>

      {agentInfo.workflow_steps && (
        <>
          <h4 style={{
            color: theme.colors.textPrimary,
            fontSize: '13px',
            fontWeight: 600,
            marginBottom: '8px'
          }}>
            Workflow Steps:
          </h4>
          <ol style={{
            color: theme.colors.textSecondary,
            fontSize: '11px',
            paddingLeft: '20px'
          }}>
            {agentInfo.workflow_steps.map((step, idx) => (
              <li key={idx} style={{ marginBottom: '4px' }}>{step}</li>
            ))}
          </ol>
        </>
      )}

      {patterns.length > 0 && (
        <>
          <h4 style={{
            color: theme.colors.textPrimary,
            fontSize: '13px',
            fontWeight: 600,
            marginTop: '16px',
            marginBottom: '8px'
          }}>
            Example Queries:
          </h4>
          {patterns.map((pattern, idx) => (
            <div key={idx} style={{ marginBottom: '12px' }}>
              <div style={{
                color: theme.colors.textSecondary,
                fontSize: '11px',
                fontWeight: 600,
                marginBottom: '4px'
              }}>
                {pattern.category}
              </div>
              {pattern.examples.map((example, exIdx) => (
                <div 
                  key={exIdx}
                  style={{
                    padding: '8px',
                    backgroundColor: theme.colors.bgTertiary,
                    borderRadius: theme.borderRadius.sm,
                    color: theme.colors.textSecondary,
                    fontSize: '11px',
                    marginBottom: '4px',
                    fontFamily: 'monospace',
                    cursor: 'pointer'
                  }}
                  onClick={() => {
                    // Copy to clipboard or insert into chat
                    navigator.clipboard.writeText(example)
                  }}
                >
                  {example}
                </div>
              ))}
            </div>
          ))}
        </>
      )}
    </div>
  )
}