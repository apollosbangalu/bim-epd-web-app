"""
Thesaurus Navigator Agent Module
Second agent in the 5-step workflow

Navigates SKOS thesaurus to find semantic concept mappings between
BIM categories and EPD concepts.

Input: BIM material data with categories
Output: List of concept mappings with confidence scores
"""
import logging
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from llm.base import BaseLLMClient
from sparql.client import SPARQLClient
from sparql.queries.thesaurus_queries import (
    build_bim_to_epd_mapping_query,
    validate_concept_uri,
    calculate_mapping_confidence
)

logger = logging.getLogger(__name__)


class ThesaurusNavigatorAgent(BaseAgent):
    """
    Agent for navigating thesaurus concept mappings
    
    Step 2 of 5: Find semantic mappings from BIM categories to EPD concepts
    """
    
    def __init__(self, llm_client: BaseLLMClient, sparql_client: SPARQLClient):
        """Initialize Thesaurus Navigator Agent"""
        super().__init__(llm_client, sparql_client, "ThesaurusNavigatorAgent")
        
        self.system_prompt = """
You are a Semantic Thesaurus Expert. Analyze concept mappings between
BIM building materials and EPD environmental products.

Evaluate mappings based on:
1. Match type (exactMatch > closeMatch)
2. Category type (primary > secondary)
3. Label similarity and semantic relevance

Return valid JSON with this structure:
```json
{
  "mappings": [
    {
      "bim_concept": "URI",
      "bim_label": "label",
      "epd_concept": "URI",
      "epd_label": "label",
      "match_type": "exactMatch|closeMatch",
      "category_type": "primary|secondary",
      "confidence": 0.0-1.0
    }
  ],
  "summary": {
    "total_mappings": 0,
    "exact_matches": 0,
    "close_matches": 0,
    "primary_used": true,
    "secondary_used": false
  }
}
```

Return ONLY JSON, no additional text.
"""
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Navigate thesaurus mappings
        
        Args:
            input_data: BIM material data with category URIs
            
        Returns:
            Concept mappings with confidence scores
        """
        # Validate input
        required_fields = ["raw_data"]
        self.validate_input(input_data, required_fields)
        
        raw_data = input_data["raw_data"]
        
        # Extract category URIs
        primary_cat = raw_data.get("primary_category_uri")
        secondary_cat = raw_data.get("secondary_category_uri")
        
        if not primary_cat:
            return self.create_result(
                success=False,
                error="No primary category URI found"
            )
        
        self.logger.info(f"Navigating thesaurus for categories: {primary_cat}")
        
        try:
            # Step 1: Query thesaurus for mappings
            sparql_query = build_bim_to_epd_mapping_query(
                primary_category_uri=primary_cat,
                secondary_category_uri=secondary_cat
            )
            
            results = await self.query_knowledge_graph(sparql_query)
            
            if not results:
                self.logger.warning("No thesaurus mappings found")
                return self.create_result(
                    success=True,
                    data={
                        "mappings": [],
                        "summary": {
                            "total_mappings": 0,
                            "exact_matches": 0,
                            "close_matches": 0
                        }
                    }
                )
            
            # Step 2: Process mappings and calculate confidence
            mappings = []
            exact_count = 0
            close_count = 0
            
            for result in results:
                match_type = result.get("match_type")
                category_type = result.get("category_type")
                
                # Calculate confidence score
                confidence = calculate_mapping_confidence(
                    match_type,
                    category_type
                )
                
                mapping = {
                    "bim_concept": result.get("bim_concept"),
                    "bim_label": result.get("bim_label"),
                    "epd_concept": result.get("epd_concept"),
                    "epd_label": result.get("epd_label"),
                    "match_type": match_type,
                    "category_type": category_type,
                    "confidence": confidence
                }
                
                mappings.append(mapping)
                
                if match_type == "exactMatch":
                    exact_count += 1
                elif match_type == "closeMatch":
                    close_count += 1
            
            # Step 3: Use LLM to validate and enrich mappings
            formatted_mappings = self._format_mappings(mappings)
            
            prompt = f"""
Analyze these thesaurus concept mappings:

{formatted_mappings}

Validate the mappings and return them in the specified JSON format.
Include a summary with counts.
"""
            
            interpretation = await self.llm_interpret(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.0,
                parse_json=True
            )
            
            # Validate structure
            if "mappings" not in interpretation:
                interpretation = {
                    "mappings": mappings,
                    "summary": {
                        "total_mappings": len(mappings),
                        "exact_matches": exact_count,
                        "close_matches": close_count,
                        "primary_used": True,
                        "secondary_used": bool(secondary_cat)
                    }
                }
            
            self.logger.info(f"Found {len(mappings)} concept mappings")
            
            return self.create_result(
                success=True,
                data=interpretation
            )
            
        except Exception as e:
            self.logger.error(f"Thesaurus navigation failed: {e}", exc_info=True)
            return self.create_result(
                success=False,
                error=str(e)
            )
    
    def _format_mappings(self, mappings: List[Dict]) -> str:
        """Format mappings for LLM"""
        formatted = []
        formatted.append("THESAURUS CONCEPT MAPPINGS:")
        formatted.append("=" * 60)
        
        for i, mapping in enumerate(mappings, 1):
            formatted.append(f"\nMapping {i}:")
            formatted.append(f"  BIM: {mapping['bim_label']} ({mapping['bim_concept']})")
            formatted.append(f"  EPD: {mapping['epd_label']} ({mapping['epd_concept']})")
            formatted.append(f"  Match Type: {mapping['match_type']}")
            formatted.append(f"  Category: {mapping['category_type']}")
            formatted.append(f"  Confidence: {mapping['confidence']:.2f}")
        
        formatted.append("=" * 60)
        return "\n".join(formatted)