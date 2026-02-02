"""
BIM Extractor Agent Module - CORRECTED FIX
First agent in the 5-step workflow

CRITICAL FIX: Accepts thesaurus_client parameter and uses it properly
WITHOUT changing any function names or imports
"""
import logging
from typing import Optional
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
    
    ✅ CRITICAL FIX: Now accepts thesaurus_client parameter
    """
    
    def __init__(
        self, 
        llm_client: BaseLLMClient, 
        sparql_client: SPARQLClient,
        thesaurus_client: SPARQLClient  # ✅ ADD THIS PARAMETER
    ):
        """
        Initialize BIM Extractor Agent
        
        Args:
            llm_client: Language model client
            sparql_client: SPARQL client for BIM ontology
            thesaurus_client: SPARQL client for thesaurus (for URI transformation)
        """
        super().__init__(llm_client, sparql_client, "BIMExtractorAgent")
        self.thesaurus_client = thesaurus_client  # ✅ STORE THESAURUS CLIENT
        
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
            
            # Get LLM interpretation
            interpretation = await self.llm_interpret(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.0,
                parse_json=True
            )
            
            # Validate structure
            if "raw_data" not in interpretation:
                interpretation["raw_data"] = self._convert_to_raw_data(material_data)
            if "semantic_interpretation" not in interpretation:
                interpretation["semantic_interpretation"] = self._create_default_interpretation(
                    interpretation["raw_data"]
                )
            
            # Step 4: Transform BIM ontology URIs to thesaurus taxonomy URIs
            # ✅ THIS IS THE CRITICAL TRANSFORMATION STEP
            interpretation = await self._transform_to_thesaurus_uris(interpretation)
            
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
    
    async def _transform_to_thesaurus_uris(
        self, 
        interpretation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform BIM ontology URIs to thesaurus taxonomy URIs using owl:equivalentClass
        
        Uses SPARQL to query the thesaurus graph for owl:equivalentClass relationships.
        
        Args:
            interpretation: BIM material data with ontology URIs
            
        Returns:
            Same data with additional thesaurus taxonomy URIs added
        """
        raw_data = interpretation.get("raw_data", {})
        
        # Transform primary category URI
        primary_uri = raw_data.get("primary_category_uri")
        if primary_uri:
            thesaurus_uri = await self._query_thesaurus_mapping(primary_uri)
            raw_data["primary_category_thesaurus_uri"] = thesaurus_uri
            if thesaurus_uri:
                self.logger.info(f"✓ Mapped primary: {primary_uri.split('#')[-1]} → {thesaurus_uri.split('#')[-1]}")
            else:
                self.logger.warning(f"⚠ No thesaurus mapping found for: {primary_uri}")
        
        # Transform secondary category URI
        secondary_uri = raw_data.get("secondary_category_uri")
        if secondary_uri:
            thesaurus_uri = await self._query_thesaurus_mapping(secondary_uri)
            raw_data["secondary_category_thesaurus_uri"] = thesaurus_uri
            if thesaurus_uri:
                self.logger.info(f"✓ Mapped secondary: {secondary_uri.split('#')[-1]} → {thesaurus_uri.split('#')[-1]}")
        else:
            raw_data["secondary_category_thesaurus_uri"] = None
        
        return interpretation


    async def _query_thesaurus_mapping(self, bim_ontology_uri: str) -> Optional[str]:
        """
        Query thesaurus for equivalent taxonomy URI using owl:equivalentClass
        
        ✅ CRITICAL FIX: Now uses self.thesaurus_client instead of creating new client
        
        Args:
            bim_ontology_uri: BIM ontology URI
                Example: "http://www.BimToolsMaterialLibrary.com/BimBuildingMaterialsOntology#Concrete"
            
        Returns:
            Thesaurus taxonomy URI or None
                Example: "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#Concrete"
        """
        # Build SPARQL query to find owl:equivalentClass relationship
        query = f"""
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?thesaurus_uri ?label
    WHERE {{
        # Find thesaurus concept equivalent to BIM ontology concept
        ?thesaurus_uri owl:equivalentClass <{bim_ontology_uri}> .
        
        # Ensure it's from bimtooltax namespace
        FILTER(STRSTARTS(STR(?thesaurus_uri), "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#"))
        
        # Get label (English only)
        OPTIONAL {{
            ?thesaurus_uri skos:prefLabel ?label .
            FILTER(LANG(?label) = "en")
        }}
    }}
    LIMIT 1
    """
        
        try:
            # ✅ USE self.thesaurus_client (not creating new client)
            results = await self.thesaurus_client.query(query)
            
            if results and len(results) > 0:
                return results[0].get("thesaurus_uri")
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Thesaurus mapping query failed: {e}")
            return None


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
            "class": material_data.get("primaryCategoryLabel", ""),
            "subclass": material_data.get("secondaryCategoryLabel"),
            "property_set": material_data.get("propertySetName")
        }
    
    def _create_default_interpretation(self, raw_data: Dict[str, str]) -> Dict[str, str]:
        """Create default semantic interpretation if LLM fails"""
        return {
            "material_type": raw_data.get("class", "Unknown"),
            "main_characteristics": raw_data.get("description", "No description available"),
            "typical_uses": "General construction applications",
            "key_properties": raw_data.get("keywords", "No keywords available"),
            "composition_summary": raw_data.get("comment", "No composition data available")
        }