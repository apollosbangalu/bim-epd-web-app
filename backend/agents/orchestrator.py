"""
Enhanced Agent Orchestrator with proper agent initialization
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

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates complete 5-step cross-matching workflow
    
    Initializes ALL specialized agents and coordinates execution.
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
            include_detailed_info: Whether to fetch detailed product info
        """
        self.llm_provider = llm_provider
        self.include_detailed_info = include_detailed_info
        
        logger.info(f"Initializing AgentOrchestrator with {llm_provider}")
        
        # Create LLM client
        self.llm_client = create_llm_client(llm_provider)
        
        # Create SPARQL clients for each ontology
        self.bim_client = SPARQLClientFactory.create_bimtool_client()
        self.epd_client = SPARQLClientFactory.create_epd_client()
        self.thesaurus_client = SPARQLClientFactory.create_thesaurus_client()
        
        # Initialize ALL specialized agents
        self._initialize_agents()
        
        logger.info("AgentOrchestrator initialized successfully")
    
    def _initialize_agents(self):
        """Initialize all specialized agents"""
        logger.info("Initializing specialized agents...")
        
        try:
            # Step 1 Agent: BIM Extractor
            self.bim_extractor = BIMExtractorAgent(
                llm_client=self.llm_client,
                sparql_client=self.bim_client
            )
            logger.info("✓ BIM Extractor Agent initialized")
            
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
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}", exc_info=True)
            raise RuntimeError(f"Agent initialization failed: {e}")
    
    async def execute_workflow(
        self,
        material_name: str,
        top_n: int = 10,
        min_confidence: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute complete 5-step cross-matching workflow
        
        Returns structured result with all workflow steps tracked.
        """
        start_time = time.time()
        workflow_steps = []
        
        logger.info("=" * 80)
        logger.info(f"Starting workflow for: {material_name}")
        logger.info("=" * 80)
        
        try:
            # STEP 1: Extract BIM Material
            step1_result = await self._execute_step_1(material_name, workflow_steps)
            if not step1_result["success"]:
                return self._create_error_response("BIM material not found", workflow_steps)
            
            bim_material = step1_result["data"]
            
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
            
            # Create final response
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "bim_material": bim_material,
                "concept_mappings": concept_mappings,
                "matches": ranked_matches,
                "workflow_steps": workflow_steps,
                "total_candidates": len(epd_candidates),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
            return self._create_error_response(str(e), workflow_steps)

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
            result = await self.bim_extractor.execute({
                "material_name": material_name
            })
            
            # Check if agent execution was successful
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            # ✅ FIX: Extract the DATA portion from agent result
            data = result.get("data", {})
            
            step_time = time.time() - step_start
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Extracted {data.get('raw_data', {}).get('name', 'material')} with {len(data.get('raw_data', {}))} fields",
                "details": {
                    "material_name": data.get("raw_data", {}).get("name"),
                    "primary_category": data.get("raw_data", {}).get("primary_category_label"),
                    "fields_extracted": len(data.get("raw_data", {}))
                }
            })
            
            # Return just the data portion (not the whole agent result)
            return {"success": True, "data": data}
            
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
            # bim_material already has the correct structure: {"raw_data": {...}, "semantic_interpretation": {...}}
            result = await self.thesaurus_navigator.execute(bim_material)
            
            # Check if agent execution was successful
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            # ✅ FIX: Extract the DATA portion
            data = result.get("data", {})
            
            step_time = time.time() - step_start
            
            # Extract mapping statistics
            mappings = data.get("mappings", [])
            exact_count = sum(1 for m in mappings if m.get("match_type") == "exactMatch")
            close_count = sum(1 for m in mappings if m.get("match_type") == "closeMatch")
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Found {len(mappings)} concept mappings ({exact_count} exact, {close_count} close)",
                "details": {
                    "total_mappings": len(mappings),
                    "exact_matches": exact_count,
                    "close_matches": close_count,
                    "concepts": [m.get("epd_label") for m in mappings[:5]]
                }
            })
            
            # Return just the data portion
            return {"success": True, "data": data}
            
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
            result = await self.epd_extractor.execute({
                "concept_mappings": concept_mappings.get("mappings", []),
                "max_products": 50,
                "include_detailed_info": self.include_detailed_info
            })
            
            # Check if agent execution was successful
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            # ✅ FIX: Extract the DATA portion
            # EPD extractor returns {"products": [...]} in its data
            data = result.get("data", {})
            products = data.get("products", [])
            
            step_time = time.time() - step_start
            
            # Extract product statistics
            exact_products = sum(1 for p in products if p.get("match_quality") == "exact")
            close_products = sum(1 for p in products if p.get("match_quality") == "close")
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Retrieved {len(products)} EPD products ({exact_products} from exact matches, {close_products} from close matches)",
                "details": {
                    "total_products": len(products),
                    "from_exact_matches": exact_products,
                    "from_close_matches": close_products,
                    "sample_products": [p.get("raw_data", {}).get("name") for p in products[:3]]
                }
            })
            
            # Return the products list directly (for consistency with Step 4's expectations)
            return {"success": True, "data": products}
            
        except Exception as e:
            workflow_steps[-1].update({
                "status": "failed",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}


    async def _execute_step_4(
        self,
        bim_material: Dict[str, Any],
        epd_candidates: List[Dict[str, Any]],
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
            # Call Similarity Judge Agent
            result = await self.similarity_judge.execute({
                "bim_material": bim_material,
                "epd_products": epd_candidates,  # Note: agent expects "epd_products" not "epd_candidates"
                "concept_mappings": concept_mappings
            })
            
            # Check if agent execution was successful
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            # ✅ FIX: Extract the DATA portion
            data = result.get("data", {})
            evaluations = data.get("evaluations", [])
            
            step_time = time.time() - step_start
            
            # Extract evaluation statistics
            avg_score = sum(e.get("scores", {}).get("total_score", 0) for e in evaluations) / len(evaluations) if evaluations else 0
            high_scores = sum(1 for e in evaluations if e.get("scores", {}).get("total_score", 0) >= 0.7)
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Evaluated {len(evaluations)} products (avg score: {avg_score:.2f}, {high_scores} high-confidence)",
                "details": {
                    "total_evaluated": len(evaluations),
                    "average_score": round(avg_score, 3),
                    "high_confidence_count": high_scores,
                    "dimensions": ["name", "category", "functional", "technical", "specificity"]
                }
            })
            
            # Return the evaluations list
            return {"success": True, "data": evaluations}
            
        except Exception as e:
            workflow_steps[-1].update({
                "status": "failed",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}


    async def _execute_step_5(
        self,
        evaluated_products: List[Dict[str, Any]],
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
            # Call Ranking Agent
            result = await self.ranking_agent.execute({
                "evaluations": evaluated_products,
                "concept_mappings": [],
                "top_n": top_n,
                "min_confidence": min_confidence
            })
            
            # Check if agent execution was successful
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            # ✅ FIX: Extract the DATA portion
            data = result.get("data", {})
            ranked_matches = data.get("ranked_matches", [])
            summary = data.get("ranking_summary", {})
            
            step_time = time.time() - step_start
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Ranked {summary.get('total_ranked', 0)} matches (top {top_n} returned)",
                "details": {
                    "total_ranked": summary.get("total_ranked", 0),
                    "exact_matches": summary.get("exact_matches", 0),
                    "close_matches": summary.get("close_matches", 0),
                    "top_n": top_n,
                    "confidence_levels": {
                        "HIGH": sum(1 for m in ranked_matches if m.get("confidence") == "HIGH"),
                        "MEDIUM": sum(1 for m in ranked_matches if m.get("confidence") == "MEDIUM"),
                        "LOW": sum(1 for m in ranked_matches if m.get("confidence") == "LOW")
                    }
                }
            })
            
            # Return the ranked matches
            return {"success": True, "data": ranked_matches}
            
        except Exception as e:
            workflow_steps[-1].update({
                "status": "failed",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}

    def _create_error_response(
        self, 
        error_message: str, 
        workflow_steps: List[Dict]
    ) -> Dict[str, Any]:
        """Create error response with workflow state"""
        return {
            "success": False,
            "error": error_message,
            "workflow_steps": workflow_steps,
            "timestamp": datetime.now().isoformat()
        }