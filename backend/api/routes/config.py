"""
Configuration API Routes
Endpoints for application configuration management
"""
import logging
from fastapi import APIRouter, HTTPException
from models.requests import ConfigUpdateRequest
from models.responses import ConfigResponse, LLMConfig, TripleStoreConfig
from core.config import settings
from sparql.client import SPARQLClientFactory

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """
    Get current application configuration
    
    Returns:
        Current configuration including LLM providers and triple store status
    """
    logger.info("Fetching current configuration")
    
    try:
        # Check LLM providers
        llm_providers = []
        
        if settings.openai_api_key:
            llm_providers.append(LLMConfig(
                provider="openai",
                model=settings.openai_model,
                available=True
            ))
        
        if settings.anthropic_api_key:
            llm_providers.append(LLMConfig(
                provider="anthropic",
                model=settings.anthropic_model,
                available=True
            ))
        
        # Check triple store health
        repositories = [
            settings.graphdb_repository_bimtool,
            settings.graphdb_repository_epd,
            settings.graphdb_repository_thesaurus
        ]
        
        # Quick health check
        health_results = await SPARQLClientFactory.health_check_all()
        all_healthy = all(health_results.values())
        
        triple_store = TripleStoreConfig(
            url=settings.graphdb_url,
            repositories=repositories,
            healthy=all_healthy
        )
        
        return ConfigResponse(
            environment=settings.environment,
            llm_providers=llm_providers,
            default_llm_provider=settings.default_llm_provider,
            triple_store=triple_store,
            cors_origins=settings.cors_origins
        )
    
    except Exception as e:
        logger.error(f"Config fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config", response_model=ConfigResponse)
async def update_config(request: ConfigUpdateRequest):
    """
    Update application configuration
    
    Note: Changes are runtime only, not persisted to .env file
    """
    logger.info("Updating configuration")
    
    try:
        # Update settings
        if request.default_llm_provider:
            settings.default_llm_provider = request.default_llm_provider
        
        if request.openai_model:
            settings.openai_model = request.openai_model
        
        if request.anthropic_model:
            settings.anthropic_model = request.anthropic_model
        
        if request.graphdb_url:
            settings.graphdb_url = request.graphdb_url
        
        # Return updated config
        return await get_config()
    
    except Exception as e:
        logger.error(f"Config update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))