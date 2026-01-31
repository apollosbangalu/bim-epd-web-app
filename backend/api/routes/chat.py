"""
Chat API Routes
Main endpoints for cross-matching and graph RAG queries
"""
import logging
from fastapi import APIRouter, HTTPException
from models.requests import ChatQueryRequest, CrossMatchRequest
from agents.orchestrator import AgentOrchestrator
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat/query", response_model=dict)
async def chat_query(request: ChatQueryRequest):
    """
    Main chat query endpoint
    
    Handles both cross-matching and direct graph RAG queries
    based on query_type parameter.
    """
    logger.info(f"Received chat query: {request.message[:50]}...")
    
    try:
        if request.query_type == "cross_match":
            # Extract material name from message
            material_name = _extract_material_name(request.message)
            
            # Create orchestrator
            orchestrator = AgentOrchestrator(
                llm_provider=request.llm_provider or settings.default_llm_provider
            )
            
            # Execute workflow
            result = await orchestrator.execute_workflow(
                material_name=material_name,
                top_n=10
            )
            
            return result
            
        elif request.query_type == "graph_rag":
            # Handle direct graph RAG query
            raise HTTPException(
                status_code=501,
                detail="Graph RAG queries not yet implemented"
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid query_type: {request.query_type}"
            )
    
    except Exception as e:
        logger.error(f"Chat query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/cross-match", response_model=dict)
async def cross_match(request: CrossMatchRequest):
    """
    Dedicated cross-matching endpoint
    
    Provides more control over the matching process with explicit parameters.
    """
    logger.info(f"Cross-matching for material: {request.material_name}")
    
    try:
        # Create orchestrator
        orchestrator = AgentOrchestrator(
            llm_provider=request.llm_provider or settings.default_llm_provider,
            include_detailed_info=request.include_details
        )
        
        # Execute workflow
        result = await orchestrator.execute_workflow(
            material_name=request.material_name,
            top_n=request.top_n,
            min_confidence=request.min_confidence
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Cross-matching failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _extract_material_name(message: str) -> str:
    """
    Extract material name from natural language message
    
    Simple heuristic extraction - can be enhanced with NLP
    """
    # Remove common phrases
    message = message.lower()
    remove_phrases = [
        "find epd for",
        "find epd products for",
        "match",
        "search for",
        "get",
        "show me"
    ]
    
    for phrase in remove_phrases:
        message = message.replace(phrase, "")
    
    material_name = message.strip()
    
    # If still too long or complex, extract key terms
    if len(material_name.split()) > 3:
        # Take the most significant terms (usually material type + grade)
        words = material_name.split()
        material_name = " ".join(words[:3])
    
    return material_name