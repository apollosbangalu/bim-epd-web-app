/**
 * Workflow Progress Component
 * Real-time visualization of the 5-step cross-matching workflow
 * 
 * Displays:
 * - Step status (pending/in_progress/completed/failed)
 * - Step timing and duration
 * - Result summaries
 * - Detailed information (collapsible)
 */
import React, { useState } from 'react'
import { useTheme } from '@/contexts/ThemeContext'
import { Check, Loader, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react'

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

interface WorkflowProgressProps {
  steps: WorkflowStep[]
  currentStep: number
  materialName?: string
}

export const WorkflowProgress: React.FC<WorkflowProgressProps> = ({ 
  steps, 
  currentStep,
  materialName 
}) => {
  const { theme } = useTheme()
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set())

  // Step metadata matching Python implementation
  const stepMetadata = {
    1: {
      title: 'BIM Material Extraction',
      subtitle: 'Extracting comprehensive material data (9+ fields)',
      icon: '📋',
      color: theme.colors.accentPrimary
    },
    2: {
      title: 'Thesaurus Navigation',
      subtitle: 'Finding semantic concept mappings (exactMatch, closeMatch)',
      icon: '🗺️',
      color: '#9333ea'
    },
    3: {
      title: 'EPD Product Search',
      subtitle: 'Retrieving matching environmental products (50+ candidates)',
      icon: '🔍',
      color: '#0891b2'
    },
    4: {
      title: 'Similarity Evaluation',
      subtitle: 'Multi-dimensional scoring (name, category, functional, technical, specificity)',
      icon: '⚖️',
      color: '#ea580c'
    },
    5: {
      title: 'Ranking & Filtering',
      subtitle: 'Prioritizing exact matches, sorting by confidence',
      icon: '🏆',
      color: '#16a34a'
    }
  }

  const toggleStepDetails = (stepNumber: number) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(stepNumber)) {
      newExpanded.delete(stepNumber)
    } else {
      newExpanded.add(stepNumber)
    }
    setExpandedSteps(newExpanded)
  }

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return ''
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`
    return `${seconds.toFixed(2)}s`
  }

  const getStatusIcon = (step: WorkflowStep) => {
    switch (step.status) {
      case 'completed':
        return <Check size={20} color={theme.colors.success} strokeWidth={3} />
      case 'in_progress':
        return (
          <Loader 
            size={20} 
            color={stepMetadata[step.step_number as keyof typeof stepMetadata]?.color || theme.colors.accentPrimary} 
            className="animate-spin" 
          />
        )
      case 'failed':
        return <AlertCircle size={20} color={theme.colors.error} strokeWidth={2} />
      case 'pending':
        return (
          <div style={{
            width: '20px',
            height: '20px',
            borderRadius: '50%',
            border: `2px solid ${theme.colors.border}`,
            backgroundColor: theme.colors.bgTertiary
          }} />
        )
    }
  }

  return (
    <div style={{
      padding: '24px',
      backgroundColor: theme.colors.bgSecondary,
      borderRadius: theme.borderRadius.lg,
      marginBottom: '24px',
      border: `1px solid ${theme.colors.border}`
    }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{
          color: theme.colors.textPrimary,
          fontSize: '18px',
          fontWeight: 700,
          marginBottom: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span>5-Step Cross-Matching Workflow</span>
          <div style={{
            padding: '4px 12px',
            backgroundColor: `${theme.colors.accentPrimary}20`,
            borderRadius: theme.borderRadius.sm,
            fontSize: '12px',
            fontWeight: 600,
            color: theme.colors.accentPrimary
          }}>
            Step {currentStep}/5
          </div>
        </h3>
        
        {materialName && (
          <div style={{
            color: theme.colors.textSecondary,
            fontSize: '14px'
          }}>
            Matching material: <span style={{ 
              fontWeight: 600, 
              color: theme.colors.textPrimary,
              fontFamily: 'monospace'
            }}>
              {materialName}
            </span>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div style={{
        marginBottom: '24px',
        height: '8px',
        backgroundColor: theme.colors.bgTertiary,
        borderRadius: '4px',
        overflow: 'hidden'
      }}>
        <div style={{
          height: '100%',
          width: `${(currentStep / 5) * 100}%`,
          backgroundColor: theme.colors.accentPrimary,
          transition: 'width 0.5s ease-out',
          borderRadius: '4px'
        }} />
      </div>

      {/* Workflow Steps */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {steps.map((step) => {
          const metadata = stepMetadata[step.step_number as keyof typeof stepMetadata]
          const isActive = step.step_number === currentStep
          const isCompleted = step.status === 'completed'
          const isFailed = step.status === 'failed'
          const isPending = step.status === 'pending'
          const isExpanded = expandedSteps.has(step.step_number)

          return (
            <div
              key={step.step_number}
              style={{
                backgroundColor: isActive 
                  ? `${metadata?.color}15`
                  : theme.colors.bgTertiary,
                borderRadius: theme.borderRadius.md,
                border: isActive 
                  ? `2px solid ${metadata?.color}`
                  : `1px solid ${theme.colors.border}`,
                transition: 'all 0.3s ease',
                opacity: isPending ? 0.6 : 1
              }}
            >
              {/* Main Step Content */}
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '16px',
                padding: '16px'
              }}>
                {/* Step Icon/Status */}
                <div style={{
                  minWidth: '32px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <div style={{ fontSize: '24px' }}>
                    {metadata?.icon}
                  </div>
                  {getStatusIcon(step)}
                </div>

                {/* Step Info */}
                <div style={{ flex: 1 }}>
                  {/* Title Row */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '6px',
                    flexWrap: 'wrap'
                  }}>
                    <span style={{
                      color: theme.colors.textSecondary,
                      fontSize: '11px',
                      fontWeight: 700,
                      letterSpacing: '0.5px',
                      textTransform: 'uppercase'
                    }}>
                      Step {step.step_number}
                    </span>
                    <span style={{
                      color: theme.colors.textPrimary,
                      fontSize: '15px',
                      fontWeight: 700
                    }}>
                      {metadata?.title || step.step_name}
                    </span>
                    
                    {/* Duration Badge */}
                    {step.execution_time && (
                      <span style={{
                        padding: '2px 8px',
                        backgroundColor: theme.colors.bgPrimary,
                        borderRadius: theme.borderRadius.sm,
                        fontSize: '11px',
                        color: theme.colors.textSecondary,
                        fontFamily: 'monospace'
                      }}>
                        {formatDuration(step.execution_time)}
                      </span>
                    )}

                    {/* Status Badge */}
                    {isActive && (
                      <span style={{
                        padding: '2px 8px',
                        backgroundColor: `${metadata?.color}30`,
                        color: metadata?.color,
                        borderRadius: theme.borderRadius.sm,
                        fontSize: '11px',
                        fontWeight: 600
                      }}>
                        IN PROGRESS
                      </span>
                    )}
                  </div>

                  {/* Subtitle */}
                  <div style={{
                    color: theme.colors.textSecondary,
                    fontSize: '12px',
                    marginBottom: '8px',
                    lineHeight: '1.5'
                  }}>
                    {metadata?.subtitle}
                  </div>

                  {/* Result Summary */}
                  {step.result_summary && (
                    <div style={{
                      color: theme.colors.textSecondary,
                      fontSize: '12px',
                      padding: '10px 12px',
                      backgroundColor: theme.colors.bgPrimary,
                      borderRadius: theme.borderRadius.sm,
                      marginTop: '8px',
                      border: `1px solid ${theme.colors.border}`
                    }}>
                      ✓ {step.result_summary}
                    </div>
                  )}

                  {/* Error Message */}
                  {step.error && (
                    <div style={{
                      color: theme.colors.error,
                      fontSize: '12px',
                      padding: '10px 12px',
                      backgroundColor: `${theme.colors.error}15`,
                      borderRadius: theme.borderRadius.sm,
                      marginTop: '8px',
                      border: `1px solid ${theme.colors.error}`
                    }}>
                      <strong>Error:</strong> {step.error}
                    </div>
                  )}

                  {/* Details Toggle (only if details available) */}
                  {step.details && isCompleted && (
                    <button
                      onClick={() => toggleStepDetails(step.step_number)}
                      style={{
                        marginTop: '12px',
                        padding: '8px 12px',
                        backgroundColor: theme.colors.bgPrimary,
                        border: `1px solid ${theme.colors.border}`,
                        borderRadius: theme.borderRadius.sm,
                        color: theme.colors.textSecondary,
                        fontSize: '12px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = theme.colors.bgTertiary
                        e.currentTarget.style.borderColor = metadata?.color || theme.colors.accentPrimary
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = theme.colors.bgPrimary
                        e.currentTarget.style.borderColor = theme.colors.border
                      }}
                    >
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      {isExpanded ? 'Hide' : 'Show'} details
                    </button>
                  )}
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && step.details && (
                <div style={{
                  padding: '0 16px 16px 64px'
                }}>
                  <div style={{
                    backgroundColor: theme.colors.bgPrimary,
                    borderRadius: theme.borderRadius.sm,
                    border: `1px solid ${theme.colors.border}`,
                    padding: '12px',
                    maxHeight: '300px',
                    overflow: 'auto'
                  }}>
                    <pre style={{
                      color: theme.colors.textSecondary,
                      fontSize: '11px',
                      fontFamily: 'monospace',
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}>
                      {JSON.stringify(step.details, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Summary Footer */}
      {steps.every(s => s.status !== 'pending') && (
        <div style={{
          marginTop: '20px',
          padding: '16px',
          backgroundColor: theme.colors.bgTertiary,
          borderRadius: theme.borderRadius.md,
          border: `1px solid ${theme.colors.border}`
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px'
          }}>
            <div>
              <div style={{
                color: theme.colors.textSecondary,
                fontSize: '11px',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '4px'
              }}>
                Workflow Status
              </div>
              <div style={{
                color: theme.colors.textPrimary,
                fontSize: '14px',
                fontWeight: 600
              }}>
                {steps.every(s => s.status === 'completed') 
                  ? '✅ All steps completed successfully'
                  : steps.some(s => s.status === 'failed')
                  ? '❌ Workflow failed'
                  : '⏳ Workflow in progress...'}
              </div>
            </div>

            {/* Total Duration */}
            {steps.every(s => s.status === 'completed') && (
              <div>
                <div style={{
                  color: theme.colors.textSecondary,
                  fontSize: '11px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  marginBottom: '4px'
                }}>
                  Total Duration
                </div>
                <div style={{
                  color: theme.colors.accentPrimary,
                  fontSize: '14px',
                  fontWeight: 600,
                  fontFamily: 'monospace'
                }}>
                  {formatDuration(
                    steps.reduce((sum, s) => sum + (s.execution_time || 0), 0)
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}