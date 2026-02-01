from fastapi import APIRouter, HTTPException
from config import (
    get_ontology_config,
    list_available_ontologies,
    list_available_llm_providers
)
from bim_query_patterns import get_all_bim_patterns
from epd_query_patterns import get_all_epd_patterns
from thesaurus_query_patterns import get_all_thesaurus_patterns

router = APIRouter()

@router.get("/config/agents")
async def get_agent_configurations():
    """
    Get all available agents with their configurations and query patterns
    
    Returns detailed configuration for each agent including:
    - System prompts
    - Query pattern examples  
    - SPARQL templates
    - Ontology structure
    """
    ontologies = list_available_ontologies()
    providers = list_available_llm_providers()
    
    agents_config = {
        "graph_rag_agents": [],
        "cross_match_agents": [],
        "ontology_patterns": {}
    }
    
    # Load query patterns for each ontology
    pattern_loaders = {
        'bimtool': get_all_bim_patterns,
        'epd': get_all_epd_patterns,
        'thesaurus': get_all_thesaurus_patterns
    }
    
    for ontology_name in ontologies:
        ontology_config = get_ontology_config(ontology_name)
        
        # Load query patterns
        if ontology_name in pattern_loaders:
            patterns = pattern_loaders[ontology_name]()
            agents_config["ontology_patterns"][ontology_name] = {
                "total_patterns": sum(len(category_patterns) for category_patterns in patterns.values()),
                "categories": list(patterns.keys()),
                "example_queries": ontology_config.example_queries,
                "patterns_summary": _summarize_patterns(patterns)
            }
        
        # Create agent configs for each provider
        for provider in providers:
            agent_name = f"{ontology_config.name.title()}_{provider.title()}"
            agents_config["graph_rag_agents"].append({
                "agent_name": agent_name,
                "ontology": ontology_config.name,
                "display_name": ontology_config.display_name,
                "provider": provider,
                "capabilities": [
                    "Direct SPARQL queries",
                    "Property-based search",
                    "Relationship traversal"
                ],
                "example_queries": ontology_config.example_queries[:3]
            })
    
    # Add cross-match agents
    for provider in providers:
        agent_name = f"CrossMatch_{provider.title()}"
        agents_config["cross_match_agents"].append({
            "agent_name": agent_name,
            "provider": provider,
            "capabilities": [
                "5-step BIM-EPD matching workflow",
                "Multi-dimensional similarity evaluation",
                "Ranked results with confidence scores"
            ],
            "workflow_steps": [
                "1. Extract BIM material (9+ fields)",
                "2. Navigate thesaurus (semantic mapping)",
                "3. Find EPD products (50+ candidates)",
                "4. Evaluate similarity (5 dimensions)",
                "5. Rank results (exact > close > score)"
            ]
        })
    
    return agents_config


def _summarize_patterns(patterns: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Summarize query patterns for frontend display"""
    summary = {}
    for category, category_patterns in patterns.items():
        summary[category] = [
            pattern_info.get("description", "")
            for pattern_info in list(category_patterns.values())[:3]  # First 3 examples
        ]
    return summary