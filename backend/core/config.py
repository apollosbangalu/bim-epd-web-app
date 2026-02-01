"""
Core Configuration Module
Manages application settings with Fuseki→GraphDB fallback support
"""
import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with dual triple-store support"""
    
    # Application
    environment: str = "development"
    debug: bool = False
    
    # API
    api_title: str = "BIM-EPD Graph RAG API"
    api_version: str = "2.0.0"
    
    # CORS - use Union to accept both string and list from .env
    cors_origins: Union[str, List[str]] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Fuseki Configuration (Primary)
    fuseki_url: str = "http://localhost:3030"
    fuseki_enabled: bool = True
    fuseki_repository_bimtool: str = "bimtool"
    fuseki_repository_epd: str = "epd"
    fuseki_repository_thesaurus: str = "thesaurus"
    
    # GraphDB Configuration (Fallback)
    graphdb_url: str = "http://localhost:7200"
    graphdb_enabled: bool = True
    graphdb_repository_bimtool: str = "bimtool"
    graphdb_repository_epd: str = "epd"
    graphdb_repository_thesaurus: str = "thesaurus"
    
    # Connection timeout
    graphdb_timeout: int = 30
    
    # LLM Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    
    # Default LLM provider
    default_llm_provider: str = "openai"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://localhost:5173"]
    
    def get_sparql_endpoints(self, repository: str) -> dict:
        """
        Get SPARQL endpoints for a repository with fallback support
        
        Returns dict with primary and fallback endpoints
        """
        endpoints = {}
        
        # Primary: Fuseki
        if self.fuseki_enabled:
            fuseki_repo = getattr(self, f"fuseki_repository_{repository}", repository)
            endpoints["fuseki"] = {
                "url": f"{self.fuseki_url}/{fuseki_repo}/query",
                "type": "fuseki",
                "enabled": True
            }
        
        # Fallback: GraphDB
        if self.graphdb_enabled:
            graphdb_repo = getattr(self, f"graphdb_repository_{repository}", repository)
            endpoints["graphdb"] = {
                "url": f"{self.graphdb_url}/repositories/{graphdb_repo}",
                "type": "graphdb",
                "enabled": True
            }
        
        return endpoints
    
    def get_llm_config(self, provider: str = None):
        """Get LLM configuration for specified provider"""
        provider = provider or self.default_llm_provider
        
        if provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model
            }
        elif provider == "anthropic":
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model
            }
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")


# Global settings instance
settings = Settings()