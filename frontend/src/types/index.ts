export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface BIMMaterial {
  uri: string
  name: string
  material_asset_name?: string
  description?: string
  keywords?: string
  comment?: string
  primary_category_uri: string
  primary_category_label: string
  secondary_category_uri?: string
  secondary_category_label?: string
  material_class?: string
  subclass?: string
  property_set?: string
}

export interface EPDProduct {
  uri: string
  name: string
  name_detail?: string
  product_type_category?: string
  web_link?: string
  technical_purpose?: string
  technology_description?: string
  location?: string
  total_gwp?: number
}

export interface MatchResult {
  epd_product: EPDProduct
  evaluation: {
    name_similarity: number
    category_alignment: number
    functional_match: number
    technical_compatibility: number
    specificity_match: number
    total_score: number
    explanation: string
  }
  confidence: 'HIGH' | 'MEDIUM' | 'LOW'
  rank: number
}

export interface CrossMatchResponse {
  success: boolean
  bim_material: BIMMaterial
  concept_mappings: any[]
  matches: MatchResult[]
  workflow_steps: any[]
  total_candidates: number
  execution_time: number
  timestamp: string
}