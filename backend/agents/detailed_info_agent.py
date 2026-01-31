"""
Detailed Information Agent Module
Post-ranking optional agent for fetching comprehensive details

Fetches complete information for top-ranked EPD products:
- Web links (Uri property from KeyDataSetInformation)
- ProcessDataSet URIs (graph identifiers)
- Total GWP values
- All product details

This agent runs AFTER ranking to avoid slowing down the main workflow.
Only fetches details for top-N products.

Input: Ranked matches (top 5-10)
Output: Enhanced match results with comprehensive details
"""
import logging
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from llm.base import BaseLLMClient
from sparql.client import SPARQLClient
from sparql.queries.epd_queries import build_epd_product_details_query

logger = logging.getLogger(__name__)


class DetailedInformationAgent(BaseAgent):
    """
    Agent for fetching detailed EPD product information
    
    Optional Step 6: Enhance top matches with comprehensive details
    """
    
    def __init__(self, llm_client: BaseLLMClient, sparql_client: SPARQLClient):
        """Initialize Detailed Information Agent"""
        super().__init__(llm_client, sparql_client, "DetailedInformationAgent")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch detailed information for ranked matches
        
        Args:
            input_data: {
                "ranked_matches": List of top matches,
                "max_details": Max number to fetch details for (default 5)
            }
            
        Returns:
            Enhanced matches with detailed information
        """
        # Validate input
        self.validate_input(input_data, ["ranked_matches"])
        
        ranked_matches = input_data["ranked_matches"]
        max_details = input_data.get("max_details", 5)
        
        if not ranked_matches:
            self.logger.warning("No matches to fetch details for")
            return self.create_result(
                success=True,
                data={"enhanced_matches": []}
            )
        
        # Limit to top N
        top_matches = ranked_matches[:max_details]
        
        self.logger.info(f"Fetching detailed info for top {len(top_matches)} matches")
        
        try:
            # Extract EPD product URIs
            product_uris = [
                match.get("epd_uri")
                for match in top_matches
                if match.get("epd_uri")
            ]
            
            if not product_uris:
                self.logger.warning("No valid product URIs found")
                return self.create_result(
                    success=True,
                    data={"enhanced_matches": ranked_matches}
                )
            
            # Query for detailed information
            sparql_query = build_epd_product_details_query(product_uris)
            results = await self.query_knowledge_graph(sparql_query)
            
            # Create lookup dictionary
            details_lookup = {}
            for result in results:
                uri = result.get("product")
                details_lookup[uri] = {
                    "web_link": result.get("webLink"),
                    "total_gwp": result.get("totalGWP"),
                    "name_detail": result.get("nameDetail"),
                    "product_type_category": result.get("productTypeCategory"),
                    "technical_purpose": result.get("technicalPurpose"),
                    "technology_description": result.get("technologyDescription"),
                    "location": result.get("location")
                }
            
            # Enhance matches with detailed information
            enhanced_matches = []
            for match in top_matches:
                epd_uri = match.get("epd_uri")
                details = details_lookup.get(epd_uri, {})
                
                enhanced_match = {
                    **match,
                    "detailed_info": details
                }
                
                enhanced_matches.append(enhanced_match)
            
            # Keep remaining matches without details
            if len(ranked_matches) > max_details:
                enhanced_matches.extend(ranked_matches[max_details:])
            
            self.logger.info(f"Enhanced {len(details_lookup)} matches with details")
            
            return self.create_result(
                success=True,
                data={"enhanced_matches": enhanced_matches}
            )
            
        except Exception as e:
            self.logger.error(f"Detail fetching failed: {e}", exc_info=True)
            # Return original matches if detail fetching fails
            return self.create_result(
                success=True,
                data={"enhanced_matches": ranked_matches}
            )
