"""
Thesaurus SPARQL Queries Module
Pre-built SPARQL query templates for SKOS-based concept mapping thesaurus

Features:
- Semantic concept mappings between BIM and EPD
- Multiple match types (exactMatch, closeMatch)
- English-only labels (no multilingual fallback)
- Hierarchical relationships
- Confidence scoring

Based on integrated thesaurus with BIMTool, EPD, BERR, and DCM taxonomies
"""
from typing import List, Optional


# Namespace prefixes for Thesaurus ontology
THESAURUS_PREFIXES = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX bimtooltax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#>
PREFIX epdtax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#>
PREFIX berrtax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/berr#>
PREFIX dcmtax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/dcm#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""


def build_bim_to_epd_mapping_query(
    primary_category_uri: str,
    secondary_category_uri: Optional[str] = None
) -> str:
    """
    Build query to find semantic mappings from BIM categories to EPD concepts
    
    CRITICAL FEATURES:
    - Queries BOTH primary and secondary categories
    - Uses ONLY exactMatch and closeMatch (NOT relatedMatch)
    - Returns actual URIs and labels
    - English-only labels (no COALESCE fallback)
    - Indicates match type and confidence
    
    Args:
        primary_category_uri: Primary BIM category URI
        secondary_category_uri: Optional secondary BIM category URI
        
    Returns:
        SPARQL query string
    """
    # Build secondary category block if provided
    secondary_block = ""
    if secondary_category_uri:
        secondary_block = f"""
    UNION
    # Secondary category matching (if provided)
    {{
        VALUES ?bim_concept {{ <{secondary_category_uri}> }}
        BIND("secondary" AS ?category_type)
        
        # Exact matches
        {{
            ?bim_concept skos:exactMatch ?epd_concept .
            BIND("exactMatch" AS ?match_type)
        }}
        UNION
        # Close matches
        {{
            ?bim_concept skos:closeMatch ?epd_concept .
            BIND("closeMatch" AS ?match_type)
        }}
        
        # Get labels - ENGLISH ONLY (NO FALLBACK)
        ?bim_concept skos:prefLabel ?bim_label .
        FILTER(LANG(?bim_label) = "en")
        
        ?epd_concept skos:prefLabel ?epd_label .
        FILTER(LANG(?epd_label) = "en")
        
        # Ensure EPD concept is from epdtax namespace
        FILTER(STRSTARTS(STR(?epd_concept), "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#"))
    }}
        """
    
    query = f"""{THESAURUS_PREFIXES}

SELECT DISTINCT
    ?bim_concept
    ?bim_label
    ?epd_concept
    ?epd_label
    ?match_type
    ?category_type
WHERE {{
    # Primary category matching
    {{
        VALUES ?bim_concept {{ <{primary_category_uri}> }}
        BIND("primary" AS ?category_type)
        
        # Exact matches
        {{
            ?bim_concept skos:exactMatch ?epd_concept .
            BIND("exactMatch" AS ?match_type)
        }}
        UNION
        # Close matches
        {{
            ?bim_concept skos:closeMatch ?epd_concept .
            BIND("closeMatch" AS ?match_type)
        }}
        
        # Get labels - ENGLISH ONLY (NO FALLBACK)
        ?bim_concept skos:prefLabel ?bim_label .
        FILTER(LANG(?bim_label) = "en")
        
        ?epd_concept skos:prefLabel ?epd_label .
        FILTER(LANG(?epd_label) = "en")
        
        # Ensure EPD concept is from epdtax namespace
        FILTER(STRSTARTS(STR(?epd_concept), "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#"))
    }}
    {secondary_block}
}}
ORDER BY DESC(?match_type) ?category_type
"""
    return query


def build_concept_details_query(concept_uri: str) -> str:
    """
    Build query to get complete details for a SKOS concept
    
    Args:
        concept_uri: Full URI of the concept
        
    Returns:
        SPARQL query string
    """
    query = f"""{THESAURUS_PREFIXES}

SELECT DISTINCT
    ?prefLabel
    ?altLabel
    ?definition
    ?broader
    ?narrower
    ?related
WHERE {{
    BIND(<{concept_uri}> AS ?concept)
    
    # Get preferred label (English only)
    OPTIONAL {{
        ?concept skos:prefLabel ?prefLabel .
        FILTER(LANG(?prefLabel) = "en")
    }}
    
    # Get alternative labels
    OPTIONAL {{
        ?concept skos:altLabel ?altLabel .
        FILTER(LANG(?altLabel) = "en")
    }}
    
    # Get definition
    OPTIONAL {{
        ?concept skos:definition ?definition .
        FILTER(LANG(?definition) = "en")
    }}
    
    # Get hierarchical relationships
    OPTIONAL {{ ?concept skos:broader ?broader . }}
    OPTIONAL {{ ?concept skos:narrower ?narrower . }}
    
    # Get related concepts
    OPTIONAL {{ ?concept skos:related ?related . }}
}}
"""
    return query


def build_all_mappings_query(match_type: Optional[str] = None) -> str:
    """
    Build query to get all concept mappings
    
    Args:
        match_type: Optional filter ('exactMatch', 'closeMatch', 'broadMatch', 'narrowMatch')
        
    Returns:
        SPARQL query string
    """
    match_filter = ""
    match_pattern = ""
    
    if match_type == "exactMatch":
        match_pattern = "?concept1 skos:exactMatch ?concept2 ."
    elif match_type == "closeMatch":
        match_pattern = "?concept1 skos:closeMatch ?concept2 ."
    elif match_type == "broadMatch":
        match_pattern = "?concept1 skos:broadMatch ?concept2 ."
    elif match_type == "narrowMatch":
        match_pattern = "?concept1 skos:narrowMatch ?concept2 ."
    else:
        # All match types
        match_pattern = """
        {
            ?concept1 skos:exactMatch ?concept2 .
            BIND("exactMatch" AS ?match_type)
        }
        UNION
        {
            ?concept1 skos:closeMatch ?concept2 .
            BIND("closeMatch" AS ?match_type)
        }
        UNION
        {
            ?concept1 skos:broadMatch ?concept2 .
            BIND("broadMatch" AS ?match_type)
        }
        UNION
        {
            ?concept1 skos:narrowMatch ?concept2 .
            BIND("narrowMatch" AS ?match_type)
        }
        """
    
    query = f"""{THESAURUS_PREFIXES}

SELECT DISTINCT
    ?concept1
    ?label1
    ?concept2
    ?label2
    ?match_type
WHERE {{
    {match_pattern}
    
    # Get labels (English only)
    ?concept1 skos:prefLabel ?label1 .
    FILTER(LANG(?label1) = "en")
    
    ?concept2 skos:prefLabel ?label2 .
    FILTER(LANG(?label2) = "en")
}}
ORDER BY ?match_type ?label1
"""
    return query


def build_concept_search_query(search_term: str) -> str:
    """
    Build query to search concepts by label
    
    Args:
        search_term: Search term to match against labels
        
    Returns:
        SPARQL query string
    """
    query = f"""{THESAURUS_PREFIXES}

SELECT DISTINCT
    ?concept
    ?label
    ?definition
WHERE {{
    ?concept a skos:Concept ;
             skos:prefLabel ?label .
    
    FILTER(LANG(?label) = "en")
    FILTER(CONTAINS(LCASE(?label), "{search_term.lower()}"))
    
    OPTIONAL {{
        ?concept skos:definition ?definition .
        FILTER(LANG(?definition) = "en")
    }}
}}
ORDER BY ?label
LIMIT 50
"""
    return query


def build_hierarchical_query(
    concept_uri: str,
    direction: str = "both"
) -> str:
    """
    Build query to get hierarchical relationships
    
    Args:
        concept_uri: Concept URI to start from
        direction: 'broader', 'narrower', or 'both'
        
    Returns:
        SPARQL query string
    """
    if direction == "broader":
        relationship_pattern = """
        <{concept_uri}> skos:broader ?related .
        BIND("broader" AS ?relationship)
        """
    elif direction == "narrower":
        relationship_pattern = """
        <{concept_uri}> skos:narrower ?related .
        BIND("narrower" AS ?relationship)
        """
    else:  # both
        relationship_pattern = """
        {
            <{concept_uri}> skos:broader ?related .
            BIND("broader" AS ?relationship)
        }
        UNION
        {
            <{concept_uri}> skos:narrower ?related .
            BIND("narrower" AS ?relationship)
        }
        """
    
    query = f"""{THESAURUS_PREFIXES}

SELECT DISTINCT
    ?related
    ?label
    ?relationship
WHERE {{
    {relationship_pattern}
    
    ?related skos:prefLabel ?label .
    FILTER(LANG(?label) = "en")
}}
ORDER BY ?relationship ?label
"""
    return query


def build_collections_query() -> str:
    """
    Build query to get all SKOS collections
    
    Returns:
        SPARQL query string
    """
    query = f"""{THESAURUS_PREFIXES}

SELECT DISTINCT
    ?collection
    ?label
    (COUNT(?member) AS ?member_count)
WHERE {{
    ?collection a skos:Collection ;
                skos:prefLabel ?label .
    
    FILTER(LANG(?label) = "en")
    
    OPTIONAL {{
        ?collection skos:member ?member .
    }}
}}
GROUP BY ?collection ?label
ORDER BY ?label
"""
    return query


# Validation helpers
def validate_concept_uri(uri: str) -> bool:
    """
    Validate concept URI
    
    Args:
        uri: Concept URI to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not uri or not isinstance(uri, str):
        return False
    
    # Must be valid HTTP URI
    if not uri.startswith("http://") and not uri.startswith("https://"):
        return False
    
    # Should be from known taxonomy namespaces
    valid_prefixes = [
        "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#",
        "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#",
        "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/berr#",
        "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/dcm#"
    ]
    
    return any(uri.startswith(prefix) for prefix in valid_prefixes)


def calculate_mapping_confidence(match_type: str, category_type: str) -> float:
    """
    Calculate confidence score for a mapping
    
    Args:
        match_type: 'exactMatch' or 'closeMatch'
        category_type: 'primary' or 'secondary'
        
    Returns:
        Confidence score (0.0-1.0)
    """
    if match_type == "exactMatch" and category_type == "primary":
        return 1.0
    elif match_type == "exactMatch" and category_type == "secondary":
        return 0.95
    elif match_type == "closeMatch" and category_type == "primary":
        return 0.85
    elif match_type == "closeMatch" and category_type == "secondary":
        return 0.80
    else:
        return 0.5  # Default for other cases