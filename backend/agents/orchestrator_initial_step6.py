"""
Enhanced Agent Orchestrator - COMPLETE VERSION WITH DETAILED INFO SUPPORT
Orchestrates complete 5-step (or 6-step) cross-matching workflow

FEATURES:
- CRITICAL FIX: Passes thesaurus_client to BIM Extractor Agent
- NEW: Optional Step 6 - Detailed Information Agent for comprehensive product details
- Fetches web links, GWP values, and technical specifications for top matches
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from llm import create_llm_client
from sparql.client import SPARQLClientFactory
from agents.bim_extractor import BIMExtractorAgent
from agents.thesaurus_navigator import ThesaurusNavigatorAgent
from agents.epd_extractor import EPDExtractorAgent
from agents.similarity_judge import SimilarityJudgeAgent
from agents.ranking_agent import RankingAgent
from agents.detailed_info_agent import DetailedInformationAgent  # ✅ NEW IMPORT

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates complete 5-step (or 6-step) cross-matching workflow
    
    Initializes ALL specialized agents and coordinates execution.
    
    FIXED: Now properly passes thesaurus client to BIM Extractor
    NEW: Optional Step 6 for fetching detailed product information
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",
        include_detailed_info: bool = False
    ):
        """
        Initialize orchestrator with all specialized agents
        
        Args:
            llm_provider: LLM provider name ('openai' or 'anthropic')
            include_detailed_info: Whether to fetch detailed product info (Step 6)
        """
        self.llm_provider = llm_provider
        self.include_detailed_info = include_detailed_info
        
        logger.info(f"Initializing AgentOrchestrator with {llm_provider}")
        logger.info(f"Detailed info enabled: {include_detailed_info}")  # ✅ NEW LOG
        
        # Create LLM client
        self.llm_client = create_llm_client(llm_provider)
        
        # Create SPARQL clients for each ontology
        self.bim_client = SPARQLClientFactory.create_bimtool_client()
        self.epd_client = SPARQLClientFactory.create_epd_client()
        self.thesaurus_client = SPARQLClientFactory.create_thesaurus_client()
        
        # ✅ Log client initialization for debugging
        active_bim = self.bim_client.get_active_endpoint() or "unknown"
        logger.info(f"✓ BIM SPARQL client initialized (using {active_bim})")

        active_epd = self.epd_client.get_active_endpoint() or "unknown"
        logger.info(f"✓ EPD SPARQL client initialized (using {active_epd})")

        active_thes = self.thesaurus_client.get_active_endpoint() or "unknown"
        logger.info(f"✓ Thesaurus SPARQL client initialized (using {active_thes})")
        
        # Initialize ALL specialized agents
        self._initialize_agents()
        
        logger.info("AgentOrchestrator initialized successfully")
    
    def _initialize_agents(self):
        """
        Initialize all specialized agents
        
        ✅ CRITICAL FIX: Pass thesaurus_client to BIM Extractor
        ✅ NEW: Conditionally initialize Detailed Information Agent
        """
        logger.info("Initializing specialized agents...")
        
        try:
            # Step 1 Agent: BIM Extractor
            # ✅ NOW INCLUDES THESAURUS CLIENT
            self.bim_extractor = BIMExtractorAgent(
                llm_client=self.llm_client,
                sparql_client=self.bim_client,
                thesaurus_client=self.thesaurus_client  # ✅ CRITICAL FIX
            )
            logger.info("✓ BIM Extractor Agent initialized (with thesaurus client)")
            
            # Step 2 Agent: Thesaurus Navigator  
            self.thesaurus_navigator = ThesaurusNavigatorAgent(
                llm_client=self.llm_client,
                sparql_client=self.thesaurus_client
            )
            logger.info("✓ Thesaurus Navigator Agent initialized")
            
            # Step 3 Agent: EPD Extractor
            self.epd_extractor = EPDExtractorAgent(
                llm_client=self.llm_client,
                sparql_client=self.epd_client
            )
            logger.info("✓ EPD Extractor Agent initialized")
            
            # Step 4 Agent: Similarity Judge
            self.similarity_judge = SimilarityJudgeAgent(
                llm_client=self.llm_client,
                sparql_client=None  # Doesn't need SPARQL
            )
            logger.info("✓ Similarity Judge Agent initialized")
            
            # Step 5 Agent: Ranking Agent
            self.ranking_agent = RankingAgent(
                llm_client=self.llm_client,
                sparql_client=None  # Doesn't need SPARQL
            )
            logger.info("✓ Ranking Agent initialized")
            
            # ✅ NEW: Step 6 Agent - Detailed Information (OPTIONAL)
            if self.include_detailed_info:
                self.detailed_info_agent = DetailedInformationAgent(
                    llm_client=self.llm_client,
                    sparql_client=self.epd_client
                )
                logger.info("✓ Detailed Information Agent initialized (OPTIONAL STEP 6)")
            else:
                self.detailed_info_agent = None
                logger.info("⊘ Detailed Information Agent disabled")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}", exc_info=True)
            raise RuntimeError(f"Agent initialization failed: {e}")
    
    async def execute_workflow(
        self,
        material_name: str,
        top_n: int = 10,
        min_confidence: Optional[str] = None,
        max_details: int = 5  # ✅ NEW PARAMETER: Number of products to fetch details for
    ) -> Dict[str, Any]:
        """
        Execute complete 5-step (or 6-step) cross-matching workflow
        
        Returns structured result with all workflow steps tracked.
        
        Args:
            material_name: BIM material name to match
            top_n: Number of top matches to return
            min_confidence: Minimum confidence level filter
            max_details: Number of products to fetch detailed info for (if enabled)
        """
        start_time = time.time()
        workflow_steps = []
        
        logger.info("=" * 80)
        logger.info(f"Starting workflow for: {material_name}")
        logger.info("=" * 80)
        
        try:
            # STEP 1: Extract BIM Material
            # ✅ Now uses thesaurus client internally for URI transformation
            step1_result = await self._execute_step_1(material_name, workflow_steps)
            if not step1_result["success"]:
                return self._create_error_response("BIM material not found", workflow_steps)
            
            bim_material = step1_result["data"]
            
            # ✅ LOG THE TRANSFORMATION RESULT
            raw_data = bim_material.get("raw_data", {})
            primary_thesaurus = raw_data.get("primary_category_thesaurus_uri")
            secondary_thesaurus = raw_data.get("secondary_category_thesaurus_uri")
            
            logger.info(f"BIM Material extracted:")
            logger.info(f"  - Primary thesaurus URI: {primary_thesaurus}")
            logger.info(f"  - Secondary thesaurus URI: {secondary_thesaurus}")
            
            # ✅ VALIDATE TRANSFORMATION SUCCESS
            if not primary_thesaurus:
                logger.error("❌ PRIMARY THESAURUS URI MISSING - Step 1 transformation failed!")
                return self._create_error_response(
                    "BIM category transformation failed - no thesaurus URI found",
                    workflow_steps
                )
            
            # STEP 2: Navigate Thesaurus
            step2_result = await self._execute_step_2(bim_material, workflow_steps)
            if not step2_result["success"]:
                return self._create_error_response("Thesaurus navigation failed", workflow_steps)
            
            concept_mappings = step2_result["data"]
            
            # STEP 3: Extract EPD Products
            step3_result = await self._execute_step_3(concept_mappings, workflow_steps)
            if not step3_result["success"]:
                return self._create_error_response("EPD extraction failed", workflow_steps)
            
            epd_candidates = step3_result["data"]
            
            # STEP 4: Evaluate Similarity
            step4_result = await self._execute_step_4(
                bim_material, epd_candidates, concept_mappings, workflow_steps
            )
            if not step4_result["success"]:
                return self._create_error_response("Similarity evaluation failed", workflow_steps)
            
            evaluated_products = step4_result["data"]
            
            # STEP 5: Rank and Filter
            step5_result = await self._execute_step_5(
                evaluated_products, top_n, min_confidence, workflow_steps
            )
            if not step5_result["success"]:
                return self._create_error_response("Ranking failed", workflow_steps)
            
            ranked_matches = step5_result["data"]
            
            # ✅ NEW: STEP 6 - Detailed Information (OPTIONAL)
            if self.include_detailed_info and self.detailed_info_agent and ranked_matches:
                step6_result = await self._execute_step_6(
                    ranked_matches, max_details, workflow_steps
                )
                
                if step6_result["success"]:
                    # Replace ranked_matches with enhanced version
                    ranked_matches = step6_result["data"]
                    logger.info("✓ Step 6 completed: Matches enhanced with detailed info")
                else:
                    # Step 6 failed but workflow continues
                    logger.warning(f"⚠ Step 6 failed: {step6_result.get('error')}")
                    logger.info("Continuing with basic results...")
            
            # Create final response
            execution_time = time.time() - start_time

            # Extract total candidates from Step 3 data
            total_candidates = epd_candidates.get("candidates", [])
            
            response = {
                "success": True,
                "bim_material": bim_material.get("raw_data", {}),
                "concept_mappings": concept_mappings,
                "matches": ranked_matches,
                "workflow_steps": workflow_steps,
                "total_candidates": len(total_candidates),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("=" * 80)
            logger.info(f"Workflow completed in {execution_time:.2f}s")
            logger.info(f"Found {len(ranked_matches)} matches from {len(total_candidates)} candidates")
            logger.info("=" * 80)
            
            return response
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
            
            # Update last step as failed if it was in progress
            if workflow_steps and workflow_steps[-1].get("status") == "in_progress":
                workflow_steps[-1].update({
                    "status": "failed",
                    "completed_at": datetime.now().isoformat(),
                    "error": str(e)
                })
            
            return {
                "success": False,
                "error": str(e),
                "workflow_steps": workflow_steps,
                "matches": [],
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_step_1(
        self, 
        material_name: str, 
        workflow_steps: List[Dict]
    ) -> Dict[str, Any]:
        """Execute Step 1: BIM Material Extraction"""
        step_start = time.time()
        
        workflow_steps.append({
            "step_number": 1,
            "step_name": "BIM Material Extraction",
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        })
        
        try:
            # Call BIM Extractor Agent
            result = await self.bim_extractor.execute({"material_name": material_name})
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            data = result.get("data", {})
            bim_material = data.get("bim_material", {})
            
            step_time = time.time() - step_start
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Extracted: {bim_material.get('name', 'Unknown')}",
                "details": {
                    "material_name": bim_material.get("name"),
                    "primary_category": bim_material.get("raw_data", {}).get("primary_category_label"),
                    "secondary_category": bim_material.get("raw_data", {}).get("secondary_category_label")
                }
            })
            
            return {"success": True, "data": bim_material}
            
        except Exception as e:
            workflow_steps[-1].update({
                "status": "failed",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
    
    async def _execute_step_2(
        self, 
        bim_material: Dict[str, Any], 
        workflow_steps: List[Dict]
    ) -> Dict[str, Any]:
        """Execute Step 2: Thesaurus Navigation"""
        step_start = time.time()
        
        workflow_steps.append({
            "step_number": 2,
            "step_name": "Thesaurus Navigation",
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        })
        
        try:
            # Call Thesaurus Navigator Agent
            result = await self.thesaurus_navigator.execute({"bim_material": bim_material})
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            data = result.get("data", {})
            concept_mappings = data.get("concept_mappings", {})
            
            step_time = time.time() - step_start
            
            # Count different types of mappings
            all_concepts = concept_mappings.get("all_mapped_concepts", [])
            exact_matches = [c for c in all_concepts if c.get("match_quality") == "exactMatch"]
            close_matches = [c for c in all_concepts if c.get("match_quality") == "closeMatch"]
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Found {len(all_concepts)} concepts ({len(exact_matches)} exact, {len(close_matches)} close)",
                "details": {
                    "total_concepts": len(all_concepts),
                    "exact_matches": len(exact_matches),
                    "close_matches": len(close_matches)
                }
            })
            
            return {"success": True, "data": concept_mappings}
            
        except Exception as e:
            workflow_steps[-1].update({
                "status": "failed",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
    
    async def _execute_step_3(
        self, 
        concept_mappings: Dict[str, Any], 
        workflow_steps: List[Dict]
    ) -> Dict[str, Any]:
        """Execute Step 3: EPD Product Extraction"""
        step_start = time.time()
        
        workflow_steps.append({
            "step_number": 3,
            "step_name": "EPD Product Search",
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        })
        
        try:
            # Call EPD Extractor Agent
            result = await self.epd_extractor.execute(concept_mappings)
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            data = result.get("data", {})
            candidates = data.get("products", [])
            
            step_time = time.time() - step_start
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Found {len(candidates)} EPD candidates",
                "details": {
                    "total_candidates": len(candidates)
                }
            })
            
            return {"success": True, "data": {"candidates": candidates}} 
            
        except Exception as e:
            workflow_steps[-1].update({
                "status": "failed",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
    
    async def _execute_step_4(
        self, 
        bim_material: Dict[str, Any],
        epd_candidates: Dict[str, Any],
        concept_mappings: Dict[str, Any],
        workflow_steps: List[Dict]
    ) -> Dict[str, Any]:
        """Execute Step 4: Similarity Evaluation"""
        step_start = time.time()
        
        workflow_steps.append({
            "step_number": 4,
            "step_name": "Similarity Evaluation",
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        })
        
        try:
            # ✅ FIX: Extract candidates list from dict
            candidates_list = epd_candidates.get("candidates", [])
            
            # ✅ CRITICAL: Store candidates for later attachment
            epd_products_by_uri = {
                product.get("uri"): product 
                for product in candidates_list
            }
            
            # Call Similarity Judge
            result = await self.similarity_judge.execute({
                "bim_material": bim_material,
                "epd_products": candidates_list,
                "concept_mappings": concept_mappings
            })
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            data = result.get("data", {})
            evaluations = data.get("evaluations", [])
            
            # ✅ CRITICAL FIX: Attach EPD product data to each evaluation
            enriched_evaluations = []
            for eval_data in evaluations:
                epd_uri = eval_data.get("epd_uri")
                epd_product = epd_products_by_uri.get(epd_uri, {})
                
                # Create enriched evaluation with product data
                enriched_eval = {
                    **eval_data,
                    "epd_product": epd_product  # ← THE MISSING PIECE!
                }
                enriched_evaluations.append(enriched_eval)
            
            step_time = time.time() - step_start
            
            avg_score = sum(p.get("total_score", 0) for p in enriched_evaluations) / len(enriched_evaluations) if enriched_evaluations else 0
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Evaluated {len(enriched_evaluations)} products (avg score: {avg_score:.2f})",
                "details": {
                    "evaluated_count": len(enriched_evaluations),
                    "average_score": round(avg_score, 2)
                }
            })
            
            # ✅ FIX: Return enriched evaluations with product data
            return {"success": True, "data": {"evaluations": enriched_evaluations}}
            
        except Exception as e:
            workflow_steps[-1].update({
                "status": "failed",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
    
    async def _execute_step_5(
        self, 
        evaluated_products: Dict[str, Any],
        top_n: int,
        min_confidence: Optional[str],
        workflow_steps: List[Dict]
    ) -> Dict[str, Any]:
        """Execute Step 5: Ranking and Filtering"""
        step_start = time.time()
        
        workflow_steps.append({
            "step_number": 5,
            "step_name": "Ranking & Filtering",
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        })
        
        try:
            # ✅ FIX: Extract evaluations list from dict
            evaluations_list = evaluated_products.get("evaluations", [])
            
            # ✅ FIX: Use correct key "evaluations" and pass list
            result = await self.ranking_agent.execute({
                "evaluations": evaluations_list,
                "concept_mappings": [],  # Empty for now, can enhance later
                "top_n": top_n,
                "min_confidence": min_confidence
            })
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            data = result.get("data", {})
            ranked = data.get("ranked_matches", [])
            
            step_time = time.time() - step_start
            
            # Count by confidence level
            exact_count = sum(1 for m in ranked if m.get("confidence") == "HIGH")
            close_count = sum(1 for m in ranked if m.get("confidence") == "MEDIUM")
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Ranked {len(ranked)} matches ({exact_count} high, {close_count} medium confidence)",
                "details": {
                    "total_matches": len(ranked),
                    "high_confidence": exact_count,
                    "medium_confidence": close_count
                }
            })
            
            return {"success": True, "data": ranked}
            
        except Exception as e:
            workflow_steps[-1].update({
                "status": "failed",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
    
    async def _execute_step_6(
        self, 
        ranked_matches: List[Dict[str, Any]],
        max_details: int,
        workflow_steps: List[Dict]
    ) -> Dict[str, Any]:
        """
        Execute Step 6: Detailed Information (OPTIONAL)
        
        Fetches comprehensive details for top-ranked EPD products:
        - ProcessDataSet URI (graph identifier)
        - Uri property (EPD online web link)
        - Total GWP (Global Warming Potential)
        - Technical specifications
        - Product classifications
        """
        step_start = time.time()
        
        workflow_steps.append({
            "step_number": 6,
            "step_name": "Detailed Information",
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        })
        
        try:
            logger.info(f"Step 6: Fetching detailed info for top {max_details} products...")
            
            # Call Detailed Information Agent
            result = await self.detailed_info_agent.execute({
                "ranked_matches": ranked_matches,
                "max_details": max_details
            })
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "completed_at": datetime.now().isoformat(),
                    "error": error,
                    "result_summary": "Detail fetching failed (continuing with basic results)"
                })
                return {"success": False, "error": error, "data": ranked_matches}
            
            data = result.get("data", {})
            enhanced_matches = data.get("enhanced_matches", ranked_matches)
            
            step_time = time.time() - step_start
            
            # Count how many matches have detailed info
            with_details = sum(1 for m in enhanced_matches if m.get("detailed_info"))
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Enhanced {with_details} products with detailed info",
                "details": {
                    "products_enhanced": with_details,
                    "total_products": len(enhanced_matches)
                }
            })
            
            logger.info(f"✓ Step 6 completed: Enhanced {with_details}/{len(enhanced_matches)} products")
            
            return {"success": True, "data": enhanced_matches}
            
        except Exception as e:
            step_time = time.time() - step_start
            workflow_steps[-1].update({
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "error": str(e),
                "result_summary": "Detail fetching failed (continuing with basic results)"
            })
            logger.error(f"Step 6 failed: {e}", exc_info=True)
            # Return original ranked_matches if Step 6 fails
            return {"success": False, "error": str(e), "data": ranked_matches}
    
    def _create_error_response(
        self, 
        error_message: str, 
        workflow_steps: List[Dict]
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "error": error_message,
            "workflow_steps": workflow_steps,
            "matches": []
        }