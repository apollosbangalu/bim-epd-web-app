"""
EPD SPARQL Queries Module
Pre-built SPARQL query templates for EPD (Environmental Product Declaration) ontology

CRITICAL FEATURES:
- Memory-safe patterns (LIMIT on products with environmental data)
- Correct property paths (ProcessDataSet → hasProcessInformation → hasKeyDataSetInformation)
- Proper property names from actual EPD ontology
- Efficient queries for ~50 products with deep structure

Based on EPD ILCD knowledge graph (~50 products, 32 indicators, 10 phases each)
"""
from typing import List, Optional


# Namespace prefixes for EPD ontology
EPD_PREFIXES = """
PREFIX epd: <http://www.EpdLcaOntology.com/EpdLcaDataSetOntology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""


def build_epd_products_by_category_query(
    category_keywords: List[str],
    max_products: int = 50
) -> str:
    """
    Build query to find EPD products by ProductTypeCategory
    
    CORRECTED VERSION with:
    - Proper property path: hasProcessInformation → hasKeyDataSetInformation
    - Correct property names from EPD ontology
    - No hardcoded LIMIT - uses parameter
    
    Args:
        category_keywords: List of keywords to search in ProductTypeCategory
        max_products: Maximum number of products to return (default 50, max 50)
        
    Returns:
        SPARQL query string
    """
    # Build filter conditions for multiple keywords (OR logic)
    filter_conditions = " || ".join([
        f'CONTAINS(LCASE(?productTypeCategory), "{keyword.lower()}")'
        for keyword in category_keywords
    ])
    
    query = f"""{EPD_PREFIXES}

SELECT DISTINCT
    ?product
    ?name
    ?nameDetail
    ?productTypeCategory
    ?technicalPurpose
    ?technologyDescription
    ?location
WHERE {{
    # Step 1: Get ProcessInformation
    ?product a epd:ProcessDataSet ;
             epd:hasProcessInformation ?procInfo .
    
    # Step 2: Get KeyDataSetInformation
    ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
    
    # Required field
    ?keyInfo epd:Name ?name .
    
    # Step 3: Get Classification
    ?keyInfo epd:hasClassificationOrCategory ?classif .
    ?classif epd:ProductTypeCategory ?productTypeCategory .
    
    # Filter by category keywords
    FILTER({filter_conditions})
    
    # Optional fields
    OPTIONAL {{ ?keyInfo epd:NameDetail ?nameDetail . }}
    
    # Get technical information
    OPTIONAL {{
        ?procInfo epd:hasTechnologicalRepresentativeness ?techRep .
        ?techRep epd:TechnicalPurposeOfProductOrProcess ?technicalPurpose .
    }}
    
    OPTIONAL {{
        ?procInfo epd:hasTechnologicalRepresentativeness ?techRep2 .
        ?techRep2 epd:TechnologyDescriptionIncludingBackgroundSystem ?technologyDescription .
    }}
    
    # Get location
    OPTIONAL {{
        ?procInfo epd:hasLocation ?location .
    }}
}}
LIMIT {min(max_products, 50)}
"""
    return query


def build_epd_product_details_query(product_uris: List[str]) -> str:
    """
    Build query to fetch comprehensive details for specific EPD products
    
    Fetches two critical URIs:
    1. ProcessDataSet URI (graph identifier)
    2. Uri property (web link to EPD online)
    
    Plus all product details and total GWP.
    
    Args:
        product_uris: List of product URIs (max 10 for performance)
        
    Returns:
        SPARQL query string
    """
    # Format URIs for VALUES clause
    uri_values = " ".join([f"<{uri}>" for uri in product_uris[:10]])
    
    query = f"""{EPD_PREFIXES}

SELECT
    ?product
    ?name
    ?nameDetail
    ?productTypeCategory
    ?webLink
    ?technicalPurpose
    ?technologyDescription
    ?location
    (SUM(?gwpValue) AS ?totalGWP)
WHERE {{
    # Bind specific products (up to 10)
    VALUES ?product {{ {uri_values} }}
    
    ?product epd:hasProcessInformation ?procInfo .
    ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
    
    # Required fields
    ?keyInfo epd:Name ?name .
    
    # CRITICAL: Web link from KeyDataSetInformation (Uri property)
    OPTIONAL {{ ?keyInfo epd:Uri ?webLink }}
    
    # Classification
    OPTIONAL {{
        ?keyInfo epd:NameDetail ?nameDetail ;
                 epd:hasClassificationOrCategory ?classif .
        ?classif epd:ProductTypeCategory ?productTypeCategory .
    }}
    
    # Technical information
    OPTIONAL {{
        ?procInfo epd:hasTechnologicalRepresentativeness ?techRep .
        ?techRep epd:TechnicalPurposeOfProductOrProcess ?technicalPurpose ;
                 epd:TechnologyDescriptionIncludingBackgroundSystem ?technologyDescription .
    }}
    
    # Location
    OPTIONAL {{ ?procInfo epd:hasLocation ?location . }}
    
    # Total GWP (Global Warming Potential)
    OPTIONAL {{
        ?product epd:hasEnvironmentalIndicator ?envInd .
        ?envInd epd:hasEnvironmentalImpactIndicators ?impactInd .
        ?impactInd epd:hasPhaseValue ?phaseValue .
        ?phaseValue epd:hasIndicator ?indicator .
        
        # Filter for GWP-Total indicator
        ?indicator rdfs:label ?indicatorLabel .
        FILTER(CONTAINS(LCASE(?indicatorLabel), "gwp-total"))
        
        ?phaseValue epd:Value ?gwpValue .
    }}
}}
GROUP BY ?product ?name ?nameDetail ?productTypeCategory ?webLink 
         ?technicalPurpose ?technologyDescription ?location
"""
    return query


def build_epd_environmental_indicators_query(
    product_uri: str,
    indicator_name: Optional[str] = None
) -> str:
    """
    Build MEMORY-SAFE query for environmental indicators
    
    CRITICAL: This query uses subquery with LIMIT to prevent memory issues.
    EPD knowledge graph has deep structure (4-6 levels) with 16,000+ data points.
    
    Args:
        product_uri: Single product URI
        indicator_name: Optional indicator filter (e.g., "GWP", "AP", "EP")
        
    Returns:
        SPARQL query string
    """
    indicator_filter = ""
    if indicator_name:
        indicator_filter = f'FILTER(CONTAINS(LCASE(?indicatorLabel), "{indicator_name.lower()}"))'
    
    query = f"""{EPD_PREFIXES}

SELECT
    ?product
    ?indicatorLabel
    ?phaseName
    ?phaseValue
WHERE {{
    # Bind single product
    BIND(<{product_uri}> AS ?product)
    
    # Get environmental indicators
    ?product epd:hasEnvironmentalIndicator ?envInd .
    ?envInd epd:hasEnvironmentalImpactIndicators ?impactInd .
    ?impactInd epd:hasPhaseValue ?phaseValueObj .
    
    # Get indicator information
    ?phaseValueObj epd:hasIndicator ?indicator .
    ?indicator rdfs:label ?indicatorLabel .
    
    {indicator_filter}
    
    # Get phase information
    ?phaseValueObj epd:hasPhase ?phase .
    ?phase rdfs:label ?phaseName .
    
    # Get value
    ?phaseValueObj epd:Value ?phaseValue .
}}
ORDER BY ?indicatorLabel ?phaseName
"""
    return query


def build_epd_products_with_gwp_query(
    max_products: int = 15
) -> str:
    """
    Build MEMORY-SAFE query to get products with total GWP
    
    CRITICAL: Uses subquery with LIMIT to prevent memory exhaustion.
    Without LIMIT, query can cause GraphDB to crash with 262MB memory limit.
    
    Args:
        max_products: Maximum products to include (default 15, max 20)
        
    Returns:
        SPARQL query string
    """
    query = f"""{EPD_PREFIXES}

SELECT
    ?product
    ?name
    ?productTypeCategory
    (SUM(?gwpValue) AS ?totalGWP)
WHERE {{
    # CRITICAL: Subquery with LIMIT for memory safety
    {{
        SELECT DISTINCT ?product WHERE {{
            ?product a epd:ProcessDataSet .
        }}
        LIMIT {min(max_products, 20)}
    }}
    
    # Get basic info
    ?product epd:hasProcessInformation ?procInfo .
    ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
    ?keyInfo epd:Name ?name .
    
    OPTIONAL {{
        ?keyInfo epd:hasClassificationOrCategory ?classif .
        ?classif epd:ProductTypeCategory ?productTypeCategory .
    }}
    
    # Get GWP values
    OPTIONAL {{
        ?product epd:hasEnvironmentalIndicator ?envInd .
        ?envInd epd:hasEnvironmentalImpactIndicators ?impactInd .
        ?impactInd epd:hasPhaseValue ?phaseValue .
        ?phaseValue epd:hasIndicator ?indicator .
        
        ?indicator rdfs:label ?indicatorLabel .
        FILTER(CONTAINS(LCASE(?indicatorLabel), "gwp-total"))
        
        ?phaseValue epd:Value ?gwpValue .
    }}
}}
GROUP BY ?product ?name ?productTypeCategory
ORDER BY ?totalGWP
"""
    return query


def build_epd_count_query(category_keyword: Optional[str] = None) -> str:
    """
    Build query to count EPD products
    
    Args:
        category_keyword: Optional category filter
        
    Returns:
        SPARQL query string
    """
    if category_keyword:
        query = f"""{EPD_PREFIXES}

SELECT (COUNT(DISTINCT ?product) AS ?count)
WHERE {{
    ?product a epd:ProcessDataSet ;
             epd:hasProcessInformation ?procInfo .
    
    ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
    ?keyInfo epd:hasClassificationOrCategory ?classif .
    ?classif epd:ProductTypeCategory ?category .
    
    FILTER(CONTAINS(LCASE(?category), "{category_keyword.lower()}"))
}}
"""
    else:
        query = f"""{EPD_PREFIXES}

SELECT (COUNT(DISTINCT ?product) AS ?count)
WHERE {{
    ?product a epd:ProcessDataSet .
}}
"""
    return query


def build_epd_categories_query() -> str:
    """
    Build query to get all unique product categories
    
    Returns:
        SPARQL query string
    """
    query = f"""{EPD_PREFIXES}

SELECT DISTINCT ?category
WHERE {{
    ?product a epd:ProcessDataSet ;
             epd:hasProcessInformation ?procInfo .
    
    ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
    ?keyInfo epd:hasClassificationOrCategory ?classif .
    ?classif epd:ProductTypeCategory ?category .
}}
ORDER BY ?category
"""
    return query


# Validation helpers
def validate_category_keywords(keywords: List[str]) -> bool:
    """
    Validate category keywords input
    
    Args:
        keywords: List of keywords to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not keywords or not isinstance(keywords, list):
        return False
    
    dangerous_chars = ["'", '"', "{", "}", "<", ">", ";"]
    for keyword in keywords:
        if not isinstance(keyword, str):
            return False
        for char in dangerous_chars:
            if char in keyword:
                return False
    
    return True


def validate_product_uri(uri: str) -> bool:
    """
    Validate EPD product URI
    
    Args:
        uri: Product URI to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not uri or not isinstance(uri, str):
        return False
    
    # Must be valid HTTP URI
    if not uri.startswith("http://") and not uri.startswith("https://"):
        return False
    
    return True