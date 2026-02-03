/**
 * Detailed Information Display Component
 * Shows comprehensive BIM and EPD product details after ranking
 * 
 * This component displays:
 * - BIM Material comprehensive details
 * - Top N EPD products with full information
 * - Two URIs: ProcessDataSet URI + Web Link
 * - Total GWP values
 * - Technical specifications
 * 
 * Matches Python app's display_comprehensive_details() output
 */
import React, { useState } from 'react'
import { useTheme } from '@/contexts/ThemeContext'
import { ChevronDown, ChevronRight, ExternalLink, Info } from 'lucide-react'

interface DetailedInfoProps {
  bimMaterial: any
  matches: any[]
  maxDisplay?: number
}

interface DetailedInfo {
  web_link?: string
  total_gwp?: number | string
  name?: string
  name_detail?: string
  product_type_category?: string
  technical_purpose?: string
  technology_description?: string
  location?: string
}

export const DetailedInformationDisplay: React.FC<DetailedInfoProps> = ({
  bimMaterial,
  matches,
  maxDisplay = 5
}) => {
  const { theme } = useTheme()
  const [expandedProducts, setExpandedProducts] = useState<Set<number>>(new Set([0])) // First product expanded by default

  const toggleProduct = (index: number) => {
    const newExpanded = new Set(expandedProducts)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedProducts(newExpanded)
  }

  const formatGWP = (gwp: number | string | undefined): string => {
    if (!gwp) return 'N/A'
    const value = typeof gwp === 'string' ? parseFloat(gwp) : gwp
    if (isNaN(value)) return 'N/A'
    return value.toFixed(2) + ' kg CO₂-eq'
  }

  const truncateText = (text: string | undefined, maxLength: number = 250): string => {
    if (!text) return 'Not specified'
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  // Only show matches that have detailed_info
  const matchesWithDetails = matches
    .slice(0, maxDisplay)
    .filter(match => match.detailed_info)

  if (matchesWithDetails.length === 0) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* BIM Material Section */}
      <div 
        className="rounded-lg p-6"
        style={{ 
          backgroundColor: theme.colors.bgSecondary,
          border: `1px solid ${theme.colors.border}`
        }}
      >
        <div className="flex items-center gap-2 mb-4">
          <Info size={20} style={{ color: theme.colors.accentPrimary }} />
          <h3 
            className="text-lg font-semibold"
            style={{ color: theme.colors.textPrimary }}
          >
            BIM Material - Comprehensive Details
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span style={{ color: theme.colors.textSecondary }}>Material Name:</span>
            <span 
              className="ml-2 font-medium"
              style={{ color: theme.colors.textPrimary }}
            >
              {bimMaterial?.name || 'Unknown'}
            </span>
          </div>
          
          <div>
            <span style={{ color: theme.colors.textSecondary }}>Asset Name:</span>
            <span 
              className="ml-2 font-medium"
              style={{ color: theme.colors.textPrimary }}
            >
              {bimMaterial?.material_asset_name || 'Not specified'}
            </span>
          </div>

          <div>
            <span style={{ color: theme.colors.textSecondary }}>Primary Category:</span>
            <span 
              className="ml-2 font-medium"
              style={{ color: theme.colors.textPrimary }}
            >
              {bimMaterial?.primary_category_label || 'Unknown'}
            </span>
          </div>

          <div>
            <span style={{ color: theme.colors.textSecondary }}>Secondary Category:</span>
            <span 
              className="ml-2 font-medium"
              style={{ color: theme.colors.textPrimary }}
            >
              {bimMaterial?.secondary_category_label || 'Not specified'}
            </span>
          </div>

          {bimMaterial?.keywords && (
            <div className="md:col-span-2">
              <span style={{ color: theme.colors.textSecondary }}>Keywords:</span>
              <span 
                className="ml-2"
                style={{ color: theme.colors.textPrimary }}
              >
                {bimMaterial.keywords}
              </span>
            </div>
          )}

          {bimMaterial?.comment && (
            <div className="md:col-span-2">
              <span style={{ color: theme.colors.textSecondary }}>Definition:</span>
              <p 
                className="mt-1 text-sm"
                style={{ color: theme.colors.textPrimary }}
              >
                {bimMaterial.comment}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* EPD Products Section */}
      <div 
        className="rounded-lg p-6"
        style={{ 
          backgroundColor: theme.colors.bgSecondary,
          border: `1px solid ${theme.colors.border}`
        }}
      >
        <h3 
          className="text-lg font-semibold mb-4"
          style={{ color: theme.colors.textPrimary }}
        >
          Top {matchesWithDetails.length} EPD Products - Comprehensive Details
        </h3>

        <div className="space-y-4">
          {matchesWithDetails.map((match, index) => {
            const detailedInfo: DetailedInfo = match.detailed_info || {}
            const evaluation = match.evaluation || {}
            const isExpanded = expandedProducts.has(index)
            const productUri = match.epd_uri || match.epd_product?.uri || match.epd_product?.raw_data?.uri

            return (
              <div
                key={index}
                className="rounded-lg overflow-hidden"
                style={{ 
                  backgroundColor: theme.colors.bgPrimary,
                  border: `1px solid ${theme.colors.border}`
                }}
              >
                {/* Product Header - Always Visible */}
                <div
                  className="p-4 cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => toggleProduct(index)}
                  style={{ backgroundColor: theme.colors.bgSecondary }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      {isExpanded ? (
                        <ChevronDown size={20} style={{ color: theme.colors.textSecondary }} />
                      ) : (
                        <ChevronRight size={20} style={{ color: theme.colors.textSecondary }} />
                      )}
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span 
                            className="text-base font-semibold"
                            style={{ color: theme.colors.textPrimary }}
                          >
                            Rank #{index + 1}
                          </span>
                          <span
                            className="px-2 py-1 rounded text-xs font-medium"
                            style={{
                              backgroundColor: match.confidence === 'HIGH' 
                                ? 'rgba(34, 197, 94, 0.1)'
                                : match.confidence === 'MEDIUM'
                                ? 'rgba(251, 191, 36, 0.1)'
                                : 'rgba(239, 68, 68, 0.1)',
                              color: match.confidence === 'HIGH'
                                ? '#22c55e'
                                : match.confidence === 'MEDIUM'
                                ? '#fbbf24'
                                : '#ef4444'
                            }}
                          >
                            {match.confidence || 'LOW'}
                          </span>
                        </div>
                        
                        <p 
                          className="text-sm font-medium"
                          style={{ color: theme.colors.textPrimary }}
                        >
                          {detailedInfo.name || match.epd_product?.name || 'Unknown Product'}
                        </p>
                        
                        {detailedInfo.product_type_category && (
                          <p 
                            className="text-xs mt-1"
                            style={{ color: theme.colors.textSecondary }}
                          >
                            {detailedInfo.product_type_category}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="text-right">
                      <p 
                        className="text-lg font-bold"
                        style={{ color: theme.colors.accentPrimary }}
                      >
                        {(match.total_score * 100).toFixed(0)}%
                      </p>
                      <p 
                        className="text-xs"
                        style={{ color: theme.colors.textSecondary }}
                      >
                        Match Score
                      </p>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="p-4 space-y-4">
                    {/* URIs Section - CRITICAL */}
                    <div className="space-y-2">
                      <h4 
                        className="text-sm font-semibold mb-2"
                        style={{ color: theme.colors.textPrimary }}
                      >
                        Product Identifiers
                      </h4>
                      
                      {/* ProcessDataSet URI (Graph Identifier) */}
                      {productUri && (
                        <div className="text-xs">
                          <span style={{ color: theme.colors.textSecondary }}>
                            ProcessDataSet URI:
                          </span>
                          <code 
                            className="block mt-1 p-2 rounded break-all"
                            style={{ 
                              backgroundColor: theme.colors.bgSecondary,
                              color: theme.colors.textPrimary 
                            }}
                          >
                            {productUri}
                          </code>
                        </div>
                      )}

                      {/* Web Link (EPD Online) */}
                      {detailedInfo.web_link && (
                        <div className="text-xs">
                          <span style={{ color: theme.colors.textSecondary }}>
                            EPD Online Link:
                          </span>
                          <a
                            href={detailedInfo.web_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 mt-1 hover:underline"
                            style={{ color: theme.colors.accentPrimary }}
                          >
                            <ExternalLink size={14} />
                            {detailedInfo.web_link}
                          </a>
                        </div>
                      )}
                    </div>

                    {/* Environmental Impact */}
                    {detailedInfo.total_gwp !== undefined && detailedInfo.total_gwp !== null && (
                      <div>
                        <h4 
                          className="text-sm font-semibold mb-2"
                          style={{ color: theme.colors.textPrimary }}
                        >
                          Environmental Impact
                        </h4>
                        <div 
                          className="p-3 rounded"
                          style={{ backgroundColor: theme.colors.bgSecondary }}
                        >
                          <p className="text-xs" style={{ color: theme.colors.textSecondary }}>
                            Total GWP (Global Warming Potential):
                          </p>
                          <p 
                            className="text-lg font-bold"
                            style={{ color: theme.colors.textPrimary }}
                          >
                            {formatGWP(detailedInfo.total_gwp)}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Technical Details */}
                    {(detailedInfo.name_detail || detailedInfo.technical_purpose || 
                      detailedInfo.technology_description || detailedInfo.location) && (
                      <div>
                        <h4 
                          className="text-sm font-semibold mb-2"
                          style={{ color: theme.colors.textPrimary }}
                        >
                          Technical Information
                        </h4>
                        <div className="space-y-2 text-xs">
                          {detailedInfo.name_detail && (
                            <div>
                              <span style={{ color: theme.colors.textSecondary }}>
                                Name Detail:
                              </span>
                              <p style={{ color: theme.colors.textPrimary }}>
                                {detailedInfo.name_detail}
                              </p>
                            </div>
                          )}

                          {detailedInfo.technical_purpose && (
                            <div>
                              <span style={{ color: theme.colors.textSecondary }}>
                                Technical Purpose:
                              </span>
                              <p style={{ color: theme.colors.textPrimary }}>
                                {truncateText(detailedInfo.technical_purpose)}
                              </p>
                            </div>
                          )}

                          {detailedInfo.technology_description && (
                            <div>
                              <span style={{ color: theme.colors.textSecondary }}>
                                Technology Description:
                              </span>
                              <p style={{ color: theme.colors.textPrimary }}>
                                {truncateText(detailedInfo.technology_description)}
                              </p>
                            </div>
                          )}

                          {detailedInfo.location && (
                            <div>
                              <span style={{ color: theme.colors.textSecondary }}>Location:</span>
                              <span 
                                className="ml-2"
                                style={{ color: theme.colors.textPrimary }}
                              >
                                {detailedInfo.location}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Match Evaluation Scores */}
                    <div>
                      <h4 
                        className="text-sm font-semibold mb-2"
                        style={{ color: theme.colors.textPrimary }}
                      >
                        Match Evaluation Scores
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                        {[
                          { key: 'name_similarity', label: 'Name' },
                          { key: 'category_alignment', label: 'Category' },
                          { key: 'functional_match', label: 'Functional' },
                          { key: 'technical_compatibility', label: 'Technical' },
                          { key: 'specificity_match', label: 'Specificity' }
                        ].map(({ key, label }) => {
                          const score = evaluation[key]?.score || 0
                          return (
                            <div 
                              key={key}
                              className="p-2 rounded text-center"
                              style={{ backgroundColor: theme.colors.bgSecondary }}
                            >
                              <p 
                                className="text-xs"
                                style={{ color: theme.colors.textSecondary }}
                              >
                                {label}
                              </p>
                              <p 
                                className="text-lg font-bold"
                                style={{ color: theme.colors.accentPrimary }}
                              >
                                {(score * 100).toFixed(0)}%
                              </p>
                            </div>
                          )
                        })}
                      </div>

                      {match.summary && (
                        <p 
                          className="text-xs mt-3 p-2 rounded"
                          style={{ 
                            backgroundColor: theme.colors.bgSecondary,
                            color: theme.colors.textSecondary 
                          }}
                        >
                          {match.summary}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}