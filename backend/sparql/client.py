"""
SPARQL HTTP Client for GraphDB/Fuseki
"""
import logging
import aiohttp
from typing import Dict, Any, Optional
from core.config import settings

logger = logging.getLogger(__name__)


class SPARQLClient:
    """Asynchronous SPARQL client"""
    
    def __init__(self, repository: str):
        self.endpoint = settings.get_sparql_endpoint(repository)
        self.timeout = settings.graphdb_timeout
        
    async def query(self, sparql_query: str) -> Dict[str, Any]:
        """
        Execute SPARQL SELECT query
        
        Args:
            sparql_query: SPARQL query string
            
        Returns:
            Query results as dictionary
        """
        logger.debug(f"Executing SPARQL query on {self.endpoint}")
        logger.debug(f"Query: {sparql_query[:200]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    data={"query": sparql_query},
                    headers={"Accept": "application/sparql-results+json"},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    logger.debug(f"Query returned {len(result.get('results', {}).get('bindings', []))} results")
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"SPARQL query failed: {e}")
            raise Exception(f"SPARQL query failed: {e}")
    
    def parse_results(self, results: Dict[str, Any]) -> list:
        """Parse SPARQL JSON results into list of dictionaries"""
        bindings = results.get("results", {}).get("bindings", [])
        
        parsed = []
        for binding in bindings:
            row = {}
            for var, value in binding.items():
                row[var] = value.get("value")
            parsed.append(row)
        
        return parsed


class SPARQLClientFactory:
    """Factory for creating repository-specific SPARQL clients"""
    
    @staticmethod
    def create_bimtool_client() -> SPARQLClient:
        return SPARQLClient(settings.graphdb_repository_bimtool)
    
    @staticmethod
    def create_epd_client() -> SPARQLClient:
        return SPARQLClient(settings.graphdb_repository_epd)
    
    @staticmethod
    def create_thesaurus_client() -> SPARQLClient:
        return SPARQLClient(settings.graphdb_repository_thesaurus)