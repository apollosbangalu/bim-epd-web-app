/**
 * Main Application Component
 * Integrates agent selection, workflow visualization, detailed information display, and chat interface
 * 
 * NEW: Supports Step 6 - Detailed Information Agent
 */
import React, { useState, useEffect } from 'react'
import { ThemeProvider } from './contexts/ThemeContext'
import { TopNav } from './components/layout/TopNav'
import { Sidebar } from './components/layout/Sidebar'
import { ChatWindow } from './components/chat/ChatWindow'
import { ChatInput } from './components/chat/ChatInput'
import { AgentSelector, type AgentConfig } from './components/AgentSelector'
import { WorkflowProgress, type WorkflowStep } from './components/WorkflowProgress'
import { DetailedInformationDisplay } from './components/DetailedInformationDisplay'
import { apiClient, type CrossMatchResponse } from './services/apiClient'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  workflowSteps?: WorkflowStep[]
  matchResults?: any[]
  bimMaterial?: any  // NEW: Store BIM material for detailed info display
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [agentConfig, setAgentConfig] = useState<AgentConfig>({
    agentType: 'cross_match',
    provider: 'openai',
    agentName: 'CrossMatch_Openai',
    displayName: 'Cross-Match (OpenAI GPT-4)'
  })
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowStep[]>([])
  const [currentStep, setCurrentStep] = useState(0)
  const [currentMaterialName, setCurrentMaterialName] = useState<string>('')
  
  // NEW: State for detailed information toggle
  const [includeDetailedInfo, setIncludeDetailedInfo] = useState(true)  // Default: enabled

  // Initialize workflow steps (conditionally include Step 6)
  useEffect(() => {
    if (agentConfig.agentType === 'cross_match') {
      const baseSteps: WorkflowStep[] = [
        { step_number: 1, step_name: 'BIM Material Extraction', status: 'pending' },
        { step_number: 2, step_name: 'Thesaurus Navigation', status: 'pending' },
        { step_number: 3, step_name: 'EPD Product Search', status: 'pending' },
        { step_number: 4, step_name: 'Similarity Evaluation', status: 'pending' },
        { step_number: 5, step_name: 'Ranking & Filtering', status: 'pending' }
      ]
      
      // Add Step 6 if detailed info is enabled
      if (includeDetailedInfo) {
        baseSteps.push({
          step_number: 6,
          step_name: 'Detailed Information',
          status: 'pending'
        })
      }
      
      setCurrentWorkflow(baseSteps)
    } else {
      setCurrentWorkflow([])
    }
  }, [agentConfig.agentType, includeDetailedInfo])

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isProcessing) return

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setIsProcessing(true)

    try {
      // Route to appropriate endpoint based on agent type
      if (agentConfig.agentType === 'cross_match') {
        await handleCrossMatchQuery(message)
      } else {
        await handleGraphRAGQuery(message)
      }
    } catch (error: any) {
      console.error('Message handling error:', error)
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error.message || 'An unexpected error occurred'}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsProcessing(false)
      setCurrentStep(0)
      setCurrentMaterialName('')
    }
  }

  const handleCrossMatchQuery = async (message: string) => {
    // Extract material name from message
    const materialName = extractMaterialName(message)
    setCurrentMaterialName(materialName)

    // Reset and start workflow - include Step 6 if detailed info is enabled
    const initialSteps: WorkflowStep[] = [
      { step_number: 1, step_name: 'BIM Material Extraction', status: 'pending' },
      { step_number: 2, step_name: 'Thesaurus Navigation', status: 'pending' },
      { step_number: 3, step_name: 'EPD Product Search', status: 'pending' },
      { step_number: 4, step_name: 'Similarity Evaluation', status: 'pending' },
      { step_number: 5, step_name: 'Ranking & Filtering', status: 'pending' }
    ]
    
    // Add Step 6 if detailed info is enabled
    if (includeDetailedInfo) {
      initialSteps.push({
        step_number: 6,
        step_name: 'Detailed Information',
        status: 'pending'
      })
    }
    
    setCurrentWorkflow(initialSteps)
    setCurrentStep(1)

    // Simulate workflow progress (in real implementation, this would come from WebSocket or polling)
    const totalSteps = includeDetailedInfo ? 6 : 5
    const progressInterval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < totalSteps) {
          return prev + 1
        }
        clearInterval(progressInterval)
        return prev
      })
    }, 2000) // Update every 2 seconds

    try {
      // Call cross-match API with detailed info flag
      const response: CrossMatchResponse = await apiClient.crossMatch({
        materialName,
        agentName: agentConfig.agentName,
        provider: agentConfig.provider,
        topN: 10,
        includeDetails: includeDetailedInfo  // ✅ Pass detailed info flag
      })

      clearInterval(progressInterval)

      if (response.success) {
        // Update workflow with actual steps from response
        if (response.workflow_steps) {
          setCurrentWorkflow(response.workflow_steps)
          setCurrentStep(response.workflow_steps.length)
        }

        // Format response message
        const resultMessage = formatCrossMatchResponse(response)
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: resultMessage,
          timestamp: new Date(),
          workflowSteps: response.workflow_steps,
          matchResults: response.matches,
          bimMaterial: response.bim_material  // ✅ Store BIM material for detailed display
        }
        setMessages((prev) => [...prev, assistantMessage])
      } else {
        throw new Error(response.error || 'Cross-match failed')
      }
    } catch (error: any) {
      clearInterval(progressInterval)
      throw error
    }
  }

  const handleGraphRAGQuery = async (message: string) => {
    // Determine ontology from agent type
    const ontologyMap = {
      'bim_materials': 'bimtool',
      'epd_products': 'epd',
      'thesaurus': 'thesaurus'
    } as const

    const ontology = ontologyMap[agentConfig.agentType as keyof typeof ontologyMap] || 'bimtool'

    try {
      const response = await apiClient.graphRAGQuery({
        query: message,
        agentName: agentConfig.agentName,
        provider: agentConfig.provider,
        ontology
      })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: formatGraphRAGResponse(response),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error: any) {
      throw error
    }
  }

  const extractMaterialName = (message: string): string => {
    // Simple extraction - remove common phrases
    let materialName = message.toLowerCase()
    const removePhrases = [
      'find epd for',
      'find epd products for',
      'match',
      'search for',
      'get',
      'show me',
      'what is',
      'tell me about'
    ]

    removePhrases.forEach((phrase: string) => {
      materialName = materialName.replace(phrase, '')
    })

    return materialName.trim()
  }

  const formatCrossMatchResponse = (response: CrossMatchResponse): string => {
    if (!response.matches || response.matches.length === 0) {
      return 'No matching EPD products found for the specified material.'
    }

    let result = `Found ${response.matches.length} matching EPD products:\n\n`

    response.matches.slice(0, 5).forEach((match, index) => {
      const product = match.epd_product || match
      const evaluation = match.evaluation || {}
      const score = evaluation.total_score || match.total_score || 0
      const confidence = match.confidence || 'UNKNOWN'

      result += `${index + 1}. ${product.name || 'Unknown Product'}\n`
      result += `   Confidence: ${confidence} (Score: ${(score * 100).toFixed(1)}%)\n`
      
      if (product.product_type_category) {
        result += `   Category: ${product.product_type_category}\n`
      }
      
      if (evaluation.explanation) {
        result += `   ${evaluation.explanation}\n`
      }
      
      result += '\n'
    })

    if (response.matches.length > 5) {
      result += `... and ${response.matches.length - 5} more matches.\n`
    }

    result += `\nTotal candidates evaluated: ${response.total_candidates || 0}\n`
    result += `Execution time: ${response.execution_time?.toFixed(2) || 0}s`

    return result
  }

  const formatGraphRAGResponse = (response: any): string => {
    // Format response from Graph RAG queries
    if (typeof response === 'string') {
      return response
    }

    if (response.results) {
      return JSON.stringify(response.results, null, 2)
    }

    return JSON.stringify(response, null, 2)
  }

  return (
    <ThemeProvider>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <TopNav
          onSemanticClick={() => console.log('Semantic clicked')}
          onGNNClick={() => console.log('GNN clicked')}
          onBDClick={() => console.log('BD clicked')}
          onAPIDocClick={() => window.open('http://localhost:8000/docs', '_blank')}
        />
        
        <div style={{ display: 'flex', flex: 1, marginTop: '60px' }}>
          {/* Sidebar with Agent Selection */}
          <div style={{
            width: sidebarOpen ? '320px' : '0px',
            height: 'calc(100vh - 60px)',
            backgroundColor: '#1a1a1a',
            borderRight: sidebarOpen ? '1px solid #333' : 'none',
            position: 'fixed',
            top: '60px',
            left: 0,
            overflow: 'auto',
            transition: 'width 0.3s ease',
            zIndex: 100,
          }}>
            {sidebarOpen && (
              <div>
                <AgentSelector
                  onAgentChange={setAgentConfig}
                  defaultAgentType="cross_match"
                  defaultProvider="openai"
                />
                
                {/* NEW: Detailed Information Toggle */}
                {agentConfig.agentType === 'cross_match' && (
                  <div style={{
                    padding: '16px',
                    borderTop: '1px solid #333',
                    marginTop: '8px'
                  }}>
                    <label style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      cursor: 'pointer',
                      color: '#e0e0e0',
                      fontSize: '14px'
                    }}>
                      <input
                        type="checkbox"
                        checked={includeDetailedInfo}
                        onChange={(e) => setIncludeDetailedInfo(e.target.checked)}
                        style={{
                          width: '16px',
                          height: '16px',
                          cursor: 'pointer',
                          accentColor: '#00d4ff'
                        }}
                      />
                      <div>
                        <div style={{ fontWeight: 500 }}>Fetch Detailed Info</div>
                        <div style={{ fontSize: '12px', color: '#999', marginTop: '2px' }}>
                          Step 6: Web links, GWP, technical specs (~+2s)
                        </div>
                      </div>
                    </label>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Main Content */}
          <main
            style={{
              flex: 1,
              marginLeft: sidebarOpen ? '320px' : '0px',
              transition: 'margin-left 0.3s ease',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}
          >
            {/* Workflow Progress (only for cross-match) */}
            {agentConfig.agentType === 'cross_match' && isProcessing && currentWorkflow.length > 0 && (
              <div style={{ 
                padding: '16px',
                maxWidth: '1200px',
                margin: '0 auto',
                width: '100%'
              }}>
                <WorkflowProgress
                  steps={currentWorkflow}
                  currentStep={currentStep}
                  materialName={currentMaterialName}
                />
              </div>
            )}

            {/* Chat Window with Detailed Information Display */}
            <div style={{ flex: 1, overflow: 'auto' }}>
              <ChatWindow messages={messages} />
              
              {/* NEW: Detailed Information Display for latest message with results */}
              {messages.length > 0 && (() => {
                const latestMessage = messages[messages.length - 1]
                const hasDetailedInfo = latestMessage.matchResults?.some(
                  (match: any) => match.detailed_info
                )
                
                return hasDetailedInfo && latestMessage.bimMaterial ? (
                  <div style={{ 
                    maxWidth: '1200px',
                    margin: '0 auto',
                    padding: '16px'
                  }}>
                    <DetailedInformationDisplay
                      bimMaterial={latestMessage.bimMaterial}
                      matches={latestMessage.matchResults || []}
                      maxDisplay={5}
                    />
                  </div>
                ) : null
              })()}
            </div>
            
            <ChatInput 
              onSend={handleSendMessage}
            />
          </main>
        </div>

        {/* Sidebar Toggle Button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          style={{
            position: 'fixed',
            top: '70px',
            left: sidebarOpen ? '310px' : '10px',
            zIndex: 101,
            padding: '8px 12px',
            backgroundColor: '#333',
            border: '1px solid #555',
            borderRadius: '4px',
            color: 'white',
            cursor: 'pointer',
            transition: 'left 0.3s ease'
          }}
        >
          {sidebarOpen ? '◀' : '▶'}
        </button>
      </div>
    </ThemeProvider>
  )
}

export default App