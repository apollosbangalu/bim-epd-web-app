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
            result = await self.bim_extractor.execute({
                "material_name": material_name
            })
            
            step_time = time.time() - step_start
            
            workflow_steps[-1].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "execution_time": step_time,
                "result_summary": f"Extracted {result.get('raw_data', {}).get('name', 'material')} with {len(result.get('raw_data', {}))} fields",
                "details": {
                    "material_name": result.get("raw_data", {}).get("name"),
                    "primary_category": result.get("raw_data", {}).get("primary_category_label"),
                    "fields_extracted": len(result.get("raw_data", {}))
                }
            })
            
            return {"success": True, "data": result}
            
        except Exception as e:
            workflow_steps[-1].update({
                "status": "failed",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
    
    # Implement similar methods for steps 2-5...
    # _execute_step_2, _execute_step_3, _execute_step_4, _execute_step_5
    
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