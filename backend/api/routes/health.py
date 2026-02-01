"""
Health Check API Routes with Timeout Protection
"""
import logging
import time
import asyncio
from fastapi import APIRouter, HTTPException
from models.responses import HealthCheckResponse, ComponentHealth
from sparql.client import SPARQLClientFactory
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=dict)
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "BIM-EPD Graph RAG API",
        "version": "2.0.0",
        "fuseki_enabled": settings.fuseki_enabled,
        "graphdb_enabled": settings.graphdb_enabled
    }


@router.get("/health/basic", response_model=dict)
async def basic_health_check():
    """
    Fast health check without SPARQL connection tests
    """
    return {
        "status": "healthy",
        "service": "BIM-EPD Graph RAG API",
        "version": "2.0.0",
        "backend": "running",
        "fuseki_configured": settings.fuseki_enabled,
        "graphdb_configured": settings.graphdb_enabled,
        "fuseki_url": settings.fuseki_url if settings.fuseki_enabled else None,
        "graphdb_url": settings.graphdb_url if settings.graphdb_enabled else None,
        "llm_provider": settings.default_llm_provider
    }


@router.get("/health/detailed", response_model=HealthCheckResponse)
async def detailed_health_check():
    """
    Detailed health check with timeout protection
    """
    logger.info("Performing detailed health check")
    
    components = []
    overall_status = "healthy"
    
    try:
        # Add timeout to prevent hanging
        sparql_health = await asyncio.wait_for(
            _check_sparql_health(),
            timeout=15.0  # 15 seconds max for all checks
        )
        components.extend(sparql_health)
        
    except asyncio.TimeoutError:
        logger.error("Health check timed out after 15 seconds")
        components.append(ComponentHealth(
            name="SPARQL Endpoints",
            status="unhealthy",
            message="Health check timed out (no response after 15s)",
            latency_ms=15000.0
        ))
        overall_status = "unhealthy"
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        components.append(ComponentHealth(
            name="SPARQL Endpoints",
            status="unhealthy",
            message=f"Error: {str(e)}",
            latency_ms=0.0
        ))
        overall_status = "unhealthy"
    
    # Determine overall status
    if components:
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
    """Check health of all SPARQL endpoints with timeout per endpoint"""
    components = []
    
    # Create all clients
    clients = [
        ("BIMTool Repository", SPARQLClientFactory.create_bimtool_client()),
        ("EPD Repository", SPARQLClientFactory.create_epd_client()),
        ("Thesaurus Repository", SPARQLClientFactory.create_thesaurus_client())
    ]
    
    # Check each endpoint with individual timeout
    for name, client in clients:
        try:
            component = await asyncio.wait_for(
                _check_sparql_endpoint(name, client),
                timeout=5.0  # 5 seconds per endpoint
            )
            components.append(component)
            
        except asyncio.TimeoutError:
            logger.warning(f"{name} health check timed out")
            components.append(ComponentHealth(
                name=name,
                status="unhealthy",
                message="Timeout (no response after 5s)",
                latency_ms=5000.0
            ))
    
    return components


async def _check_sparql_endpoint(name: str, client) -> ComponentHealth:
    """Check health of a single SPARQL endpoint"""
    start_time = time.time()
    
    try:
        is_healthy = await client.health_check()
        latency = (time.time() - start_time) * 1000
        
        # Get active endpoint info
        active_endpoint = client.get_active_endpoint()
        endpoint_info = f" (using {active_endpoint.upper()})" if active_endpoint else ""
        
        return ComponentHealth(
            name=name,
            status="healthy" if is_healthy else "unhealthy",
            message=f"Accessible{endpoint_info}" if is_healthy else "Not accessible",
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