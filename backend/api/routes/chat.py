"""
Chat API Routes
Main endpoints for cross-matching and graph RAG queries

ENDPOINTS:
- POST /chat/query - Main chat endpoint (supports both cross_match and graph_rag)
- POST /chat/cross-match - Dedicated cross-matching endpoint

This module now includes FULL implementation of Graph RAG queries.

FIXES APPLIED:
1. Improved _extract_material_name() with regex patterns
2. Fixed bug: undefined 'result' variable
3. cross_match() now extracts material name from natural language queries
4. Added debug logging for extraction process
"""
import logging
import re
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
            logger.info(f"Extracted material name: '{material_name}' from query: '{request.message}'")
            
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
    
    Automatically extracts material name from natural language queries.
    
    Examples:
        "find epd for concrete c12/15" → "concrete c12/15"
        "match steel beam" → "steel beam"
        "concrete" → "concrete"
    
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
        
        # ✅ CRITICAL FIX: Extract actual material name from natural language query
        extracted_name = _extract_material_name(request.material_name)
        logger.info(f"Extracted material name: '{extracted_name}' from query: '{request.material_name}'")
        
        # Create orchestrator
        logger.info(f"Creating orchestrator with provider: {request.llm_provider or settings.default_llm_provider}")
        orchestrator = AgentOrchestrator(
            llm_provider=request.llm_provider or settings.default_llm_provider,
            include_detailed_info=request.include_details
        )
        
        # Execute workflow with extracted material name
        logger.info(f"Executing cross-match workflow for: {extracted_name}")
        result = await orchestrator.execute_workflow(
            material_name=extracted_name,  # ✅ Use extracted name, not raw query
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


def _extract_material_name(query: str) -> str:
    """
    Extract material name from natural language query
    
    Uses regex patterns to identify material names in various query formats.
    Based on Python app's _parse_material_name() function.
    
    ✅ CORRECTED VERSION with bug fixes and improved patterns
    
    Supports:
        - "Find EPD for Concrete_C12/15" → "Concrete_C12/15"
        - "find epd for concrete c12/15" → "concrete c12/15"
        - "Match Steel_Beam" → "Steel_Beam"
        - "get products for wood" → "wood"
        - "search for masonry brick" → "masonry brick"
        - "concrete" → "concrete"
    
    Args:
        query: User's natural language query
        
    Returns:
        Extracted material name
    """
    query = query.strip()
    
    # Pattern 1: "action [epd/products] for <material>"
    # Matches: "find epd for X", "get products for X", "search for X"
    match = re.search(
        r'(?:find|match|get|search)(?:\s+epd|\s+products?)?\s+for\s+([A-Za-z0-9_/\-\s]+?)(?:\s+with|\s+top|\s+and|$)',
        query,
        re.IGNORECASE
    )
    if match:
        extracted = match.group(1).strip()
        logger.debug(f"Pattern 1 matched: '{query}' → '{extracted}'")
        return extracted
    
    # Pattern 2: "action <material>" (without "for")
    # Matches: "match steel", "get concrete"
    match = re.search(
        r'(?:match|get|search)\s+([A-Za-z0-9_/\-\s]+?)(?:\s+with|\s+top|\s+and|$)',
        query,
        re.IGNORECASE
    )
    if match:
        extracted = match.group(1).strip()
        logger.debug(f"Pattern 2 matched: '{query}' → '{extracted}'")
        return extracted
    
    # Pattern 3: Remove stop words and common phrases
    # For queries that don't match patterns above
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'find', 'search', 'get', 'show', 'me', 'epd', 'products', 'product',
        'material', 'materials', 'what', 'is', 'are', 'tell', 'about'
    }
    
    words = query.split()
    filtered = [w for w in words if w.lower() not in stop_words and len(w) > 1]
    
    if filtered:
        extracted = ' '.join(filtered)
        logger.debug(f"Stop word removal: '{query}' → '{extracted}'")
        return extracted
    
    # Pattern 4: Fallback - return original if nothing else works
    logger.debug(f"No pattern matched, returning original: '{query}'")
    return query