"""
Ranking Agent Module
Fifth agent in the 5-step workflow

Ranks and filters evaluated EPD products based on similarity scores and match types.

RANKING STRATEGY:
1. Exact Match Priority: exactMatch concepts ranked highest
2. Close Match Second: closeMatch concepts next
3. Score-based: Within same match type, sort by total score
4. Confidence Assignment: HIGH (>0.7), MEDIUM (0.5-0.7), LOW (<0.5)
5. Filtering: Optional minimum confidence threshold

Input: Evaluated products with scores + concept mappings
Output: Ranked, filtered list of top matches
"""
import logging
from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from llm.base import BaseLLMClient
from sparql.client import SPARQLClient

logger = logging.getLogger(__name__)


class RankingAgent(BaseAgent):
    """
    Agent for ranking and filtering match results
    
    Step 5 of 5: Rank products with exact match priority and score-based sorting
    """
    
    def __init__(self, llm_client: BaseLLMClient, sparql_client: SPARQLClient):
        """Initialize Ranking Agent"""
        super().__init__(llm_client, sparql_client, "RankingAgent")
        
        # Confidence thresholds
        self.HIGH_THRESHOLD = 0.7
        self.MEDIUM_THRESHOLD = 0.5
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rank and filter evaluated products
        
        Args:
            input_data: {
                "evaluations": List of evaluated products,
                "concept_mappings": Thesaurus mappings,
                "top_n": Number of results (default 10),
                "min_confidence": Optional confidence filter
            }
            
        Returns:
            Ranked and filtered match results
        """
        # Validate input
        required_fields = ["evaluations"]
        self.validate_input(input_data, required_fields)
        
        evaluations = input_data["evaluations"]
        concept_mappings = input_data.get("concept_mappings", [])
        top_n = input_data.get("top_n", 10)
        min_confidence = input_data.get("min_confidence")
        
        if not evaluations:
            self.logger.warning("No evaluations to rank")
            return self.create_result(
                success=True,
                data={"ranked_matches": []}
            )
        
        self.logger.info(f"Ranking {len(evaluations)} evaluated products")
        
        try:
            # Step 1: Assign confidence levels
            scored_evaluations = []
            for eval_data in evaluations:
                scores = eval_data.get("scores", {})
                total_score = scores.get("total_score", 0.0)
                
                # Assign confidence level
                if total_score >= self.HIGH_THRESHOLD:
                    confidence = "HIGH"
                elif total_score >= self.MEDIUM_THRESHOLD:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"
                
                scored_evaluations.append({
                    **eval_data,
                    "confidence": confidence,
                    "total_score": total_score
                })
            
            # Step 2: Determine match types from concept mappings
            epd_concept_match_types = self._extract_match_types(concept_mappings)
            
            # Step 3: Categorize by match type
            exact_matches = []
            close_matches = []
            other_matches = []
            
            for eval_data in scored_evaluations:
                epd_uri = eval_data.get("epd_uri")
                
                # Determine match type based on EPD concept
                # This is a simplified heuristic - in production, would map URIs precisely
                match_type = self._determine_match_type(
                    epd_uri,
                    epd_concept_match_types
                )
                
                if match_type == "exactMatch":
                    exact_matches.append(eval_data)
                elif match_type == "closeMatch":
                    close_matches.append(eval_data)
                else:
                    other_matches.append(eval_data)
            
            # Step 4: Sort within each category by score
            exact_matches.sort(key=lambda x: x["total_score"], reverse=True)
            close_matches.sort(key=lambda x: x["total_score"], reverse=True)
            other_matches.sort(key=lambda x: x["total_score"], reverse=True)
            
            # Step 5: Combine in priority order
            ranked = exact_matches + close_matches + other_matches
            
            # Step 6: Filter by minimum confidence if specified
            if min_confidence:
                confidence_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
                min_level = confidence_order.get(min_confidence, 0)
                
                ranked = [
                    r for r in ranked
                    if confidence_order.get(r["confidence"], 0) >= min_level
                ]
                
                self.logger.info(
                    f"Filtered to {len(ranked)} matches with "
                    f"min confidence {min_confidence}"
                )
            
            # Step 7: Take top N
            ranked = ranked[:top_n]
            
            # Step 8: Add rank positions
            for i, match in enumerate(ranked, 1):
                match["rank"] = i
            
            self.logger.info(
                f"Final ranking: {len(ranked)} matches "
                f"(exact: {len([r for r in ranked if r.get('match_type') == 'exactMatch'])}, "
                f"close: {len([r for r in ranked if r.get('match_type') == 'closeMatch'])})"
            )
            
            return self.create_result(
                success=True,
                data={
                    "ranked_matches": ranked,
                    "ranking_summary": {
                        "total_evaluated": len(evaluations),
                        "total_ranked": len(ranked),
                        "exact_matches": len(exact_matches),
                        "close_matches": len(close_matches),
                        "top_n": top_n,
                        "min_confidence": min_confidence
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Ranking failed: {e}", exc_info=True)
            return self.create_result(
                success=False,
                error=str(e)
            )
    
    def _extract_match_types(
        self,
        concept_mappings: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Extract match types for EPD concepts
        
        Returns:
            Dict mapping EPD concept labels to match types
        """
        match_types = {}
        
        for mapping in concept_mappings:
            epd_label = mapping.get("epd_label")
            match_type = mapping.get("match_type")
            
            if epd_label and match_type:
                # Keep the best match type (exact > close)
                existing = match_types.get(epd_label)
                if not existing or match_type == "exactMatch":
                    match_types[epd_label] = match_type
        
        return match_types
    
    def _determine_match_type(
        self,
        epd_uri: str,
        epd_concept_match_types: Dict[str, str]
    ) -> str:
        """
        Determine match type for an EPD product
        
        This is a heuristic based on product category matching concept labels.
        In production, would use precise URI-to-concept mapping.
        
        Args:
            epd_uri: EPD product URI
            epd_concept_match_types: Match types for EPD concepts
            
        Returns:
            Match type: "exactMatch", "closeMatch", or "other"
        """
        # Default to score-based ranking
        return "other"
        
        # TODO: In production, implement precise matching:
        # 1. Query EPD product's category
        # 2. Find corresponding concept in thesaurus
        # 3. Return that concept's match type
