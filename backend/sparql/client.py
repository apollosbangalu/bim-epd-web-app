"""
SPARQL HTTP Client with Fuseki→GraphDB Automatic Fallback
"""
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from core.config import settings

logger = logging.getLogger(__name__)


class SPARQLClient:
    """
    Asynchronous SPARQL client with automatic fallback support
    
    Tries Fuseki first, falls back to GraphDB if Fuseki fails
    """
    
    def __init__(self, repository: str):
        """
        Initialize client with fallback endpoints
        
        Args:
            repository: Repository name (bimtool, epd, or thesaurus)
        """
        self.repository = repository
        self.endpoints = settings.get_sparql_endpoints(repository)
        self.timeout = settings.graphdb_timeout
        self.active_endpoint = None  # Track which endpoint is currently working
        
        logger.info(f"Initialized SPARQL client for '{repository}' with fallback support")
        logger.debug(f"Available endpoints: {list(self.endpoints.keys())}")
    
    async def query(self, sparql_query: str) -> Dict[str, Any]:
        """
        Execute SPARQL SELECT query with automatic fallback
        
        Tries endpoints in order: Fuseki → GraphDB
        
        Args:
            sparql_query: SPARQL query string
            
        Returns:
            Query results as dictionary
            
        Raises:
            Exception: If all endpoints fail
        """
        logger.debug(f"Executing SPARQL query: {sparql_query[:100]}...")
        
        # Try endpoints in priority order
        endpoint_order = ['fuseki', 'graphdb']
        errors = []
        
        for endpoint_type in endpoint_order:
            if endpoint_type not in self.endpoints:
                continue
                
            endpoint_config = self.endpoints[endpoint_type]
            if not endpoint_config['enabled']:
                continue
            
            endpoint_url = endpoint_config['url']
            
            try:
                logger.debug(f"Trying {endpoint_type.upper()} endpoint: {endpoint_url}")
                
                result = await self._execute_query(endpoint_url, sparql_query)
                
                # Success! Mark this endpoint as active
                if self.active_endpoint != endpoint_type:
                    logger.info(
                        f"✅ Successfully connected to {endpoint_type.upper()} "
                        f"for repository '{self.repository}'"
                    )
                    self.active_endpoint = endpoint_type
                
                return result
                
            except Exception as e:
                error_msg = f"{endpoint_type.upper()} failed: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                
                # If this was the active endpoint, clear it
                if self.active_endpoint == endpoint_type:
                    self.active_endpoint = None
                
                continue  # Try next endpoint
        
        # All endpoints failed
        error_summary = "; ".join(errors)
        logger.error(
            f"❌ All SPARQL endpoints failed for repository '{self.repository}': "
            f"{error_summary}"
        )
        raise Exception(
            f"SPARQL query failed on all endpoints for '{self.repository}'. "
            f"Errors: {error_summary}"
        )
    
    async def _execute_query(
        self, 
        endpoint_url: str, 
        sparql_query: str
    ) -> Dict[str, Any]:
        """
        Execute query on a specific endpoint
        
        Args:
            endpoint_url: Full SPARQL endpoint URL
            sparql_query: SPARQL query string
            
        Returns:
            Query results
            
        Raises:
            Exception: If query fails
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint_url,
                data={"query": sparql_query},
                headers={"Accept": "application/sparql-results+json"},
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                result_count = len(result.get('results', {}).get('bindings', []))
                logger.debug(f"Query returned {result_count} results")
                
                return result
    
    def parse_results(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Parse SPARQL JSON results into list of dictionaries"""
        bindings = results.get("results", {}).get("bindings", [])
        
        parsed = []
        for binding in bindings:
            row = {}
            for var, value in binding.items():
                row[var] = value.get("value")
            parsed.append(row)
        
        return parsed
    
    async def health_check(self) -> bool:
        """
        Check if at least one endpoint is accessible
        
        Returns:
            True if any endpoint responds, False otherwise
        """
        simple_query = "SELECT * WHERE { ?s ?p ?o } LIMIT 1"
        
        try:
            # Add timeout wrapper
            import asyncio
            
            # Try to execute query with 5-second timeout
            await asyncio.wait_for(
                self.query(simple_query),
                timeout=5.0  # 5 seconds max
            )
            return True
            
        except asyncio.TimeoutError:
            logger.error(
                f"Health check timed out for '{self.repository}' "
                f"(no response after 5 seconds)"
            )
            return False
            
        except Exception as e:
            logger.error(f"Health check failed for '{self.repository}': {e}")
            return False
    
    def get_active_endpoint(self) -> Optional[str]:
        """
        Get the currently active endpoint type
        
        Returns:
            'fuseki', 'graphdb', or None if no endpoint is active
        """
        return self.active_endpoint


class SPARQLClientFactory:
    """Factory for creating repository-specific SPARQL clients"""
    
    @staticmethod
    def create_bimtool_client() -> SPARQLClient:
        return SPARQLClient("bimtool")
    
    @staticmethod
    def create_epd_client() -> SPARQLClient:
        return SPARQLClient("epd")
    
    @staticmethod
    def create_thesaurus_client() -> SPARQLClient:
        return SPARQLClient("thesaurus")
    
    @staticmethod
    async def health_check_all() -> Dict[str, bool]:
        """
        Check health of all repositories
        
        Returns:
            Dict mapping repository names to health status
        """
        bim_client = SPARQLClientFactory.create_bimtool_client()
        epd_client = SPARQLClientFactory.create_epd_client()
        thesaurus_client = SPARQLClientFactory.create_thesaurus_client()
        
        return {
            "bimtool": await bim_client.health_check(),
            "epd": await epd_client.health_check(),
            "thesaurus": await thesaurus_client.health_check()
        }