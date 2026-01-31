"""
Base Agent Module
Abstract base class for all specialized agents in the workflow

Provides common functionality:
- SPARQL query execution
- LLM interpretation
- Error handling
- Logging
"""
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from llm.base import BaseLLMClient
from sparql.client import SPARQLClient

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all workflow agents
    
    Each agent performs a specialized task:
    1. Queries knowledge graphs via SPARQL
    2. Uses LLM to interpret and process results
    3. Returns structured data for next agent
    
    All agents follow the same pattern but with different
    SPARQL queries and prompts.
    """
    
    def __init__(
        self, 
        llm_client: BaseLLMClient, 
        sparql_client: SPARQLClient,
        agent_name: Optional[str] = None
    ):
        """
        Initialize base agent
        
        Args:
            llm_client: Language model client
            sparql_client: SPARQL query client
            agent_name: Optional name for logging (defaults to class name)
        """
        self.llm = llm_client
        self.sparql = sparql_client
        self.agent_name = agent_name or self.__class__.__name__
        self.logger = logging.getLogger(self.agent_name)
        
        self.logger.info(
            f"Initialized {self.agent_name} with "
            f"LLM={llm_client.get_provider_name()}, "
            f"Model={llm_client.get_model_name()}"
        )
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic (must be implemented by subclasses)
        
        Args:
            input_data: Input data from previous agent or user
            
        Returns:
            Result dictionary for next agent
            
        Raises:
            Exception: If execution fails
        """
        pass
    
    async def query_knowledge_graph(
        self, 
        sparql_query: str
    ) -> List[Dict[str, str]]:
        """
        Execute SPARQL query and parse results
        
        Helper method that wraps SPARQL client and provides
        error handling and logging.
        
        Args:
            sparql_query: SPARQL query string
            
        Returns:
            List of result dictionaries
            
        Raises:
            Exception: If query fails
        """
        try:
            self.logger.debug(f"Executing SPARQL query: {sparql_query[:100]}...")
            
            # Execute query
            results = await self.sparql.query(sparql_query)
            
            # Parse results
            parsed = self.sparql.parse_results(results)
            
            self.logger.info(f"SPARQL query returned {len(parsed)} results")
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"SPARQL query failed: {e}", exc_info=True)
            raise Exception(f"Knowledge graph query failed: {str(e)}")
    
    async def llm_interpret(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.0,
        parse_json: bool = False
    ) -> Any:
        """
        Use LLM to interpret data and generate structured output
        
        Args:
            prompt: User prompt with data to interpret
            system_prompt: System prompt defining task
            temperature: Sampling temperature (0.0 = deterministic)
            parse_json: Whether to parse response as JSON
            
        Returns:
            LLM response (string or parsed JSON)
            
        Raises:
            Exception: If LLM call or JSON parsing fails
        """
        try:
            self.logger.debug("Requesting LLM interpretation")
            
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Call LLM
            response = await self.llm.complete(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature
            )
            
            self.logger.info(f"LLM generated {len(response)} characters")
            
            # Parse JSON if requested
            if parse_json:
                try:
                    # Try to extract JSON from markdown code blocks
                    if "```json" in response:
                        json_start = response.find("```json") + 7
                        json_end = response.find("```", json_start)
                        json_str = response[json_start:json_end].strip()
                    elif "```" in response:
                        json_start = response.find("```") + 3
                        json_end = response.find("```", json_start)
                        json_str = response[json_start:json_end].strip()
                    else:
                        json_str = response.strip()
                    
                    # Parse JSON
                    parsed = json.loads(json_str)
                    self.logger.debug("Successfully parsed JSON response")
                    return parsed
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON: {e}")
                    self.logger.debug(f"Response was: {response}")
                    raise Exception(f"LLM returned invalid JSON: {str(e)}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"LLM interpretation failed: {e}", exc_info=True)
            raise Exception(f"LLM interpretation failed: {str(e)}")
    
    def format_query_results(
        self, 
        results: List[Dict[str, str]],
        max_results: int = 50
    ) -> str:
        """
        Format SPARQL results for LLM consumption
        
        Converts list of dictionaries to readable text format
        that LLMs can easily process.
        
        Args:
            results: Parsed SPARQL results
            max_results: Maximum number of results to include
            
        Returns:
            Formatted string representation
        """
        if not results:
            return "No results found."
        
        # Limit results to avoid token limits
        results = results[:max_results]
        
        formatted_lines = []
        for i, result in enumerate(results, 1):
            formatted_lines.append(f"Result {i}:")
            for key, value in result.items():
                formatted_lines.append(f"  {key}: {value}")
            formatted_lines.append("")  # Blank line between results
        
        return "\n".join(formatted_lines)
    
    def validate_input(
        self, 
        input_data: Dict[str, Any], 
        required_fields: List[str]
    ) -> None:
        """
        Validate that input contains required fields
        
        Args:
            input_data: Input dictionary to validate
            required_fields: List of required field names
            
        Raises:
            ValueError: If required field is missing
        """
        for field in required_fields:
            if field not in input_data:
                raise ValueError(f"Missing required input field: {field}")
            
            value = input_data[field]
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"Required field '{field}' is empty")
        
        self.logger.debug(f"Input validation passed for fields: {required_fields}")
    
    def create_result(
        self, 
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create standardized result dictionary
        
        Args:
            success: Whether execution was successful
            data: Result data (if successful)
            error: Error message (if failed)
            
        Returns:
            Standardized result dictionary
        """
        result = {
            "agent": self.agent_name,
            "success": success
        }
        
        if success and data:
            result["data"] = data
        
        if not success and error:
            result["error"] = error
        
        return result
    
    async def execute_with_retry(
        self,
        input_data: Dict[str, Any],
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Execute agent with automatic retry on failure
        
        Args:
            input_data: Input data
            max_retries: Maximum number of retry attempts
            
        Returns:
            Execution result
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(
                    f"Executing {self.agent_name} (attempt {attempt + 1}/{max_retries + 1})"
                )
                
                result = await self.execute(input_data)
                
                self.logger.info(f"{self.agent_name} execution successful")
                return result
                
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {e}"
                )
                
                if attempt < max_retries:
                    self.logger.info("Retrying...")
        
        # All retries failed
        error_msg = f"{self.agent_name} failed after {max_retries + 1} attempts: {last_error}"
        self.logger.error(error_msg)
        raise Exception(error_msg)