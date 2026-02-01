"""
EPD SPARQL Queries Module - CORRECTED VERSION
Pre-built SPARQL query templates for EPD (Environmental Product Declaration) ontology

CRITICAL FIXES:
1. Correct namespace URI from original Python app
2. Correct property paths: ProcessDataSet → hasProcessInformation → hasKeyDataSetInformation
3. Memory-safe patterns with LIMIT clauses
4. Proper property names from actual EPD ontology

Based on EPD ILCD knowledge graph (~50 products, 32 indicators, 10 phases each)
"""
from typing import List, Optional


# Namespace prefixes for EPD ontology - CORRECTED NAMESPACE
EPD_PREFIXES = """
PREFIX epd: <http://www.EpdLcaOntology.com/EpdLcaDataSetOntology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
    - Configurable LIMIT for memory safety
    
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
LIMIT {max_products}
"""
    return query


def build_epd_product_details_query(product_uri: str) -> str:
    """
    Build query to get detailed information for a specific EPD product
    
    Args:
        product_uri: Full URI of the EPD product
        
    Returns:
        SPARQL query string
    """
    query = f"""{EPD_PREFIXES}

SELECT DISTINCT
    ?name
    ?nameDetail
    ?productTypeCategory
    ?technicalPurpose
    ?technologyDescription
    ?functionalUnit
    ?referenceFlowName
    ?location
WHERE {{
    <{product_uri}> a epd:ProcessDataSet ;
                    epd:hasProcessInformation ?procInfo .
    
    ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
    ?keyInfo epd:Name ?name .
    
    # Optional fields
    OPTIONAL {{ ?keyInfo epd:NameDetail ?nameDetail . }}
    
    # Classification
    OPTIONAL {{
        ?keyInfo epd:hasClassificationOrCategory ?classif .
        ?classif epd:ProductTypeCategory ?productTypeCategory .
    }}
    
    # Technical info
    OPTIONAL {{
        ?procInfo epd:hasTechnologicalRepresentativeness ?techRep .
        ?techRep epd:TechnicalPurposeOfProductOrProcess ?technicalPurpose .
    }}
    
    OPTIONAL {{
        ?procInfo epd:hasTechnologicalRepresentativeness ?techRep2 .
        ?techRep2 epd:TechnologyDescriptionIncludingBackgroundSystem ?technologyDescription .
    }}
    
    # Functional unit
    OPTIONAL {{
        ?procInfo epd:hasQuantitativeReference ?quantRef .
        ?quantRef epd:FunctionalUnit ?functionalUnit .
    }}
    
    # Reference flow
    OPTIONAL {{
        ?procInfo epd:hasReferenceFlow ?refFlow .
        ?refFlow epd:Name ?referenceFlowName .
    }}
    
    # Location
    OPTIONAL {{ ?procInfo epd:hasLocation ?location . }}
}}
"""
    return query


def build_epd_environmental_indicators_query(
    product_uri: str,
    indicator_labels: Optional[List[str]] = None
) -> str:
    """
    Build query to get environmental indicators for an EPD product
    
    MEMORY-SAFE VERSION with optional indicator filtering
    
    Args:
        product_uri: Full URI of the EPD product
        indicator_labels: Optional list of specific indicator labels to retrieve
                         (e.g., ["GWP", "ODP", "AP"])
        
    Returns:
        SPARQL query string
    """
    # Build indicator filter if specified
    indicator_filter = ""
    if indicator_labels:
        labels_str = ", ".join([f'"{label}"' for label in indicator_labels])
        indicator_filter = f"FILTER(?indicatorLabel IN ({labels_str}))"
    
    query = f"""{EPD_PREFIXES}

SELECT DISTINCT
    ?indicatorLabel
    ?phase
    ?value
    ?unit
WHERE {{
    <{product_uri}> a epd:ProcessDataSet ;
                    epd:hasLCIAResult ?lciaResult .
    
    # Get indicator information
    ?lciaResult epd:hasIndicator ?indicator .
    ?indicator rdfs:label ?indicatorLabel .
    
    # Get phase information
    ?lciaResult epd:hasLifeCyclePhase ?lcPhase .
    ?lcPhase rdfs:label ?phase .
    
    # Get value and unit
    ?lciaResult epd:MeanValue ?value .
    ?lciaResult epd:hasUnit ?unit .
    
    {indicator_filter}
}}
ORDER BY ?indicatorLabel ?phase
LIMIT 100
"""
    return query


def build_all_epd_products_query(limit: int = 50) -> str:
    """
    Build query to list all EPD products
    
    Args:
        limit: Maximum number of products to return
        
    Returns:
        SPARQL query string
    """
    query = f"""{EPD_PREFIXES}

SELECT DISTINCT ?product ?name ?productTypeCategory
WHERE {{
    ?product a epd:ProcessDataSet ;
             epd:hasProcessInformation ?procInfo .
    
    ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
    ?keyInfo epd:Name ?name .
    
    OPTIONAL {{
        ?keyInfo epd:hasClassificationOrCategory ?classif .
        ?classif epd:ProductTypeCategory ?productTypeCategory .
    }}
}}
ORDER BY ?name
LIMIT {limit}
"""
    return query


def build_epd_product_count_query() -> str:
    """
    Build query to count total EPD products
    
    Returns:
        SPARQL query string
    """
    query = f"""{EPD_PREFIXES}

SELECT (COUNT(DISTINCT ?product) AS ?count)
WHERE {{
    ?product a epd:ProcessDataSet .
}}
"""
    return query


def build_epd_categories_query() -> str:
    """
    Build query to get all product categories
    
    Returns:
        SPARQL query string
    """
    query = f"""{EPD_PREFIXES}

SELECT DISTINCT ?productTypeCategory (COUNT(?product) AS ?count)
WHERE {{
    ?product a epd:ProcessDataSet ;
             epd:hasProcessInformation ?procInfo .
    
    ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
    ?keyInfo epd:hasClassificationOrCategory ?classif .
    ?classif epd:ProductTypeCategory ?productTypeCategory .
}}
GROUP BY ?productTypeCategory
ORDER BY DESC(?count)
"""
    return query


def build_epd_search_by_name_query(search_term: str, limit: int = 20) -> str:
    """
    Build query to search EPD products by name
    
    Args:
        search_term: Term to search for in product names
        limit: Maximum number of results
        
    Returns:
        SPARQL query string
    """
    query = f"""{EPD_PREFIXES}

SELECT DISTINCT ?product ?name ?nameDetail ?productTypeCategory
WHERE {{
    ?product a epd:ProcessDataSet ;
             epd:hasProcessInformation ?procInfo .
    
    ?procInfo epd:hasKeyDataSetInformation ?keyInfo .
    ?keyInfo epd:Name ?name .
    
    # Case-insensitive search
    FILTER(CONTAINS(LCASE(?name), LCASE("{search_term}")))
    
    OPTIONAL {{ ?keyInfo epd:NameDetail ?nameDetail . }}
    
    OPTIONAL {{
        ?keyInfo epd:hasClassificationOrCategory ?classif .
        ?classif epd:ProductTypeCategory ?productTypeCategory .
    }}
}}
ORDER BY ?name
LIMIT {limit}
"""
    return query


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


def validate_indicator_labels(labels: List[str]) -> bool:
    """
    Validate indicator label inputs
    
    Args:
        labels: List of indicator labels to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not labels:
        return True  # Empty list is valid (means no filtering)
    
    # Known valid indicators (based on ILCD standard)
    valid_indicators = {
        "GWP", "ODP", "AP", "EP", "POCP", "ADPE", "ADPF",
        "WDP", "PM", "IRP", "ETP-fw", "HTP-c", "HTP-nc",
        "SQP", "PERT", "PENRT", "SM", "RSF", "NRSF",
        "FW", "HWD", "NHWD", "RWD"
    }
    
    for label in labels:
        if label.upper() not in valid_indicators:
            return False
    
    return True