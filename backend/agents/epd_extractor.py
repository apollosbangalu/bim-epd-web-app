"""
EPD Extractor Agent Module
Third agent in the 5-step workflow

Extracts Environmental Product Declaration (EPD) products based on
concept mappings from thesaurus.

CRITICAL FEATURES:
- Memory-safe queries (LIMIT on products)
- Correct property paths
- ProductTypeCategory filtering

Input: Thesaurus mappings with EPD concept labels
Output: List of EPD products with basic information
"""
import logging
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from llm.base import BaseLLMClient
from sparql.client import SPARQLClient
from sparql.queries.epd_queries import (
    build_epd_products_by_category_query,
    validate_category_keywords
)

logger = logging.getLogger(__name__)


class EPDExtractorAgent(BaseAgent):
    """
    Agent for extracting EPD product data
    
    Step 3 of 5: Find EPD products matching mapped categories
    """
    
    def __init__(self, llm_client: BaseLLMClient, sparql_client: SPARQLClient):
        """Initialize EPD Extractor Agent"""
        super().__init__(llm_client, sparql_client, "EPDExtractorAgent")
        
        self.system_prompt = """
You are an EPD Product Analysis Expert. Analyze environmental product
declarations and extract relevant information.

Focus on:
1. Product name and categorization
2. Technical purpose and description
3. Location and manufacturing details
4. Environmental performance indicators

Return valid JSON:
```json
{
  "products": [
    {
      "uri": "...",
      "name": "...",
      "name_detail": "...",
      "product_type_category": "...",
      "technical_purpose": "...",
      "technology_description": "...",
      "location": "..."
    }
  ],
  "summary": {
    "total_products": 0,
    "categories": []
  }
}
```
"""
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract EPD products
        
        Args:
            input_data: Thesaurus mappings with EPD concept labels
            
        Returns:
            List of EPD products
        """
        # Validate input
        self.validate_input(input_data, ["mappings"])
        
        mappings = input_data["mappings"]
        
        if not mappings:
            self.logger.warning("No mappings provided, returning empty results")
            return self.create_result(
                success=True,
                data={
                    "products": [],
                    "summary": {"total_products": 0, "categories": []}
                }
            )
        
        try:
            # Extract EPD concept labels for category search
            category_keywords = list(set([
                m["epd_label"] 
                for m in mappings 
                if m.get("epd_label")
            ]))
            
            self.logger.info(f"Searching EPD products for keywords: {category_keywords}")
            
            # Validate keywords
            if not validate_category_keywords(category_keywords):
                raise ValueError("Invalid category keywords")
            
            # Query EPD products
            sparql_query = build_epd_products_by_category_query(
                category_keywords=category_keywords,
                max_products=50
            )
            
            results = await self.query_knowledge_graph(sparql_query)
            
            if not results:
                self.logger.warning("No EPD products found")
                return self.create_result(
                    success=True,
                    data={
                        "products": [],
                        "summary": {"total_products": 0, "categories": category_keywords}
                    }
                )
            
            # Format products
            products = []
            for result in results:
                product = {
                    "uri": result.get("product"),
                    "name": result.get("name"),
                    "name_detail": result.get("nameDetail"),
                    "product_type_category": result.get("productTypeCategory"),
                    "technical_purpose": result.get("technicalPurpose"),
                    "technology_description": result.get("technologyDescription"),
                    "location": result.get("location")
                }
                products.append(product)
            
            self.logger.info(f"Found {len(products)} EPD products")
            
            return self.create_result(
                success=True,
                data={
                    "products": products,
                    "summary": {
                        "total_products": len(products),
                        "categories": category_keywords
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"EPD extraction failed: {e}", exc_info=True)
            return self.create_result(
                success=False,
                error=str(e)
            )