"""
Enhanced Config API Routes - CORRECTED VERSION
Provides agent configurations, query patterns, and system information

FIXES:
- Removed incorrect config imports
- Made it work without needing the full Python app codebase
- Returns mock/example data that you can customize
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/config")
async def get_config():
    """
    Get basic system configuration
    Returns basic API configuration without requiring full settings
    """
    return {
        "api_version": "1.0.0",
        "environment": "development",
        "features": {
            "cross_match": True,
            "graph_rag": True,
            "web_search": False
        },
        "llm_providers": ["openai", "anthropic"],
        "ontologies": ["bimtool", "epd", "thesaurus"]
    }


@router.get("/config/agents")
async def get_agent_configurations():
    """
    Get all agent configurations with capabilities and example queries
    
    This endpoint provides:
    - Available Graph RAG agents (BIMTool, EPD, Thesaurus)
    - Available Cross-Match agents
    - Ontology query patterns
    - Agent capabilities and example queries
    """
    
    # Define Graph RAG agents
    graph_rag_agents = [
        {
            "agent_name": "BIMTool_Openai",
            "ontology": "bimtool",
            "display_name": "BIM Materials (OpenAI)",
            "provider": "openai",
            "capabilities": [
                "Search BIM materials by name",
                "Query material properties",
                "Find materials by category",
                "Get material composition details"
            ],
            "example_queries": [
                "Find concrete materials",
                "What is Concrete_C12/15?",
                "List all materials in category Masonry",
                "Show me materials with density > 2000"
            ]
        },
        {
            "agent_name": "BIMTool_Anthropic",
            "ontology": "bimtool",
            "display_name": "BIM Materials (Anthropic)",
            "provider": "anthropic",
            "capabilities": [
                "Search BIM materials by name",
                "Query material properties",
                "Find materials by category",
                "Get material composition details"
            ],
            "example_queries": [
                "Find concrete materials",
                "What is Concrete_C12/15?",
                "List all materials in category Masonry",
                "Show me materials with density > 2000"
            ]
        },
        {
            "agent_name": "EPD_Openai",
            "ontology": "epd",
            "display_name": "EPD Products (OpenAI)",
            "provider": "openai",
            "capabilities": [
                "Search EPD products by name",
                "Query environmental data",
                "Find products by category",
                "Get LCA information"
            ],
            "example_queries": [
                "Find concrete EPD products",
                "What is the GWP of product X?",
                "List all products in category Concrete",
                "Show EPD products from Germany"
            ]
        },
        {
            "agent_name": "EPD_Anthropic",
            "ontology": "epd",
            "display_name": "EPD Products (Anthropic)",
            "provider": "anthropic",
            "capabilities": [
                "Search EPD products by name",
                "Query environmental data",
                "Find products by category",
                "Get LCA information"
            ],
            "example_queries": [
                "Find concrete EPD products",
                "What is the GWP of product X?",
                "List all products in category Concrete",
                "Show EPD products from Germany"
            ]
        },
        {
            "agent_name": "Thesaurus_Openai",
            "ontology": "thesaurus",
            "display_name": "Thesaurus Navigator (OpenAI)",
            "provider": "openai",
            "capabilities": [
                "Find concept mappings",
                "Navigate semantic relationships",
                "Discover exactMatch and closeMatch",
                "Calculate mapping confidence"
            ],
            "example_queries": [
                "What EPD concepts match BIM concept X?",
                "Find exact matches for Concrete",
                "Show close matches for category Y"
            ]
        },
        {
            "agent_name": "Thesaurus_Anthropic",
            "ontology": "thesaurus",
            "display_name": "Thesaurus Navigator (Anthropic)",
            "provider": "anthropic",
            "capabilities": [
                "Find concept mappings",
                "Navigate semantic relationships",
                "Discover exactMatch and closeMatch",
                "Calculate mapping confidence"
            ],
            "example_queries": [
                "What EPD concepts match BIM concept X?",
                "Find exact matches for Concrete",
                "Show close matches for category Y"
            ]
        }
    ]
    
    # Define Cross-Match agents
    cross_match_agents = [
        {
            "agent_name": "CrossMatch_Openai",
            "display_name": "Cross-Match Workflow (OpenAI)",
            "provider": "openai",
            "workflow_steps": [
                "1. Extract BIM material (9+ fields)",
                "2. Navigate thesaurus (semantic mapping)",
                "3. Find EPD products (50+ candidates)",
                "4. Evaluate similarity (5 dimensions)",
                "5. Rank results (exact → close → score)"
            ],
            "capabilities": [
                "Full 5-step cross-matching workflow",
                "Semantic material-to-product matching",
                "Multi-dimensional similarity evaluation",
                "Confidence-based ranking"
            ],
            "example_queries": [
                "Find EPD for Concrete_C12/15",
                "Match BIM material X to EPD products",
                "Cross-match Steel_S235"
            ]
        },
        {
            "agent_name": "CrossMatch_Anthropic",
            "display_name": "Cross-Match Workflow (Anthropic)",
            "provider": "anthropic",
            "workflow_steps": [
                "1. Extract BIM material (9+ fields)",
                "2. Navigate thesaurus (semantic mapping)",
                "3. Find EPD products (50+ candidates)",
                "4. Evaluate similarity (5 dimensions)",
                "5. Rank results (exact → close → score)"
            ],
            "capabilities": [
                "Full 5-step cross-matching workflow",
                "Semantic material-to-product matching",
                "Multi-dimensional similarity evaluation",
                "Confidence-based ranking"
            ],
            "example_queries": [
                "Find EPD for Concrete_C12/15",
                "Match BIM material X to EPD products",
                "Cross-match Steel_S235"
            ]
        }
    ]
    
    # Define ontology patterns summary
    ontology_patterns = {
        "bimtool": {
            "total_patterns": 80,
            "categories": [
                "Material search by name",
                "Category-based queries",
                "Property-based filtering",
                "Composition queries"
            ],
            "example_pattern": "SELECT ?material ?name WHERE { ?material a bimtool:Material ; bimtool:name ?name . FILTER(CONTAINS(?name, 'Concrete')) }"
        },
        "epd": {
            "total_patterns": 80,
            "categories": [
                "Product search by name",
                "Environmental data queries",
                "LCA impact queries",
                "Manufacturer queries"
            ],
            "example_pattern": "SELECT ?product ?name WHERE { ?product a epd:ProcessDataSet ; epd:hasProcessInformation/epd:hasKeyDataSetInformation/epd:Name ?name }"
        },
        "thesaurus": {
            "total_patterns": 21,
            "categories": [
                "Exact match queries",
                "Close match queries",
                "Broader/narrower relationships",
                "Related concepts"
            ],
            "example_pattern": "SELECT ?bimConcept ?epdConcept WHERE { ?bimConcept skos:exactMatch ?epdConcept }"
        }
    }
    
    return {
        "graph_rag_agents": graph_rag_agents,
        "cross_match_agents": cross_match_agents,
        "ontology_patterns": ontology_patterns,
        "total_agents": len(graph_rag_agents) + len(cross_match_agents)
    }