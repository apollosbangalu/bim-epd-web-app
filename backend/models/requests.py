"""
Request Models Module
Pydantic models for API request validation

All API endpoints use these models to validate incoming requests.
Provides automatic validation, type checking, and documentation.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ConfidenceLevel(str, Enum):
    """Confidence levels for matching results"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ChatQueryRequest(BaseModel):
    """
    Request model for chat query endpoint
    
    Used for both Graph RAG queries and Cross-Matching queries
    """
    message: str = Field(
        ...,
        description="User's query message",
        min_length=1,
        max_length=2000,
        examples=["Find EPD products for Concrete_C12/15"]
    )
    
    query_type: str = Field(
        default="cross_match",
        description="Type of query: 'cross_match' or 'graph_rag'",
        examples=["cross_match", "graph_rag"]
    )
    
    llm_provider: Optional[LLMProvider] = Field(
        default=None,
        description="LLM provider to use (defaults to configured provider)"
    )
    
    temperature: float = Field(
        default=0.0,
        description="LLM temperature for creativity (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    stream: bool = Field(
        default=False,
        description="Enable streaming responses"
    )
    
    # NEW FIELD for Graph RAG ontology selection
    ontology: Optional[str] = Field(
        default=None,
        description="Target ontology for graph_rag queries: 'bimtool', 'epd', or 'thesaurus'"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate and sanitize message"""
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v
    
    @field_validator('query_type')
    @classmethod
    def validate_query_type(cls, v: str) -> str:
        """Validate query type"""
        valid_types = ["cross_match", "graph_rag"]
        if v not in valid_types:
            raise ValueError(f"query_type must be one of {valid_types}")
        return v
    
    @field_validator('ontology')
    @classmethod
    def validate_ontology(cls, v: Optional[str]) -> Optional[str]:
        """Validate ontology selection"""
        if v is not None:
            valid_ontologies = ["bimtool", "epd", "thesaurus"]
            if v not in valid_ontologies:
                raise ValueError(f"ontology must be one of {valid_ontologies}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Find EPD products for Concrete_C12/15",
                "query_type": "cross_match",
                "llm_provider": "openai",
                "temperature": 0.0,
                "stream": False,
                "ontology": None
            }
        }


class CrossMatchRequest(BaseModel):
    """
    Request model specifically for cross-matching workflow
    
    Provides more control over the matching process
    """
    material_name: str = Field(
        ...,
        description="BIM material name to find EPD matches for",
        min_length=1,
        max_length=200,
        examples=["Concrete_C12/15", "Steel_Beam_S275", "Glass_Laminated"]
    )
    
    top_n: int = Field(
        default=10,
        description="Number of top matches to return",
        ge=1,
        le=50
    )
    
    min_confidence: Optional[ConfidenceLevel] = Field(
        default=None,
        description="Minimum confidence level filter"
    )
    
    llm_provider: Optional[LLMProvider] = Field(
        default=None,
        description="LLM provider to use"
    )
    
    include_details: bool = Field(
        default=True,
        description="Include comprehensive product details in results"
    )
    
    @field_validator('material_name')
    @classmethod
    def validate_material_name(cls, v: str) -> str:
        """Validate and sanitize material name"""
        v = v.strip()
        if not v:
            raise ValueError("Material name cannot be empty")
        
        # Check for dangerous characters
        dangerous_chars = ["<", ">", "{", "}", ";", "'", '"']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f"Material name contains invalid character: {char}")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "material_name": "Concrete_C12/15",
                "top_n": 10,
                "min_confidence": "MEDIUM",
                "llm_provider": "openai",
                "include_details": True
            }
        }


class GraphRAGQueryRequest(BaseModel):
    """
    Request model for direct Graph RAG queries
    
    Used for querying knowledge graphs directly without cross-matching
    """
    query: str = Field(
        ...,
        description="Natural language query about knowledge graph",
        min_length=1,
        max_length=500,
        examples=["How many concrete products are in the EPD database?"]
    )
    
    ontology: str = Field(
        default="bimtool",
        description="Target ontology: 'bimtool', 'epd', or 'thesaurus'",
        examples=["bimtool", "epd", "thesaurus"]
    )
    
    llm_provider: Optional[LLMProvider] = Field(
        default=None,
        description="LLM provider to use"
    )
    
    @field_validator('ontology')
    @classmethod
    def validate_ontology(cls, v: str) -> str:
        """Validate ontology selection"""
        valid_ontologies = ["bimtool", "epd", "thesaurus"]
        if v not in valid_ontologies:
            raise ValueError(f"ontology must be one of {valid_ontologies}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "How many concrete materials are available?",
                "ontology": "bimtool",
                "llm_provider": "openai"
            }
        }


class ConfigUpdateRequest(BaseModel):
    """
    Request model for updating application configuration
    """
    default_llm_provider: Optional[LLMProvider] = Field(
        default=None,
        description="Default LLM provider"
    )
    
    openai_model: Optional[str] = Field(
        default=None,
        description="OpenAI model name",
        examples=["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"]
    )
    
    anthropic_model: Optional[str] = Field(
        default=None,
        description="Anthropic model name",
        examples=["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]
    )
    
    graphdb_url: Optional[str] = Field(
        default=None,
        description="GraphDB endpoint URL",
        examples=["http://localhost:7200"]
    )
    
    @field_validator('graphdb_url')
    @classmethod
    def validate_graphdb_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate GraphDB URL"""
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("GraphDB URL must start with http:// or https://")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "default_llm_provider": "openai",
                "openai_model": "gpt-4",
                "anthropic_model": "claude-3-5-sonnet-20241022",
                "graphdb_url": "http://localhost:7200"
            }
        }


class HealthCheckRequest(BaseModel):
    """
    Request model for health check endpoint
    """
    check_llm: bool = Field(
        default=False,
        description="Include LLM connectivity check"
    )
    
    check_sparql: bool = Field(
        default=True,
        description="Include SPARQL endpoints check"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "check_llm": False,
                "check_sparql": True
            }
        }