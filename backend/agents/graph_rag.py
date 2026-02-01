"""
Graph RAG Agent Module
Creates standalone agents for querying individual ontologies

This module implements direct Graph RAG queries for BIMTool, EPD, and Thesaurus
ontologies. Unlike the cross-matching orchestrator which coordinates 5 specialized
agents, these agents directly query a single ontology for exploration and discovery.

Features:
- BIMTool ontology queries (361 building materials)
- EPD ontology queries (50+ environmental product declarations)
- Thesaurus queries (SKOS concept mappings)
- LLM-powered SPARQL generation
- Natural language response formatting
- Support for both OpenAI and Anthropic

Architecture:
- Uses existing LLM client infrastructure
- Leverages existing SPARQL client with fallback
- Follows same patterns as specialized agents
- Fully async for performance
"""
import logging
import time
from typing import Dict, Any, Optional
from llm import create_llm_client, BaseLLMClient
from sparql.client import SPARQLClientFactory, SPARQLClient
from core.config import settings

logger = logging.getLogger(__name__)


class GraphRAGAgent:
    """
    Standalone Graph RAG agent for direct ontology queries
    
    Unlike the cross-matching orchestrator which coordinates 5 specialized agents,
    this agent directly queries a single ontology (BIMTool, EPD, or Thesaurus).
    
    The agent uses a two-step process:
    1. LLM generates SPARQL query from natural language
    2. LLM formats SPARQL results into natural language answer
    """
    
    def __init__(
        self,
        ontology: str,  # 'bimtool', 'epd', or 'thesaurus'
        llm_provider: str = "openai"
    ):
        """
        Initialize Graph RAG agent for specific ontology
        
        Args:
            ontology: Target ontology name ('bimtool', 'epd', or 'thesaurus')
            llm_provider: LLM provider to use ('openai' or 'anthropic')
            
        Raises:
            ValueError: If ontology is not supported
        """
        if ontology not in ['bimtool', 'epd', 'thesaurus']:
            raise ValueError(f"Unknown ontology: {ontology}. Must be 'bimtool', 'epd', or 'thesaurus'")
        
        self.ontology = ontology
        self.llm_provider = llm_provider
        
        logger.info(f"Initializing Graph RAG agent for '{ontology}' ontology with {llm_provider}")
        
        # Create LLM client
        self.llm_client: BaseLLMClient = create_llm_client(llm_provider)
        
        # Create SPARQL client for target ontology
        self.sparql_client: SPARQLClient = self._create_sparql_client(ontology)
        
        # Get ontology-specific system prompts
        self.query_generation_prompt = self._get_query_generation_prompt(ontology)
        self.answer_formatting_prompt = self._get_answer_formatting_prompt(ontology)
        
        # Get namespace prefixes for this ontology
        self.namespace_prefixes = self._get_namespace_prefixes(ontology)
        
        logger.info(f"✓ Graph RAG agent ready for {ontology} ontology")
    
    def _create_sparql_client(self, ontology: str) -> SPARQLClient:
        """Create SPARQL client for specific ontology"""
        if ontology == "bimtool":
            return SPARQLClientFactory.create_bimtool_client()
        elif ontology == "epd":
            return SPARQLClientFactory.create_epd_client()
        elif ontology == "thesaurus":
            return SPARQLClientFactory.create_thesaurus_client()
        else:
            raise ValueError(f"Unknown ontology: {ontology}")
    
    def _get_namespace_prefixes(self, ontology: str) -> str:
        """Get SPARQL namespace prefixes for ontology"""
        
        if ontology == "bimtool":
            return """PREFIX btml: <http://www.BimToolsMaterialLibrary.com/BimBuildingMaterialsOntology#>
PREFIX dcm: <https://w3id.org/digitalconstruction/0.3/BuildingMaterials#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX qudt: <http://qudt.org/schema/qudt/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>"""
        
        elif ontology == "epd":
            return """PREFIX epd: <http://www.EpdLcaOntology.com/EpdLcaDataSetOntology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>"""
        
        elif ontology == "thesaurus":
            return """PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX bimtooltax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#>
PREFIX epdtax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#>
PREFIX berrtax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/berr#>
PREFIX dcmtax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/dcm#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>"""
        
        else:
            return ""
    
    def _get_query_generation_prompt(self, ontology: str) -> str:
        """Get system prompt for SPARQL query generation"""
        
        if ontology == "bimtool":
            return """You are a BIM Materials SPARQL expert. Generate accurate SPARQL queries for the BIM Tool Materials Library.

ONTOLOGY STRUCTURE:
- Root class: dcm:BuildingMaterial
- Properties: btml:hasMaterialProperty → btml:GeneralInformation, btml:Mechanical, etc.
- Material name: btml:MaterialName
- Categories: btml:hasPrimaryCategory, btml:hasSecondaryCategory
- Category labels: rdfs:label

REQUIRED PREFIXES (Always include these):
PREFIX btml: <http://www.BimToolsMaterialLibrary.com/BimBuildingMaterialsOntology#>
PREFIX dcm: <https://w3id.org/digitalconstruction/0.3/BuildingMaterials#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

QUERY PATTERNS:
1. List materials:
   SELECT ?material ?name WHERE {
     ?material a dcm:BuildingMaterial ;
              btml:hasMaterialProperty ?genInfo .
     ?genInfo a btml:GeneralInformation ;
             btml:MaterialName ?name .
   }

2. Search by name:
   FILTER(CONTAINS(LCASE(?name), LCASE("search_term")))

3. Filter by category:
   ?material btml:hasPrimaryCategory ?category .
   ?category rdfs:label ?categoryLabel .
   FILTER(?categoryLabel = "Concrete")

DATABASE STATS:
- 361 total materials
- Safe limits: Use LIMIT 10-20 for list queries
- All queries run FAST (<2 seconds)

CRITICAL RULES:
1. ALWAYS use both dcm: and btml: prefixes
2. Root class is dcm:BuildingMaterial (NOT btml:BuildingMaterial)
3. Include LIMIT clause (typically 10-20)
4. Use CONTAINS(LCASE()) for case-insensitive search
5. Return only valid SPARQL, no explanations"""

        elif ontology == "epd":
            return """You are an EPD Products SPARQL expert. Generate accurate SPARQL queries for Environmental Product Declarations.

ONTOLOGY STRUCTURE:
- Root class: epd:ProcessDataSet
- Property path: hasProcessInformation → hasKeyDataSetInformation
- Product name: epd:Name
- Category: hasClassificationOrCategory → epd:ProductTypeCategory

REQUIRED PREFIXES (Always include these):
PREFIX epd: <http://www.EpdLcaOntology.com/EpdLcaDataSetOntology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

QUERY PATTERNS:
1. List products:
   SELECT ?product ?name ?category WHERE {
     ?product a epd:ProcessDataSet ;
             epd:hasProcessInformation ?procInfo .
     ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
     ?keyInfo epd:Name ?name ;
             epd:hasClassificationOrCategory ?classif .
     ?classif epd:ProductTypeCategory ?category .
   }

2. Search by category:
   FILTER(CONTAINS(LCASE(?category), LCASE("search_term")))

DATABASE STATS:
- ~50 EPD products
- ~32 environmental indicators per product
- ~10 life cycle phases per product

CRITICAL RULES - MEMORY SAFETY:
1. ALWAYS use LIMIT (max 50 for products)
2. NEVER query environmental indicators for 50+ products directly
3. Use subqueries with LIMIT when querying indicator values
4. Prefer product-level queries over detailed environmental data
5. Return only valid SPARQL, no explanations"""

        elif ontology == "thesaurus":
            return """You are a Thesaurus SPARQL expert. Generate accurate SPARQL queries for SKOS concept mappings.

ONTOLOGY STRUCTURE:
- Concepts: skos:Concept
- Labels: skos:prefLabel (multilingual)
- Mappings: skos:exactMatch, skos:closeMatch, skos:broadMatch, skos:narrowMatch
- Taxonomies: bimtooltax, epdtax, berrtax, dcmtax

REQUIRED PREFIXES (Always include these):
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX bimtooltax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#>
PREFIX epdtax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#>

QUERY PATTERNS:
1. Find exact matches:
   SELECT ?bim_concept ?epd_concept WHERE {
     ?bim_concept skos:exactMatch ?epd_concept .
     ?bim_concept skos:prefLabel ?bim_label .
     FILTER(LANG(?bim_label) = "en")
   }

2. Count mappings:
   SELECT (COUNT(*) as ?count) WHERE {
     ?concept1 skos:exactMatch ?concept2 .
   }

MAPPING TYPES:
- exactMatch: Confidence 1.0 (identical concepts)
- closeMatch: Confidence 0.8 (very similar)
- broadMatch: General → specific
- narrowMatch: Specific → general

CRITICAL RULES:
1. ALWAYS filter labels by language: FILTER(LANG(?label) = "en")
2. Use FILTER to ensure concepts from different taxonomies
3. Include confidence/match type in results
4. Use LIMIT for large result sets
5. Return only valid SPARQL, no explanations"""

        else:
            return "You are a SPARQL expert. Generate accurate SPARQL queries."
    
    def _get_answer_formatting_prompt(self, ontology: str) -> str:
        """Get system prompt for answer formatting"""
        
        if ontology == "bimtool":
            return """You are a BIM Materials assistant. Format SPARQL query results into clear, concise natural language answers.

FORMATTING GUIDELINES:
1. Answer the user's question directly
2. For counts: State the number clearly
3. For lists: Show top 5-10 results, mention total if more
4. For specific materials: Provide key details (name, category, properties)
5. Keep answers concise and focused
6. Use proper terminology (materials, categories, properties)

Do not explain SPARQL queries or technical details unless asked."""

        elif ontology == "epd":
            return """You are an EPD Products assistant. Format SPARQL query results into clear, concise natural language answers.

FORMATTING GUIDELINES:
1. Answer the user's question directly
2. For counts: State the number clearly
3. For products: Include name and category
4. For environmental data: Present values with units
5. Keep answers concise and data-focused
6. Use proper LCA terminology

Do not explain SPARQL queries or technical details unless asked."""

        elif ontology == "thesaurus":
            return """You are a Thesaurus assistant. Format SPARQL query results into clear, concise natural language answers.

FORMATTING GUIDELINES:
1. Answer the user's question directly
2. For mappings: Show concept relationships clearly
3. Indicate match type (exact, close, broad, narrow)
4. Explain semantic relationships when relevant
5. Keep answers concise and clear
6. Use proper semantic web terminology

Do not explain SPARQL queries or technical details unless asked."""

        else:
            return "You are an assistant. Format results into clear natural language."
    
    async def query(self, user_query: str) -> Dict[str, Any]:
        """
        Execute Graph RAG query
        
        Two-step process:
        1. LLM generates SPARQL query from natural language
        2. Execute SPARQL query against knowledge graph
        3. LLM formats results into natural language answer
        
        Args:
            user_query: User's natural language query
            
        Returns:
            Dict containing:
            - query: Original user query
            - ontology: Target ontology
            - answer: Natural language answer
            - sparql_query: Generated SPARQL query
            - results_count: Number of results
            - execution_time: Total time in seconds
            - success: Whether query succeeded
        """
        logger.info(f"Processing query for {self.ontology}: {user_query[:100]}...")
        
        start_time = time.time()
        
        try:
            # Step 1: Generate SPARQL query
            logger.debug("Step 1: Generating SPARQL query...")
            sparql_query = await self._generate_sparql_query(user_query)
            logger.debug(f"Generated SPARQL:\n{sparql_query}")
            
            # Step 2: Execute SPARQL query
            logger.debug("Step 2: Executing SPARQL query...")
            results = await self.sparql_client.query(sparql_query)
            results_count = len(results.get("results", {}).get("bindings", []))
            logger.info(f"Query returned {results_count} results")
            
            # Step 3: Format results into natural language answer
            logger.debug("Step 3: Formatting answer...")
            answer = await self._format_answer(user_query, results, sparql_query)
            
            execution_time = time.time() - start_time
            logger.info(f"Query completed in {execution_time:.2f}s")
            
            return {
                "query": user_query,
                "ontology": self.ontology,
                "answer": answer,
                "sparql_query": sparql_query,
                "results_count": results_count,
                "execution_time": execution_time,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Graph RAG query failed: {e}", exc_info=True)
            execution_time = time.time() - start_time
            
            return {
                "query": user_query,
                "ontology": self.ontology,
                "answer": f"I encountered an error processing your query: {str(e)}",
                "error": str(e),
                "execution_time": execution_time,
                "success": False
            }
    
    async def _generate_sparql_query(self, user_query: str) -> str:
        """
        Use LLM to generate SPARQL query from natural language
        
        Args:
            user_query: User's natural language query
            
        Returns:
            SPARQL query string
        """
        prompt = f"""Given the user query: "{user_query}"

Generate an appropriate SPARQL query for the {self.ontology} ontology.

Requirements:
1. Include all required namespace prefixes
2. Follow the query patterns for this ontology
3. Include appropriate LIMIT clause
4. Use proper filtering for search queries
5. Return ONLY the SPARQL query, no explanations or markdown

SPARQL Query:"""

        # Call LLM
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm_client.complete(
            messages=messages,
            system_prompt=self.query_generation_prompt,
            temperature=0.0,
            max_tokens=1000
        )
        
        sparql_query = response.strip()
        
        # Clean up markdown code blocks if present
        if "```sparql" in sparql_query:
            sparql_query = sparql_query.split("```sparql")[1].split("```")[0].strip()
        elif "```" in sparql_query:
            # Remove any code block markers
            sparql_query = sparql_query.replace("```", "").strip()
        
        # Ensure prefixes are included
        if "PREFIX" not in sparql_query:
            sparql_query = self.namespace_prefixes + "\n\n" + sparql_query
        
        return sparql_query
    
    async def _format_answer(
        self, 
        user_query: str, 
        results: Dict[str, Any],
        sparql_query: str
    ) -> str:
        """
        Use LLM to generate natural language answer from SPARQL results
        
        Args:
            user_query: Original user query
            results: SPARQL query results
            sparql_query: The SPARQL query that was executed
            
        Returns:
            Natural language answer
        """
        bindings = results.get("results", {}).get("bindings", [])
        
        if not bindings:
            return f"No results found for your query about {self.ontology}."
        
        # Format results for LLM
        results_count = len(bindings)
        
        # Show first 10 results in detail
        results_summary = f"Query returned {results_count} results:\n\n"
        for i, binding in enumerate(bindings[:10], 1):
            row = {var: val.get("value") for var, val in binding.items()}
            # Format each row nicely
            row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
            results_summary += f"{i}. {row_str}\n"
        
        if results_count > 10:
            results_summary += f"\n... and {results_count - 10} more results"
        
        prompt = f"""User asked: "{user_query}"

Query results:
{results_summary}

Provide a clear, concise answer to the user's question based on these results.
Focus on directly answering what they asked.

Answer:"""

        messages = [
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm_client.complete(
            messages=messages,
            system_prompt=self.answer_formatting_prompt,
            temperature=0.0,
            max_tokens=1000
        )
        
        return response.strip()