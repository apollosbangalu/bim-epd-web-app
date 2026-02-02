"""
Thesaurus Navigator Agent Module - ENHANCED WITH STRICT VALIDATION
Second agent in the 5-step workflow

Navigates SKOS thesaurus to find semantic concept mappings between
BIM categories and EPD concepts.

Input: BIM material data with thesaurus taxonomy URIs
Output: List of concept mappings with confidence scores

CRITICAL ENHANCEMENT: Now validates that URIs are thesaurus taxonomy URIs
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
    
    ENHANCED: Now strictly validates thesaurus taxonomy URIs
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
            input_data: BIM material data with thesaurus taxonomy URIs
            
        Returns:
            Concept mappings with confidence scores
        """
        # Validate input
        required_fields = ["raw_data"]
        self.validate_input(input_data, required_fields)
        
        raw_data = input_data["raw_data"]
        
        # ✅ STRICT: Only use thesaurus taxonomy URIs (NOT ontology URIs)
        primary_cat = raw_data.get("primary_category_thesaurus_uri")
        secondary_cat = raw_data.get("secondary_category_thesaurus_uri")
        
        # ✅ LOG FOR DEBUGGING
        self.logger.info(f"Thesaurus Navigator received:")
        self.logger.info(f"  - Primary thesaurus URI: {primary_cat}")
        self.logger.info(f"  - Secondary thesaurus URI: {secondary_cat}")
        
        # ✅ VALIDATE: Primary URI must exist
        if not primary_cat:
            # Check if we have ontology URI (indicates Step 1 transformation failed)
            primary_ontology = raw_data.get("primary_category_uri")
            
            if primary_ontology:
                error_msg = (
                    f"No primary thesaurus URI found. "
                    f"BIM extraction failed to transform ontology URI to thesaurus URI. "
                    f"Ontology URI present: {primary_ontology} "
                    f"This indicates the owl:equivalentClass mapping is missing or "
                    f"the thesaurus client was not properly initialized in Step 1."
                )
            else:
                error_msg = "No primary category URI found (neither thesaurus nor ontology)"
            
            self.logger.error(error_msg)
            return self.create_result(
                success=False,
                error=error_msg
            )
        
        # ✅ VALIDATE: URI must be from thesaurus taxonomy namespace
        if not self._is_thesaurus_taxonomy_uri(primary_cat):
            error_msg = (
                f"Invalid primary URI: Expected thesaurus taxonomy URI "
                f"(http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#...), "
                f"but got: {primary_cat}. "
                f"This indicates Step 1 failed to transform BIM ontology URI to thesaurus URI."
            )
            self.logger.error(error_msg)
            return self.create_result(
                success=False,
                error=error_msg
            )
        
        # ✅ VALIDATE: Secondary URI (if present) must also be thesaurus taxonomy URI
        if secondary_cat and not self._is_thesaurus_taxonomy_uri(secondary_cat):
            self.logger.warning(
                f"Invalid secondary URI (ignoring): {secondary_cat}. "
                f"Expected thesaurus taxonomy URI."
            )
            secondary_cat = None  # Ignore invalid secondary URI
        
        self.logger.info(f"✓ URI validation passed - proceeding with thesaurus navigation")
        
        try:
            # Step 1: Query thesaurus for mappings
            sparql_query = build_bim_to_epd_mapping_query(
                primary_category_uri=primary_cat,
                secondary_category_uri=secondary_cat
            )
            
            self.logger.debug(f"Executing thesaurus query:\n{sparql_query}")
            
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
                            "close_matches": 0,
                            "primary_used": True,
                            "secondary_used": bool(secondary_cat)
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
                confidence = calculate_mapping_confidence(match_type, category_type)
                
                mapping = {
                    "bim_concept": result.get("bim_concept"),
                    "bim_label": result.get("bim_label", ""),
                    "epd_concept": result.get("epd_concept"),
                    "epd_label": result.get("epd_label", ""),
                    "match_type": match_type,
                    "category_type": category_type,
                    "confidence": confidence
                }
                
                mappings.append(mapping)
                
                if match_type == "exactMatch":
                    exact_count += 1
                elif match_type == "closeMatch":
                    close_count += 1
            
            # Sort by confidence (exact > close, primary > secondary)
            mappings.sort(key=lambda x: (-x["confidence"], x["category_type"]))
            
            summary = {
                "total_mappings": len(mappings),
                "exact_matches": exact_count,
                "close_matches": close_count,
                "primary_used": True,
                "secondary_used": bool(secondary_cat)
            }
            
            self.logger.info(
                f"✓ Found {len(mappings)} mappings: "
                f"{exact_count} exact, {close_count} close"
            )
            
            # Step 3: LLM interpretation (optional - for quality assessment)
            # This can help prioritize mappings if needed
            
            return self.create_result(
                success=True,
                data={
                    "mappings": mappings,
                    "summary": summary
                }
            )
            
        except Exception as e:
            self.logger.error(f"Thesaurus navigation failed: {e}", exc_info=True)
            return self.create_result(
                success=False,
                error=f"Thesaurus navigation error: {str(e)}"
            )
    
    def _is_thesaurus_taxonomy_uri(self, uri: str) -> bool:
        """
        Validate that URI is a thesaurus taxonomy URI
        
        Valid thesaurus taxonomy URIs start with:
        - http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#
        - http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#
        
        Invalid (BIM ontology URIs) start with:
        - http://www.BimToolsMaterialLibrary.com/BimBuildingMaterialsOntology#
        
        Args:
            uri: URI to validate
            
        Returns:
            True if valid thesaurus taxonomy URI, False otherwise
        """
        if not uri:
            return False
        
        valid_prefixes = [
            "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#",
            "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#",
            "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/berr#",
            "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/dcm#"
        ]
        
        return any(uri.startswith(prefix) for prefix in valid_prefixes)