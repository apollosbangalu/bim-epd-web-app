"""
Chat API Routes
Main endpoints for cross-matching and graph RAG queries

ENDPOINTS:
- POST /chat/query - Main chat endpoint (supports both cross_match and graph_rag)
- POST /chat/cross-match - Dedicated cross-matching endpoint

This module now includes FULL implementation of Graph RAG queries.
"""
import logging
from fastapi import APIRouter, HTTPException
from models.requests import ChatQueryRequest, CrossMatchRequest
from agents.orchestrator import AgentOrchestrator
from agents.graph_rag import GraphRAGAgent
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat/query", response_model=dict)
async def chat_query(request: ChatQueryRequest):
    """
    Main chat query endpoint
    
    Handles both cross-matching and direct graph RAG queries
    based on query_type parameter.
    
    Query Types:
    - cross_match: 5-step workflow to match BIM materials to EPD products
    - graph_rag: Direct queries to individual ontologies (BIMTool, EPD, Thesaurus)
    
    Args:
        request: ChatQueryRequest with message, query_type, and other parameters
        
    Returns:
        Query results (format depends on query_type)
        
    Raises:
        HTTPException: 400 for invalid parameters, 500 for processing errors
    """
    logger.info(f"Received chat query: type={request.query_type}, message={request.message[:50]}...")
    
    try:
        if request.query_type == "cross_match":
            # ============================================================
            # CROSS-MATCHING WORKFLOW
            # ============================================================
            logger.info("Processing cross-match query")
            
            # Extract material name from message
            material_name = _extract_material_name(request.message)
            logger.info(f"Extracted material name: {material_name}")
            
            # Create orchestrator
            orchestrator = AgentOrchestrator(
                llm_provider=request.llm_provider or settings.default_llm_provider
            )
            
            # Execute 5-step workflow
            result = await orchestrator.execute_workflow(
                material_name=material_name,
                top_n=10
            )
            
            logger.info("Cross-match workflow completed successfully")
            return result
            
        elif request.query_type == "graph_rag":
            # ============================================================
            # GRAPH RAG QUERY
            # ============================================================
            logger.info("Processing graph RAG query")
            
            # Validate ontology parameter
            if not hasattr(request, 'ontology') or not request.ontology:
                logger.error("Ontology parameter missing for graph_rag query")
                raise HTTPException(
                    status_code=400,
                    detail="Ontology parameter required for graph_rag queries. Must be 'bimtool', 'epd', or 'thesaurus'"
                )
            
            # Validate ontology value
            valid_ontologies = ['bimtool', 'epd', 'thesaurus']
            if request.ontology not in valid_ontologies:
                logger.error(f"Invalid ontology: {request.ontology}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid ontology '{request.ontology}'. Must be one of: {valid_ontologies}"
                )
            
            logger.info(f"Creating Graph RAG agent for ontology: {request.ontology}")
            
            # Create Graph RAG agent for specified ontology
            agent = GraphRAGAgent(
                ontology=request.ontology,
                llm_provider=request.llm_provider or settings.default_llm_provider
            )
            
            # Execute query
            logger.info(f"Executing query: {request.message[:100]}")
            result = await agent.query(request.message)
            
            if result.get("success"):
                logger.info(f"Graph RAG query completed successfully: {result.get('results_count', 0)} results")
            else:
                logger.warning(f"Graph RAG query failed: {result.get('error', 'unknown error')}")
            
            return result
        
        else:
            # ============================================================
            # INVALID QUERY TYPE
            # ============================================================
            logger.error(f"Invalid query type: {request.query_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid query_type: {request.query_type}. Must be 'cross_match' or 'graph_rag'"
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions (already have proper status codes)
        raise
    
    except Exception as e:
        # Log unexpected errors and return 500
        logger.error(f"Chat query failed with unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/chat/cross-match", response_model=dict)
async def cross_match(request: CrossMatchRequest):
    """
    Dedicated cross-matching endpoint
    
    Provides more control over the matching process with explicit parameters.
    Executes the 5-step workflow:
    1. Extract BIM material data
    2. Navigate thesaurus to find concept mappings
    3. Search EPD products using mapped concepts
    4. Evaluate similarity between BIM material and EPD products
    5. Rank and return top matches
    
    Args:
        request: CrossMatchRequest with material_name and matching parameters
        
    Returns:
        CrossMatchResponse with matches and workflow details
        
    Raises:
        HTTPException: 400 for invalid input, 500 for processing errors
    """
    logger.info(f"Received cross-match request: material_name={request.material_name}")
    
    try:
        # Validate material name
        if not request.material_name or len(request.material_name.strip()) == 0:
            logger.error("Empty material name provided")
            raise HTTPException(
                status_code=400,
                detail="Material name cannot be empty"
            )
        
        # Create orchestrator
        logger.info(f"Creating orchestrator with provider: {request.llm_provider or settings.default_llm_provider}")
        orchestrator = AgentOrchestrator(
            llm_provider=request.llm_provider or settings.default_llm_provider,
            include_detailed_info=request.include_details
        )
        
        # Execute workflow
        logger.info(f"Executing cross-match workflow for: {request.material_name}")
        result = await orchestrator.execute_workflow(
            material_name=request.material_name,
            top_n=request.top_n or 10
        )
        
        logger.info(f"Cross-match completed: {len(result.get('matches', []))} matches found")
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Log and wrap unexpected errors
        logger.error(f"Cross-match failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Cross-matching error: {str(e)}"
        )


def _extract_material_name(message: str) -> str:
    """
    Extract material name from user message
    
    Removes common query phrases to isolate the actual material name.
    
    Args:
        message: User's query message
        
    Returns:
        Extracted material name
        
    Examples:
        "Find EPD for Concrete_C12/15" -> "Concrete_C12/15"
        "Match Steel_Beam" -> "Steel_Beam"
        "concrete" -> "concrete"
    """
    message = message.lower()
    
    # Common phrases to remove
    remove_phrases = [
        "find epd for",
        "find epd products for",
        "find epd",
        "match",
        "search for",
        "get",
        "show me",
        "what is",
        "tell me about",
        "cross-match",
        "cross match"
    ]
    
    for phrase in remove_phrases:
        message = message.replace(phrase, "")
        
    result = result.replace("_", " ")
    return message.strip()