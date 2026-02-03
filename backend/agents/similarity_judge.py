"""
Similarity Judge Agent Module
Fourth agent in the 5-step workflow

Evaluates multi-dimensional similarity between BIM materials and EPD products.

EVALUATION DIMENSIONS:
1. Name Similarity (0-1)
2. Category Alignment (0-1)
3. Functional Match (0-1)  
4. Technical Compatibility (0-1)
5. Specificity Match (0-1)

Uses holistic contextual evaluation considering ALL available context
from both BIM (10+ fields) and EPD (5 fields).

Input: BIM material data + EPD product list
Output: Evaluated products with similarity scores
"""
import logging
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from llm.base import BaseLLMClient
from sparql.client import SPARQLClient

logger = logging.getLogger(__name__)


class SimilarityJudgeAgent(BaseAgent):
    """
    Agent for evaluating similarity between BIM and EPD
    
    Step 4 of 5: Multi-dimensional contextual similarity evaluation
    """
    
    def __init__(self, llm_client: BaseLLMClient, sparql_client: SPARQLClient):
        """Initialize Similarity Judge Agent"""
        super().__init__(llm_client, sparql_client, "SimilarityJudgeAgent")
        
        # ✅ NEW: Single-product system prompt (used for one-at-a-time evaluation)
        self.system_prompt_single = """
    You are a Similarity Evaluation Expert for building materials and environmental products.

    Evaluate the similarity between ONE BIM material and ONE EPD product across 5 dimensions.

    EVALUATION DIMENSIONS (each scored 0.0-1.0):

    1. NAME SIMILARITY (20% weight):
    - Compare BIM name/asset name with EPD name/nameDetail
    - Consider abbreviations, standards, grades (e.g., C12/15, S275)
    - Look for keyword overlap and semantic equivalence
    - Example: "Concrete C12/15" vs "Ready-mix Concrete Grade C12" → HIGH

    2. CATEGORY ALIGNMENT (25% weight):
    - Compare BIM class/subclass/categories with EPD productTypeCategory
    - Consider hierarchical relationships (parent/child categories)
    - Check for semantic equivalence across ontologies
    - Example: BIM "Concrete/Structural" vs EPD "Concrete Products" → HIGH

    3. FUNCTIONAL MATCH (25% weight):
    - Compare BIM description/keywords AND comment (material definition) with EPD technicalPurpose
    - The COMMENT field is CRITICAL - contains detailed material composition
    - Does EPD serve same structural/functional purpose as BIM material?
    - Example: BIM comment "load-bearing structural concrete" vs EPD "structural applications" → HIGH

    4. TECHNICAL COMPATIBILITY (20% weight):
    - Compare BIM properties AND comment with EPD technologyDescription
    - Are manufacturing processes compatible?
    - Do specifications align (grades, standards, composition)?
    - Use COMMENT field to understand material composition
    - Example: BIM comment "composite with cement binder" vs EPD "Portland cement based" → HIGH

    5. SPECIFICITY MATCH (10% weight):
    - Does EPD specificity level match BIM material detail level?
    - Is EPD too generic (low detail) or too specific (overly detailed)?
    - Appropriate level of granularity?
    - Example: BIM "C12/15 Grade" needs HIGH specificity EPD → GOOD

    SCORING CALCULATION:
    Total Score = (name × 0.20) + (category × 0.25) + (functional × 0.25) 
                + (technical × 0.20) + (specificity × 0.10)

    CRITICAL GUIDELINES:
    ✓ Use ALL available fields in evaluation
    ✓ ALWAYS reference BIM comment field for Dimensions 3 & 4
    ✓ Weight exact name/terminology matches higher
    ✓ Consider domain knowledge (construction, manufacturing)
    ✓ Be objective and evidence-based
    ✓ Account for missing fields gracefully (don't penalize)

    RETURN FORMAT (STRICT JSON - NO MARKDOWN):
    {
    "scores": {
        "name_similarity": 0.0-1.0,
        "category_alignment": 0.0-1.0,
        "functional_match": 0.0-1.0,
        "technical_compatibility": 0.0-1.0,
        "specificity_match": 0.0-1.0,
        "total_score": 0.0-1.0
    },
    "explanation": "Brief 2-3 sentence explanation of the evaluation",
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"]
    }

    IMPORTANT: Return ONLY the JSON object above. No explanatory text before or after.
    """
        
        # Keep existing batch system prompt (for potential future batch processing)
        self.system_prompt = """
    You are a Similarity Evaluation Expert for building materials and environmental products.

    Evaluate similarity across 5 dimensions (each 0.0-1.0):

    1. NAME SIMILARITY:
    - Compare BIM name/asset name with EPD name/nameDetail
    - Consider abbreviations, standards, grades
    - Look for keyword overlap

    2. CATEGORY ALIGNMENT:
    - Compare BIM class/subclass/categories with EPD productTypeCategory
    - Consider hierarchical relationships
    - Check semantic equivalence

    3. FUNCTIONAL MATCH:
    - Compare BIM description/keywords AND comment (material definition) with EPD technicalPurpose
    - The COMMENT field is critical - it contains detailed material composition info
    - Does EPD serve same purpose as BIM material?

    4. TECHNICAL COMPATIBILITY:
    - Compare BIM properties AND comment with EPD technologyDescription
    - Manufacturing processes compatible?
    - Specifications align (grades, standards)?
    - COMMENT provides composition understanding

    5. SPECIFICITY MATCH:
    - Does EPD specificity level match BIM detail?
    - Too generic or too specific?
    - Appropriate level of detail?

    Calculate weighted total score:
    - Name: 20%
    - Category: 25%
    - Functional: 25%
    - Technical: 20%
    - Specificity: 10%

    Return JSON:
    ```json
    {
    "evaluations": [
        {
        "epd_uri": "...",
        "scores": {
            "name_similarity": 0.0-1.0,
            "category_alignment": 0.0-1.0,
            "functional_match": 0.0-1.0,
            "technical_compatibility": 0.0-1.0,
            "specificity_match": 0.0-1.0,
            "total_score": 0.0-1.0
        },
        "explanation": "Brief explanation of evaluation",
        "strengths": ["point 1", "point 2"],
        "weaknesses": ["point 1", "point 2"]
        }
    ]
    }
    ```

    Evaluate ALL products. Be precise and objective. Use COMMENT field for deeper understanding.
    """
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate similarity for all EPD products (ONE AT A TIME)
        
        Args:
            input_data: BIM material data + EPD products
            
        Returns:
            Evaluated products with similarity scores
        """
        # Validate input
        required_fields = ["bim_material", "epd_products"]
        self.validate_input(input_data, required_fields)
        
        bim_material = input_data["bim_material"]
        epd_products = input_data["epd_products"]
        
        if not epd_products:
            self.logger.warning("No EPD products to evaluate")
            return self.create_result(
                success=True,
                data={"evaluations": []}
            )
        
        self.logger.info(f"Evaluating {len(epd_products)} EPD products")
        
        evaluations = []
        
        # ✅ FIX: Evaluate ONE product at a time (like Python app)
        for i, product in enumerate(epd_products, 1):
            try:
                self.logger.debug(f"Evaluating product {i}/{len(epd_products)}")
                
                # Format data for SINGLE product evaluation
                formatted_data = self._format_single_product_evaluation(
                    bim_material,
                    product
                )
                
                prompt = f"""
    Evaluate the similarity between this BIM material and this EPD product.

    {formatted_data}

    Provide comprehensive 5-dimensional evaluation.
    Consider all available context including the comment field.
    """
                
                # Call LLM for SINGLE product evaluation
                evaluation_result = await self.llm_interpret(
                    prompt=prompt,
                    system_prompt=self.system_prompt_single,
                    temperature=0.0,
                    parse_json=True
                )
                
                # ✅ Add product URI to evaluation
                evaluation_result["epd_uri"] = product.get("uri", "")
                
                evaluations.append(evaluation_result)
                
            except Exception as e:
                self.logger.error(f"Failed to evaluate product {i}: {e}")
                # Continue with other products even if one fails
                continue
        
        self.logger.info(f"Completed {len(evaluations)} evaluations")
        
        return self.create_result(
            success=True,
            data={"evaluations": evaluations}
        )
    
    def _format_evaluation_data(
        self,
        bim_material: Dict[str, Any],
        epd_products: List[Dict[str, Any]]
    ) -> str:
        """Format BIM and EPD data for evaluation"""
        formatted = []
        
        # BIM Material Section
        formatted.append("=" * 80)
        formatted.append("BIM MATERIAL (Reference)")
        formatted.append("=" * 80)
        
        raw_data = bim_material.get("raw_data", {})
        formatted.append(f"Name: {raw_data.get('name')}")
        formatted.append(f"Asset Name: {raw_data.get('material_asset_name', 'N/A')}")
        formatted.append(f"Description: {raw_data.get('description', 'N/A')}")
        formatted.append(f"Keywords: {raw_data.get('keywords', 'N/A')}")
        formatted.append(f"Material Definition (Comment): {raw_data.get('comment', 'N/A')}")
        formatted.append(f"Primary Category: {raw_data.get('primary_category_label')}")
        formatted.append(f"Secondary Category: {raw_data.get('secondary_category_label', 'N/A')}")
        formatted.append(f"Class: {raw_data.get('class', 'N/A')}")
        formatted.append(f"Subclass: {raw_data.get('subclass', 'N/A')}")
        
        semantic = bim_material.get("semantic_interpretation", {})
        formatted.append(f"\nSemantic Interpretation:")
        formatted.append(f"  Type: {semantic.get('material_type')}")
        formatted.append(f"  Characteristics: {semantic.get('main_characteristics')}")
        formatted.append(f"  Uses: {semantic.get('typical_uses')}")
        
        # EPD Products Section
        formatted.append("\n" + "=" * 80)
        formatted.append("EPD PRODUCTS TO EVALUATE")
        formatted.append("=" * 80)

        for i, product in enumerate(epd_products, 1):
            formatted.append(f"\nProduct {i}:")
            # ✅ FIX: Access nested structure correctly
            formatted.append(f"  URI: {product.get('uri', 'N/A')}")
            formatted.append(f"  Name: {product.get('name', 'N/A')}")
            formatted.append(f"  Name Detail: {product.get('name_detail', 'N/A')}")
            formatted.append(f"  Category: {product.get('product_type_category', 'N/A')}")
            formatted.append(f"  Technical Purpose: {product.get('technical_purpose', 'N/A')}")
            formatted.append(f"  Technology: {product.get('technology_description', 'N/A')}")
            formatted.append(f"  Location: {product.get('location', 'N/A')}")
            formatted.append("")
        
        formatted.append("=" * 80)
        
        return "\n".join(formatted)
    
    def _format_single_product_evaluation(
        self,
        bim_material: Dict[str, Any],
        epd_product: Dict[str, Any]
    ) -> str:
        """Format BIM and single EPD product for evaluation"""
        formatted = []
        
        # BIM Material Section
        formatted.append("=" * 80)
        formatted.append("BIM MATERIAL (Reference)")
        formatted.append("=" * 80)
        
        raw_data = bim_material.get("raw_data", {})
        formatted.append(f"Name: {raw_data.get('name')}")
        formatted.append(f"Asset Name: {raw_data.get('material_asset_name', 'N/A')}")
        formatted.append(f"Description: {raw_data.get('description', 'N/A')}")
        formatted.append(f"Keywords: {raw_data.get('keywords', 'N/A')}")
        formatted.append(f"Material Definition (Comment): {raw_data.get('comment', 'N/A')}")
        formatted.append(f"Primary Category: {raw_data.get('primary_category_label')}")
        formatted.append(f"Secondary Category: {raw_data.get('secondary_category_label', 'N/A')}")
        
        # EPD Product Section (SINGLE product)
        formatted.append("\n" + "=" * 80)
        formatted.append("EPD PRODUCT TO EVALUATE")
        formatted.append("=" * 80)
        formatted.append(f"URI: {epd_product.get('uri', 'N/A')}")
        formatted.append(f"Name: {epd_product.get('name', 'N/A')}")
        formatted.append(f"Name Detail: {epd_product.get('name_detail', 'N/A')}")
        formatted.append(f"Category: {epd_product.get('product_type_category', 'N/A')}")
        formatted.append(f"Technical Purpose: {epd_product.get('technical_purpose', 'N/A')}")
        formatted.append(f"Technology: {epd_product.get('technology_description', 'N/A')}")
        formatted.append(f"Location: {epd_product.get('location', 'N/A')}")
        formatted.append("=" * 80)
        
        return "\n".join(formatted)



