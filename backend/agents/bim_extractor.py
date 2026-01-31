"""
BIM Extractor Agent Module
First agent in the 5-step workflow

Extracts comprehensive building material data from BIMTool ontology:
- 9+ fields including name, categories, properties
- Material definition from rdfs:comment (critical for composition understanding)
- Primary and secondary categories (secondary is optional)
- Semantic interpretation using LLM

Input: Material name (from user)
Output: Complete BIM material data structure
"""
import logging
from typing import Dict, Any
from agents.base_agent import BaseAgent
from llm.base import BaseLLMClient
from sparql.client import SPARQLClient
from sparql.queries.bim_queries import (
    build_material_extraction_query,
    validate_material_name
)

logger = logging.getLogger(__name__)


class BIMExtractorAgent(BaseAgent):
    """
    Agent for extracting BIM material data
    
    Step 1 of 5: Extract complete material information from BIMTool knowledge graph
    """
    
    def __init__(self, llm_client: BaseLLMClient, sparql_client: SPARQLClient):
        """Initialize BIM Extractor Agent"""
        super().__init__(llm_client, sparql_client, "BIMExtractorAgent")
        
        # System prompt for LLM interpretation
        self.system_prompt = """
You are a BIM Material Analysis Expert. Your task is to interpret building material
data extracted from a knowledge graph and provide semantic understanding.

CRITICAL FIELDS TO EXTRACT:
1. Material URI and name
2. Material Asset Name (if available)
3. Description
4. Keywords
5. Comment (material definition - explains composition and properties)
6. Primary category URI and label
7. Secondary category URI and label (if available - only 6.6% have this)
8. Material class and subclass
9. Property set

The COMMENT field is particularly important as it contains detailed material
definitions explaining composition, properties, and characteristics.

Your output must be valid JSON with this structure:
```json
{
  "raw_data": {
    "uri": "...",
    "name": "...",
    "material_asset_name": "...",
    "description": "...",
    "keywords": "...",
    "comment": "...",
    "primary_category_uri": "...",
    "primary_category_label": "...",
    "secondary_category_uri": "...",
    "secondary_category_label": "...",
    "class": "...",
    "subclass": "...",
    "property_set": "..."
  },
  "semantic_interpretation": {
    "material_type": "...",
    "main_characteristics": "...",
    "typical_uses": "...",
    "key_properties": "...",
    "composition_summary": "..."
  }
}
```

Return ONLY the JSON, no additional text.
"""
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract BIM material data
        
        Args:
            input_data: Dictionary with 'material_name' key
            
        Returns:
            Dictionary with complete material data and semantic interpretation
            
        Raises:
            ValueError: If material name is invalid or not found
            Exception: If extraction fails
        """
        # Validate input
        self.validate_input(input_data, ["material_name"])
        material_name = input_data["material_name"].strip()
        
        # Validate material name
        if not validate_material_name(material_name):
            raise ValueError(
                f"Invalid material name: {material_name}. "
                "Contains dangerous characters."
            )
        
        self.logger.info(f"Extracting BIM material: {material_name}")
        
        try:
            # Step 1: Build and execute SPARQL query
            sparql_query = build_material_extraction_query(material_name)
            results = await self.query_knowledge_graph(sparql_query)
            
            # Check if material was found
            if not results:
                error_msg = f"Material not found: {material_name}"
                self.logger.warning(error_msg)
                return self.create_result(
                    success=False,
                    error=error_msg
                )
            
            # Get first result (most relevant match)
            material_data = results[0]
            self.logger.info(f"Found material: {material_data.get('name')}")
            
            # Step 2: Format data for LLM
            formatted_data = self._format_material_data(material_data)
            
            # Step 3: Use LLM to interpret and structure data
            prompt = f"""
Analyze the following BIM material data and provide structured interpretation:

{formatted_data}

Provide semantic interpretation focusing on:
1. Material type and category
2. Main characteristics and properties
3. Typical uses and applications
4. Key properties and specifications
5. Composition summary (from comment field if available)

Return valid JSON only.
"""
            
            interpretation = await self.llm_interpret(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.0,
                parse_json=True
            )
            
            # Validate interpretation structure
            if "raw_data" not in interpretation or "semantic_interpretation" not in interpretation:
                self.logger.error("LLM returned invalid structure")
                # Fallback to raw data only
                interpretation = {
                    "raw_data": self._convert_to_raw_data(material_data),
                    "semantic_interpretation": self._create_default_interpretation(material_data)
                }
            
            self.logger.info("Successfully extracted and interpreted BIM material")
            
            return self.create_result(
                success=True,
                data=interpretation
            )
            
        except Exception as e:
            self.logger.error(f"BIM extraction failed: {e}", exc_info=True)
            return self.create_result(
                success=False,
                error=str(e)
            )
    
    def _format_material_data(self, material_data: Dict[str, str]) -> str:
        """Format material data for LLM consumption"""
        formatted = []
        formatted.append("BIM MATERIAL DATA:")
        formatted.append("=" * 60)
        
        for key, value in material_data.items():
            if value:  # Only include non-empty fields
                # Format key to be more readable
                readable_key = key.replace("_", " ").title()
                formatted.append(f"{readable_key}: {value}")
        
        formatted.append("=" * 60)
        return "\n".join(formatted)
    
    def _convert_to_raw_data(self, material_data: Dict[str, str]) -> Dict[str, str]:
        """Convert SPARQL result to standardized raw_data format"""
        return {
            "uri": material_data.get("material", ""),
            "name": material_data.get("name", ""),
            "material_asset_name": material_data.get("materialAssetName"),
            "description": material_data.get("description"),
            "keywords": material_data.get("keywords"),
            "comment": material_data.get("comment"),
            "primary_category_uri": material_data.get("primaryCategoryUri", ""),
            "primary_category_label": material_data.get("primaryCategoryLabel", ""),
            "secondary_category_uri": material_data.get("secondaryCategoryUri"),
            "secondary_category_label": material_data.get("secondaryCategoryLabel"),
            "class": material_data.get("class"),
            "subclass": material_data.get("subclass"),
            "property_set": material_data.get("propertySet")
        }
    
    def _create_default_interpretation(self, material_data: Dict[str, str]) -> Dict[str, str]:
        """Create default semantic interpretation if LLM fails"""
        name = material_data.get("name", "")
        category = material_data.get("primaryCategoryLabel", "")
        description = material_data.get("description", "")
        comment = material_data.get("comment", "")
        
        return {
            "material_type": category,
            "main_characteristics": description or f"{category} material",
            "typical_uses": f"Typical {category.lower()} applications",
            "key_properties": "See property set for details",
            "composition_summary": comment or f"{name} - {category}"
        }