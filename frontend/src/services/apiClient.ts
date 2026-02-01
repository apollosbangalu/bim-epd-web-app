/**
 * Enhanced API Client
 * Supports agent selection, workflow tracking, and streaming responses
 */
import axios, { AxiosInstance } from 'axios'

export interface AgentConfig {
  agentType: string
  provider: string
  agentName: string
  displayName: string
}

export interface ChatQueryParams {
  message: string
  agentConfig: AgentConfig
  temperature?: number
  stream?: boolean
}

export interface CrossMatchParams {
  materialName: string
  agentName: string
  provider: string
  topN?: number
  minConfidence?: 'HIGH' | 'MEDIUM' | 'LOW'
  includeDetails?: boolean
}

export interface WorkflowStep {
  step_number: number
  step_name: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  execution_time?: number
  result_summary?: string
  error?: string
  details?: Record<string, any>
}

export interface CrossMatchResponse {
  success: boolean
  bim_material?: any
  concept_mappings?: any
  matches?: any[]
  workflow_steps?: WorkflowStep[]
  total_candidates?: number
  execution_time?: number
  timestamp?: string
  error?: string
}

export interface AgentInfo {
  agent_name: string
  ontology?: string
  display_name?: string
  provider: string
  capabilities: string[]
  example_queries?: string[]
  workflow_steps?: string[]
}

export interface AgentConfigurations {
  graph_rag_agents: AgentInfo[]
  cross_match_agents: AgentInfo[]
  ontology_patterns: Record<string, any>
}

class APIClient {
  private client: AxiosInstance

  constructor() {
    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
    
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 60000, // 60 second timeout for long-running workflows
    })

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data)
        return config
      },
      (error) => {
        console.error('[API] Request error:', error)
        return Promise.reject(error)
      }
    )

    // Add response interceptor for logging
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[API] Response from ${response.config.url}:`, response.data)
        return response
      },
      (error) => {
        console.error('[API] Response error:', error.response?.data || error.message)
        return Promise.reject(error)
      }
    )
  }

  /**
   * Get agent configurations from backend
   * Returns available agents, their capabilities, and query patterns
   */
  async getAgentConfigurations(): Promise<AgentConfigurations> {
    const response = await this.client.get('/config/agents')
    return response.data
  }

  /**
   * Main chat query endpoint
   * Supports both Graph RAG and Cross-Match queries based on agent type
   */
  async chatQuery(params: ChatQueryParams): Promise<any> {
    const { message, agentConfig, temperature = 0.0, stream = false } = params

    const requestData = {
      message,
      query_type: agentConfig.agentType === 'cross_match' ? 'cross_match' : 'graph_rag',
      agent_name: agentConfig.agentName,
      llm_provider: agentConfig.provider,
      temperature,
      stream
    }

    const response = await this.client.post('/chat/query', requestData)
    return response.data
  }

  /**
   * Dedicated cross-matching endpoint
   * Provides full control over the 5-step workflow
   */
  async crossMatch(params: CrossMatchParams): Promise<CrossMatchResponse> {
    const {
      materialName,
      agentName,
      provider,
      topN = 10,
      minConfidence,
      includeDetails = true
    } = params

    try {
      const response = await this.client.post('/chat/cross-match', {
        material_name: materialName,
        agent_name: agentName,
        llm_provider: provider,
        top_n: topN,
        min_confidence: minConfidence,
        include_details: includeDetails
      })

      return response.data
    } catch (error: any) {
      console.error('[API] Cross-match error:', error)
      
      // Return structured error response
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Unknown error occurred',
        workflow_steps: [],
        timestamp: new Date().toISOString()
      }
    }
  }

  /**
   * Graph RAG query for direct ontology queries
   * Use this for BIM materials, EPD products, or thesaurus queries
   */
  async graphRAGQuery(params: {
    query: string
    agentName: string
    provider: string
    ontology: 'bimtool' | 'epd' | 'thesaurus'
  }): Promise<any> {
    const { query, agentName, provider, ontology } = params

    const response = await this.client.post('/chat/query', {
      message: query,
      query_type: 'graph_rag',
      agent_name: agentName,
      llm_provider: provider,
      ontology
    })

    return response.data
  }

  /**
   * Get system configuration
   */
  async getConfig(): Promise<any> {
    const response = await this.client.get('/config')
    return response.data
  }

  /**
   * Health check endpoints
   */
  async getHealth(): Promise<any> {
    const response = await this.client.get('/health')
    return response.data
  }

  async getBasicHealth(): Promise<any> {
    const response = await this.client.get('/health/basic')
    return response.data
  }

  async getDetailedHealth(): Promise<any> {
    const response = await this.client.get('/health/detailed')
    return response.data
  }

  /**
   * WebSocket connection for streaming responses
   * (To be implemented when backend WebSocket is ready)
   */
  createWebSocket(onMessage: (data: any) => void, onError: (error: any) => void): WebSocket | null {
    try {
      const wsUrl = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000') + '/ws/chat'
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('[WebSocket] Connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage(data)
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error)
        onError(error)
      }

      ws.onclose = () => {
        console.log('[WebSocket] Disconnected')
      }

      return ws
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error)
      onError(error)
      return null
    }
  }

  /**
   * Send message through WebSocket
   */
  sendWebSocketMessage(ws: WebSocket, message: any): void {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    } else {
      console.error('[WebSocket] Cannot send message - connection not open')
    }
  }
}

// Export singleton instance
export const apiClient = new APIClient()

// Export types
export type { APIClient }