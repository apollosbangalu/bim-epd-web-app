"""
Agent Orchestrator Module
Coordinates the complete 5-step cross-matching workflow

WORKFLOW:
1. BIM Extraction: Extract material data (9+ fields)
2. Thesaurus Navigation: Find semantic concept mappings
3. EPD Extraction: Retrieve matching EPD products
4. Similarity Evaluation: Multi-dimensional similarity scoring
5. Ranking & Filtering: Prioritize and filter results
6. (Optional) Detailed Information: Fetch comprehensive details

Manages:
- Agent initialization
- Workflow execution
- Step tracking
- Error handling
- Progress reporting
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncIterator
from enum import Enum

from llm import create_llm_client
from sparql.client import SPARQLClientFactory
from agents.bim_extractor import BIMExtractorAgent
from agents.thesaurus_navigator import ThesaurusNavigatorAgent
from agents.epd_extractor import EPDExtractorAgent
from agents.similarity_judge import SimilarityJudgeAgent
from agents.ranking_agent import RankingAgent
from agents.detailed_info_agent import DetailedInformationAgent

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentOrchestrator:
    """
    Orchestrates the complete cross-matching workflow
    
    Initializes all agents and coordinates their execution in sequence.
    Tracks progress and handles errors at each step.
    """
    
    def __init__(self, llm_provider: str = "openai", include_detailed_info: bool = True):
        """
        Initialize orchestrator with all agents
        
        Args:
            llm_provider: LLM provider to use ('openai' or 'anthropic')
            include_detailed_info: Whether to fetch detailed info for top matches
        """
        self.llm_provider = llm_provider
        self.include_detailed_info = include_detailed_info
        
        logger.info(f"Initializing Agent Orchestrator with LLM: {llm_provider}")
        
        try:
            # Initialize LLM client
            self.llm_client = create_llm_client(llm_provider)
            
            # Initialize SPARQL clients for each repository
            self.bim_sparql = SPARQLClientFactory.create_bimtool_client()
            self.epd_sparql = SPARQLClientFactory.create_epd_client()
            self.thesaurus_sparql = SPARQLClientFactory.create_thesaurus_client()
            
            # Initialize all agents
            self.bim_extractor = BIMExtractorAgent(
                self.llm_client,
                self.bim_sparql
            )
            
            self.thesaurus_navigator = ThesaurusNavigatorAgent(
                self.llm_client,
                self.thesaurus_sparql
            )
            
            self.epd_extractor = EPDExtractorAgent(
                self.llm_client,
                self.epd_sparql
            )
            
            self.similarity_judge = SimilarityJudgeAgent(
                self.llm_client,
                self.epd_sparql
            )
            
            self.ranking_agent = RankingAgent(
                self.llm_client,
                self.epd_sparql
            )
            
            if include_detailed_info:
                self.detailed_info_agent = DetailedInformationAgent(
                    self.llm_client,
                    self.epd_sparql
                )
            
            logger.info("All agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    async def execute_workflow(
        self,
        material_name: str,
        top_n: int = 10,
        min_confidence: Optional[str] = None,
        stream_progress: bool = False
    ) -> Dict[str, Any]:
        """
        Execute complete cross-matching workflow
        
        Args:
            material_name: BIM material name to match
            top_n: Number of top matches to return
            min_confidence: Optional minimum confidence filter
            stream_progress: Whether to yield progress updates
            
        Returns:
            Complete workflow results with all 5 steps
        """
        start_time = time.time()
        
        logger.info("=" * 80)
        logger.info(f"Starting cross-matching workflow for: {material_name}")
        logger.info("=" * 80)
        
        # Initialize workflow state
        workflow_state = {
            "material_name": material_name,
            "top_n": top_n,
            "min_confidence": min_confidence,
            "steps": [],
            "started_at": datetime.now().isoformat()
        }
        
        try:
            # ================================================================
            # STEP 1: BIM MATERIAL EXTRACTION
            # ================================================================
            step1_result = await self._execute_step(
                step_number=1,
                step_name="BIM Material Extraction",
                agent=self.bim_extractor,
                input_data={"material_name": material_name},
                workflow_state=workflow_state
            )
            
            if not step1_result["success"]:
                return self._create_error_response(
                    "Step 1 failed: BIM material not found",
                    workflow_state
                )
            
            bim_material = step1_result["data"]
            
            # ================================================================
            # STEP 2: THESAURUS NAVIGATION
            # ================================================================
            step2_result = await self._execute_step(
                step_number=2,
                step_name="Thesaurus Navigation",
                agent=self.thesaurus_navigator,
                input_data=bim_material,
                workflow_state=workflow_state
            )
            
            if not step2_result["success"]:
                return self._create_error_response(
                    "Step 2 failed: Thesaurus navigation failed",
                    workflow_state
                )
            
            concept_mappings = step2_result["data"]
            
            # ================================================================
            # STEP 3: EPD PRODUCT EXTRACTION
            # ================================================================
            step3_result = await self._execute_step(
                step_number=3,
                step_name="EPD Product Extraction",
                agent=self.epd_extractor,
                input_data=concept_mappings,
                workflow_state=workflow_state
            )
            
            if not step3_result["success"]:
                return self._create_error_response(
                    "Step 3 failed: EPD extraction failed",
                    workflow_state
                )
            
            epd_products = step3_result["data"]["products"]
            
            if not epd_products:
                logger.warning("No EPD products found to evaluate")
                return self._create_empty_response(
                    "No matching EPD products found",
                    workflow_state,
                    bim_material,
                    concept_mappings
                )
            
            # ================================================================
            # STEP 4: SIMILARITY EVALUATION
            # ================================================================
            step4_result = await self._execute_step(
                step_number=4,
                step_name="Similarity Evaluation",
                agent=self.similarity_judge,
                input_data={
                    "bim_material": bim_material,
                    "epd_products": epd_products
                },
                workflow_state=workflow_state
            )
            
            if not step4_result["success"]:
                return self._create_error_response(
                    "Step 4 failed: Similarity evaluation failed",
                    workflow_state
                )
            
            evaluations = step4_result["data"]["evaluations"]
            
            # ================================================================
            # STEP 5: RANKING AND FILTERING
            # ================================================================
            step5_result = await self._execute_step(
                step_number=5,
                step_name="Ranking and Filtering",
                agent=self.ranking_agent,
                input_data={
                    "evaluations": evaluations,
                    "concept_mappings": concept_mappings.get("mappings", []),
                    "top_n": top_n,
                    "min_confidence": min_confidence
                },
                workflow_state=workflow_state
            )
            
            if not step5_result["success"]:
                return self._create_error_response(
                    "Step 5 failed: Ranking failed",
                    workflow_state
                )
            
            ranked_matches = step5_result["data"]["ranked_matches"]
            
            # ================================================================
            # STEP 6 (OPTIONAL): DETAILED INFORMATION
            # ================================================================
            if self.include_detailed_info and ranked_matches:
                step6_result = await self._execute_step(
                    step_number=6,
                    step_name="Detailed Information",
                    agent=self.detailed_info_agent,
                    input_data={
                        "ranked_matches": ranked_matches,
                        "max_details": min(5, len(ranked_matches))
                    },
                    workflow_state=workflow_state
                )
                
                if step6_result["success"]:
                    ranked_matches = step6_result["data"]["enhanced_matches"]
            
            # ================================================================
            # COMPLETE WORKFLOW
            # ================================================================
            execution_time = time.time() - start_time
            
            logger.info("=" * 80)
            logger.info(f"Workflow completed successfully in {execution_time:.2f}s")
            logger.info(f"Found {len(ranked_matches)} matches")
            logger.info("=" * 80)
            
            return {
                "success": True,
                "bim_material": bim_material,
                "concept_mappings": concept_mappings.get("mappings", []),
                "matches": ranked_matches,
                "workflow_steps": workflow_state["steps"],
                "total_candidates": len(epd_products),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
            return self._create_error_response(str(e), workflow_state)
    
    async def _execute_step(
        self,
        step_number: int,
        step_name: str,
        agent: Any,
        input_data: Dict[str, Any],
        workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single workflow step with progress tracking
        
        Args:
            step_number: Step number (1-6)
            step_name: Human-readable step name
            agent: Agent to execute
            input_data: Input data for the agent
            workflow_state: Workflow state for tracking
            
        Returns:
            Step execution result
        """
        logger.info(f"\n{'─'*80}")
        logger.info(f"STEP {step_number}: {step_name}")
        logger.info(f"{'─'*80}")
        
        step_start = time.time()
        
        # Record step start
        step_info = {
            "step_number": step_number,
            "step_name": step_name,
            "status": WorkflowStatus.IN_PROGRESS,
            "started_at": datetime.now().isoformat()
        }
        
        workflow_state["steps"].append(step_info)
        
        try:
            # Execute agent
            result = await agent.execute(input_data)
            
            # Update step info
            step_info["status"] = (
                WorkflowStatus.COMPLETED if result.get("success")
                else WorkflowStatus.FAILED
            )
            step_info["completed_at"] = datetime.now().isoformat()
            step_info["execution_time"] = time.time() - step_start
            
            if not result.get("success"):
                step_info["error"] = result.get("error")
                logger.error(f"Step {step_number} failed: {result.get('error')}")
            else:
                logger.info(f"Step {step_number} completed in {step_info['execution_time']:.2f}s")
            
            return result
            
        except Exception as e:
            # Update step info with error
            step_info["status"] = WorkflowStatus.FAILED
            step_info["completed_at"] = datetime.now().isoformat()
            step_info["execution_time"] = time.time() - step_start
            step_info["error"] = str(e)
            
            logger.error(f"Step {step_number} exception: {e}", exc_info=True)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_error_response(
        self,
        error_message: str,
        workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create error response"""
        return {
            "success": False,
            "error": error_message,
            "workflow_steps": workflow_state.get("steps", []),
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_empty_response(
        self,
        message: str,
        workflow_state: Dict[str, Any],
        bim_material: Dict[str, Any],
        concept_mappings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create empty response when no matches found"""
        return {
            "success": True,
            "message": message,
            "bim_material": bim_material,
            "concept_mappings": concept_mappings.get("mappings", []),
            "matches": [],
            "workflow_steps": workflow_state.get("steps", []),
            "total_candidates": 0,
            "timestamp": datetime.now().isoformat()
        }
