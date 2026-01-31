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
        Evaluate similarity for all EPD products
        
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
        
        try:
            # Format data for LLM
            formatted_data = self._format_evaluation_data(
                bim_material,
                epd_products
            )
            
            prompt = f"""
Evaluate the similarity between this BIM material and each EPD product.

{formatted_data}

Provide comprehensive 5-dimensional evaluation for EACH product.
Be thorough and consider all available context including the comment field.
"""
            
            # Call LLM for evaluation
            evaluation_result = await self.llm_interpret(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.0,
                parse_json=True
            )
            
            # Validate response
            if "evaluations" not in evaluation_result:
                raise ValueError("Invalid evaluation response format")
            
            evaluations = evaluation_result["evaluations"]
            
            # Ensure all products were evaluated
            if len(evaluations) != len(epd_products):
                self.logger.warning(
                    f"Expected {len(epd_products)} evaluations, "
                    f"got {len(evaluations)}"
                )
            
            self.logger.info(f"Completed {len(evaluations)} evaluations")
            
            return self.create_result(
                success=True,
                data={"evaluations": evaluations}
            )
            
        except Exception as e:
            self.logger.error(f"Similarity evaluation failed: {e}", exc_info=True)
            return self.create_result(
                success=False,
                error=str(e)
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
            formatted.append(f"  URI: {product.get('uri')}")
            formatted.append(f"  Name: {product.get('name')}")
            formatted.append(f"  Name Detail: {product.get('name_detail', 'N/A')}")
            formatted.append(f"  Category: {product.get('product_type_category', 'N/A')}")
            formatted.append(f"  Technical Purpose: {product.get('technical_purpose', 'N/A')}")
            formatted.append(f"  Technology: {product.get('technology_description', 'N/A')}")
            formatted.append(f"  Location: {product.get('location', 'N/A')}")
            formatted.append("")
        
        formatted.append("=" * 80)
        
        return "\n".join(formatted)
