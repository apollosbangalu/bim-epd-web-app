"""
Enhanced Agent Orchestrator - FIXED VERSION WITH PROPER CLIENT PASSING
Orchestrates complete 5-step cross-matching workflow

CRITICAL FIX: Now passes thesaurus_client to BIM Extractor Agent
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
    
    FIXED: Now properly passes thesaurus client to BIM Extractor
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
        
        # ✅ Log client initialization for debugging
        logger.info(f"✓ BIM SPARQL client initialized: {self.bim_client.endpoint}")
        logger.info(f"✓ EPD SPARQL client initialized: {self.epd_client.endpoint}")
        logger.info(f"✓ Thesaurus SPARQL client initialized: {self.thesaurus_client.endpoint}")
        
        # Initialize ALL specialized agents
        self._initialize_agents()
        
        logger.info("AgentOrchestrator initialized successfully")
    
    def _initialize_agents(self):
        """
        Initialize all specialized agents
        
        ✅ CRITICAL FIX: Pass thesaurus_client to BIM Extractor
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
            
            # Create final response
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "bim_material": bim_material,
                "concept_mappings": concept_mappings,
                "matches": ranked_matches,
                "workflow_steps": workflow_steps,
                "execution_time": execution_time,
                "metadata": {
                    "material_name": material_name,
                    "total_matches": len(ranked_matches),
                    "llm_provider": self.llm_provider
                }
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
            # ✅ Now uses thesaurus client internally
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
            
            # Extract the data portion
            data = result.get("data", {})
            
            step_time = time.time() - step_start
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Extracted: {data.get('raw_data', {}).get('name', 'Unknown')}",
                "details": {
                    "material_name": data.get("raw_data", {}).get("name"),
                    "primary_category": data.get("raw_data", {}).get("class"),
                    "secondary_category": data.get("raw_data", {}).get("subclass"),
                    "primary_thesaurus_uri": data.get("raw_data", {}).get("primary_category_thesaurus_uri"),
                    "secondary_thesaurus_uri": data.get("raw_data", {}).get("secondary_category_thesaurus_uri")
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
            result = await self.thesaurus_navigator.execute(bim_material)
            
            # Check if agent execution was successful
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            # Extract the data portion
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
                    "close_matches": close_count
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
            result = await self.epd_extractor.execute(concept_mappings)
            
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                workflow_steps[-1].update({
                    "status": "failed",
                    "error": error
                })
                return {"success": False, "error": error}
            
            data = result.get("data", {})
            candidates = data.get("candidates", [])
            
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
            
            return {"success": True, "data": data}
            
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
            # Call Similarity Judge Agent
            result = await self.similarity_judge.execute({
                "bim_material": bim_material,
                "epd_candidates": epd_candidates,
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
            evaluated = data.get("evaluated_products", [])
            
            step_time = time.time() - step_start
            
            avg_score = sum(p.get("total_score", 0) for p in evaluated) / len(evaluated) if evaluated else 0
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Evaluated {len(evaluated)} products (avg score: {avg_score:.2f})",
                "details": {
                    "evaluated_count": len(evaluated),
                    "average_score": round(avg_score, 2)
                }
            })
            
            return {"success": True, "data": data}
            
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
            # Call Ranking Agent
            result = await self.ranking_agent.execute({
                "evaluated_products": evaluated_products,
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