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
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from llm.base import BaseLLMClient
from sparql.client import SPARQLClient

logger = logging.getLogger(__name__)


class DetailedInformationAgent(BaseAgent):
    """
    Agent for fetching detailed EPD product information
    
    Optional Step 6: Enhance top matches with comprehensive details
    
    This agent fetches TWO critical URIs:
    1. ProcessDataSet URI - The graph identifier (e.g., epd:ConcretePavingBraemar...)
    2. Uri property - The EPD online web link from KeyDataSetInformation
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
            product_uris = []
            for match in top_matches:
                # Try different possible URI locations based on data structure
                uri = (match.get("epd_uri") or 
                       match.get("epd_product", {}).get("uri") or
                       match.get("epd_product", {}).get("raw_data", {}).get("uri"))
                if uri:
                    product_uris.append(uri)
            
            if not product_uris:
                self.logger.warning("No valid product URIs found")
                return self.create_result(
                    success=True,
                    data={"enhanced_matches": ranked_matches}
                )
            
            # Build SPARQL query for detailed information
            sparql_query = self._build_epd_details_query(product_uris)
            
            # Query for detailed information
            results = await self.query_knowledge_graph(sparql_query)
            
            # Create lookup dictionary
            details_lookup = {}
            for result in results:
                uri = result.get("product")
                details_lookup[uri] = {
                    "web_link": result.get("webLink"),
                    "total_gwp": result.get("totalGWP"),
                    "name": result.get("name"),
                    "name_detail": result.get("nameDetail"),
                    "product_type_category": result.get("productTypeCategory"),
                    "technical_purpose": result.get("technicalPurpose"),
                    "technology_description": result.get("technologyDescription"),
                    "location": result.get("location")
                }
            
            # Enhance matches with detailed information
            enhanced_matches = []
            for match in top_matches:
                # Get the EPD URI from match
                epd_uri = (match.get("epd_uri") or 
                          match.get("epd_product", {}).get("uri") or
                          match.get("epd_product", {}).get("raw_data", {}).get("uri"))
                
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
    
    def _build_epd_details_query(self, product_uris: List[str]) -> str:
        """
        Build SPARQL query for fetching comprehensive EPD product details
        
        CRITICAL: Fetches TWO URIs:
        1. ProcessDataSet URI (?product) - The graph identifier
        2. Uri property (?webLink) - The EPD online web link from KeyDataSetInformation
        
        Also fetches:
        - Total GWP across all life cycle phases
        - Product names and classifications
        - Technical details
        - Location information
        
        Args:
            product_uris: List of EPD ProcessDataSet URIs
            
        Returns:
            SPARQL query string
        """
        # Format URIs for VALUES clause - MUST use full URIs with angle brackets
        values_clause = " ".join(f"<{uri}>" for uri in product_uris)
        
        # CRITICAL: This query pattern matches the Python app EXACTLY
        query = f"""
PREFIX epd: <http://www.EpdLcaOntology.com/EpdLcaDataSetOntology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?product ?name ?nameDetail ?productTypeCategory 
       ?webLink ?technicalPurpose ?technologyDescription ?location
       (SUM(?gwpValue) AS ?totalGWP)
WHERE {{
  # Bind specific products
  VALUES ?product {{ {values_clause} }}
  
  ?product epd:hasProcessInformation ?procInfo .
  ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
  
  # Required fields
  ?keyInfo epd:Name ?name .
  
  # CRITICAL: Web link from KeyDataSetInformation (Uri property)
  OPTIONAL {{ ?keyInfo epd:Uri ?webLink }}
  
  # Classification
  OPTIONAL {{
    ?keyInfo epd:NameDetail ?nameDetail ;
             epd:hasClassificationOrCategory ?classif .
    ?classif epd:ProductTypeCategory ?productTypeCategory .
  }}
  
  # Technical information
  OPTIONAL {{ ?keyInfo epd:TechnicalPurpose ?technicalPurpose }}
  OPTIONAL {{ ?procInfo epd:hasTechnology ?tech .
              ?tech epd:TechnologyDescription ?technologyDescription }}
  
  # Location
  OPTIONAL {{ ?procInfo epd:hasGeography ?geo .
              ?geo epd:Location ?location }}
  
  # Total GWP calculation (sum across all life cycle phases)
  OPTIONAL {{
    ?product epd:hasLCIAResult ?lciaResult .
    ?lciaResult epd:hasLCIAResultIndicator ?indicator .
    ?indicator rdfs:label ?indicatorLabel ;
               epd:hasImpactCategoryIndicatorValue ?impactValue .
    ?impactValue epd:MeanValue ?gwpValue .
    
    # Filter for GWP indicator only
    FILTER(CONTAINS(LCASE(?indicatorLabel), "gwp") || 
           CONTAINS(LCASE(?indicatorLabel), "global warming"))
  }}
}}
GROUP BY ?product ?name ?nameDetail ?productTypeCategory 
         ?webLink ?technicalPurpose ?technologyDescription ?location
ORDER BY ?name
"""
        return query