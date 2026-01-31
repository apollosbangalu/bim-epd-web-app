"""
Response and Configuration Models Module
Pydantic models for API responses and configuration management

Includes:
- Response models for all endpoints
- Configuration models for system settings
- Error response models
- Workflow status models
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class StepStatus(str, Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStep(BaseModel):
    """
    Model representing a single step in the 5-step workflow
    """
    step_number: int = Field(description="Step number (1-5)")
    step_name: str = Field(description="Step name")
    status: StepStatus = Field(description="Current status")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Step output data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "step_name": "BIM Material Extraction",
                "status": "completed",
                "data": {"material_name": "Concrete_C12/15"},
                "error": None,
                "started_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:00:05Z"
            }
        }


class BIMMaterialData(BaseModel):
    """BIM material extracted data"""
    uri: str = Field(description="Material URI")
    name: str = Field(description="Material name")
    material_asset_name: Optional[str] = Field(default=None, description="Asset name")
    description: Optional[str] = Field(default=None, description="Description")
    keywords: Optional[str] = Field(default=None, description="Keywords")
    comment: Optional[str] = Field(default=None, description="Material definition comment")
    primary_category_uri: str = Field(description="Primary category URI")
    primary_category_label: str = Field(description="Primary category label")
    secondary_category_uri: Optional[str] = Field(default=None, description="Secondary category URI")
    secondary_category_label: Optional[str] = Field(default=None, description="Secondary category label")
    material_class: Optional[str] = Field(default=None, description="Material class")
    subclass: Optional[str] = Field(default=None, description="Subclass")
    property_set: Optional[str] = Field(default=None, description="Property set")


class ThesaurusMapping(BaseModel):
    """Thesaurus concept mapping"""
    bim_concept: str = Field(description="BIM concept URI")
    bim_label: str = Field(description="BIM concept label")
    epd_concept: str = Field(description="EPD concept URI")
    epd_label: str = Field(description="EPD concept label")
    match_type: str = Field(description="Match type (exactMatch/closeMatch)")
    category_type: str = Field(description="Category type (primary/secondary)")
    confidence: float = Field(description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)


class EPDProductData(BaseModel):
    """EPD product data"""
    uri: str = Field(description="Product URI")
    name: str = Field(description="Product name")
    name_detail: Optional[str] = Field(default=None, description="Name detail")
    product_type_category: Optional[str] = Field(default=None, description="Product type category")
    web_link: Optional[str] = Field(default=None, description="Link to online EPD")
    technical_purpose: Optional[str] = Field(default=None, description="Technical purpose")
    technology_description: Optional[str] = Field(default=None, description="Technology description")
    location: Optional[str] = Field(default=None, description="Location")
    total_gwp: Optional[float] = Field(default=None, description="Total GWP value")


class SimilarityEvaluation(BaseModel):
    """Similarity evaluation results"""
    name_similarity: float = Field(description="Name similarity score", ge=0.0, le=1.0)
    category_alignment: float = Field(description="Category alignment score", ge=0.0, le=1.0)
    functional_match: float = Field(description="Functional match score", ge=0.0, le=1.0)
    technical_compatibility: float = Field(description="Technical compatibility score", ge=0.0, le=1.0)
    specificity_match: float = Field(description="Specificity match score", ge=0.0, le=1.0)
    total_score: float = Field(description="Total weighted score", ge=0.0, le=1.0)
    explanation: str = Field(description="Human-readable explanation")


class MatchResult(BaseModel):
    """Single match result combining EPD product with evaluation"""
    epd_product: EPDProductData = Field(description="EPD product data")
    evaluation: SimilarityEvaluation = Field(description="Similarity evaluation")
    confidence: str = Field(description="Confidence level (HIGH/MEDIUM/LOW)")
    rank: int = Field(description="Rank position in results")


class CrossMatchResponse(BaseModel):
    """
    Complete response for cross-matching request
    
    Contains all 5-step workflow results
    """
    bim_material: BIMMaterialData = Field(description="Extracted BIM material")
    concept_mappings: List[ThesaurusMapping] = Field(description="Thesaurus mappings")
    matches: List[MatchResult] = Field(description="Ranked match results")
    
    workflow_steps: List[WorkflowStep] = Field(description="Detailed workflow steps")
    
    total_candidates: int = Field(description="Total candidates evaluated")
    execution_time: float = Field(description="Total execution time (seconds)")
    timestamp: datetime = Field(description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bim_material": {
                    "uri": "http://example.org/material/Concrete_C12_15",
                    "name": "Concrete_C12/15",
                    "primary_category_label": "Concrete"
                },
                "concept_mappings": [],
                "matches": [],
                "workflow_steps": [],
                "total_candidates": 15,
                "execution_time": 12.5,
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }


class GraphRAGResponse(BaseModel):
    """Response for direct Graph RAG queries"""
    query: str = Field(description="Original query")
    ontology: str = Field(description="Queried ontology")
    answer: str = Field(description="Generated answer")
    sparql_query: Optional[str] = Field(default=None, description="SPARQL query used")
    results_count: Optional[int] = Field(default=None, description="Number of results")
    execution_time: float = Field(description="Execution time (seconds)")
    timestamp: datetime = Field(description="Response timestamp")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Material name cannot be empty",
                "details": {"field": "material_name"},
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }


# ============================================================================
# CONFIGURATION MODELS
# ============================================================================

class LLMConfig(BaseModel):
    """LLM provider configuration"""
    provider: str = Field(description="Provider name (openai/anthropic)")
    model: str = Field(description="Model name")
    available: bool = Field(description="Whether API key is configured")


class TripleStoreConfig(BaseModel):
    """Triple store configuration"""
    url: str = Field(description="Endpoint URL")
    repositories: List[str] = Field(description="Available repositories")
    healthy: bool = Field(description="Health status")


class ConfigResponse(BaseModel):
    """Current application configuration"""
    environment: str = Field(description="Environment (development/production)")
    llm_providers: List[LLMConfig] = Field(description="Configured LLM providers")
    default_llm_provider: str = Field(description="Default LLM provider")
    triple_store: TripleStoreConfig = Field(description="Triple store configuration")
    cors_origins: List[str] = Field(description="Allowed CORS origins")
    
    class Config:
        json_schema_extra = {
            "example": {
                "environment": "development",
                "llm_providers": [
                    {"provider": "openai", "model": "gpt-4", "available": True}
                ],
                "default_llm_provider": "openai",
                "triple_store": {
                    "url": "http://localhost:7200",
                    "repositories": ["bimtool", "epd", "thesaurus"],
                    "healthy": True
                },
                "cors_origins": ["http://localhost:3000"]
            }
        }


# ============================================================================
# HEALTH CHECK MODELS
# ============================================================================

class ComponentHealth(BaseModel):
    """Health status of a system component"""
    name: str = Field(description="Component name")
    status: str = Field(description="Status (healthy/unhealthy)")
    message: Optional[str] = Field(default=None, description="Status message")
    latency_ms: Optional[float] = Field(default=None, description="Response latency in ms")


class HealthCheckResponse(BaseModel):
    """Complete health check response"""
    status: str = Field(description="Overall status (healthy/degraded/unhealthy)")
    components: List[ComponentHealth] = Field(description="Individual component statuses")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "components": [
                    {
                        "name": "graphdb",
                        "status": "healthy",
                        "message": "All repositories accessible",
                        "latency_ms": 15.3
                    },
                    {
                        "name": "llm",
                        "status": "healthy",
                        "message": "OpenAI API accessible",
                        "latency_ms": 234.5
                    }
                ],
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }


# ============================================================================
# WEBSOCKET MODELS
# ============================================================================

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str = Field(description="Message type (step/complete/error)")
    data: Dict[str, Any] = Field(description="Message data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "step",
                "data": {
                    "step_number": 1,
                    "step_name": "BIM Extraction",
                    "status": "completed"
                },
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }