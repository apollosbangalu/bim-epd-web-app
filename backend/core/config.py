"""
Core Configuration Module
Manages application settings and environment variables
"""
import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    environment: str = "development"
    debug: bool = False
    
    # API
    api_title: str = "BIM-EPD Graph RAG API"
    api_version: str = "2.0.0"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # GraphDB/Fuseki Configuration
    graphdb_url: str = "http://localhost:7200"
    fuseki_url: str = "http://localhost:3030"
    graphdb_timeout: int = 30
    
    # Repository names
    graphdb_repository_bimtool: str = "bimtool"
    graphdb_repository_epd: str = "epd"
    graphdb_repository_thesaurus: str = "thesaurus"
    
    # LLM Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    
    # Default LLM provider
    default_llm_provider: str = "openai"  # "openai" or "anthropic"
    
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
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    def get_sparql_endpoint(self, repository: str) -> str:
        """Get SPARQL endpoint URL for a repository"""
        # Try GraphDB first
        return f"{self.graphdb_url}/repositories/{repository}"
    
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