"""
Health Check API Routes
Endpoints for checking system health and component status

Endpoints:
- GET /api/health - Basic health check
- GET /api/health/detailed - Detailed component health status
"""
import logging
import time
from fastapi import APIRouter, HTTPException
from models.responses import HealthCheckResponse, ComponentHealth
from sparql.client import SPARQLClientFactory
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=dict)
async def health_check():
    """
    Basic health check endpoint
    
    Returns:
        Simple health status
    """
    return {
        "status": "healthy",
        "service": "BIM-EPD Graph RAG API",
        "version": "2.0.0"
    }


@router.get("/health/detailed", response_model=HealthCheckResponse)
async def detailed_health_check():
    """
    Detailed health check with component status
    
    Checks:
    - SPARQL endpoints (GraphDB/Fuseki)
    - LLM API availability (optional)
    
    Returns:
        Detailed health check response with all component statuses
    """
    logger.info("Performing detailed health check")
    
    components = []
    overall_status = "healthy"
    
    # Check SPARQL endpoints
    sparql_health = await _check_sparql_health()
    components.extend(sparql_health)
    
    # Determine overall status
    unhealthy_components = [c for c in components if c.status != "healthy"]
    if unhealthy_components:
        if len(unhealthy_components) == len(components):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
    
    return HealthCheckResponse(
        status=overall_status,
        components=components
    )


async def _check_sparql_health() -> list:
    """Check health of all SPARQL endpoints"""
    components = []
    
    # Check BIMTool repository
    bim_client = SPARQLClientFactory.create_bimtool_client()
    components.append(
        await _check_sparql_endpoint(
            name="BIMTool Repository",
            client=bim_client
        )
    )
    
    # Check EPD repository
    epd_client = SPARQLClientFactory.create_epd_client()
    components.append(
        await _check_sparql_endpoint(
            name="EPD Repository",
            client=epd_client
        )
    )
    
    # Check Thesaurus repository
    thesaurus_client = SPARQLClientFactory.create_thesaurus_client()
    components.append(
        await _check_sparql_endpoint(
            name="Thesaurus Repository",
            client=thesaurus_client
        )
    )
    
    return components


async def _check_sparql_endpoint(name: str, client) -> ComponentHealth:
    """Check health of a single SPARQL endpoint"""
    start_time = time.time()
    
    try:
        is_healthy = await client.health_check()
        latency = (time.time() - start_time) * 1000  # Convert to ms
        
        return ComponentHealth(
            name=name,
            status="healthy" if is_healthy else "unhealthy",
            message="Accessible" if is_healthy else "Not accessible",
            latency_ms=latency
        )
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return ComponentHealth(
            name=name,
            status="unhealthy",
            message=f"Error: {str(e)}",
            latency_ms=latency
        )
