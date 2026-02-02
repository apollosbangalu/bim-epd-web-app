"""
Thesaurus SPARQL Queries Module - CORRECTED VERSION
Pre-built SPARQL query templates for SKOS-based concept mapping thesaurus

CRITICAL FIXES:
1. Correct namespace URIs from original Python app
2. English-only labels with FILTER(LANG(?label) = "en")
3. Proper match types (exactMatch, closeMatch)
4. Confidence scoring based on match type

Features:
- Semantic concept mappings between BIM and EPD
- Multiple match types with confidence scores
- Hierarchical relationships
- Quality filtering

Based on integrated thesaurus with BIMTool, EPD, BERR, and DCM taxonomies
"""
from typing import List, Optional


# Namespace prefixes for Thesaurus ontology - CORRECTED NAMESPACES
THESAURUS_PREFIXES = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX bimtooltax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#>
PREFIX epdtax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#>
PREFIX berrtax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/berr#>
PREFIX dcmtax: <http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/dcm#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
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
    # Extract the category name from URI for thesaurus mapping
    # e.g., "http://...#Concrete" → "Concrete"
    primary_name = primary_category_uri.split('#')[-1].split('/')[-1]
    
    # Build the thesaurus BIM taxonomy URI
    bim_thesaurus_uri = f"bimtooltax:{primary_name}"
    
    # Build secondary category block if provided
    secondary_block = ""
    if secondary_category_uri:
        secondary_name = secondary_category_uri.split('#')[-1].split('/')[-1]
        bim_thesaurus_secondary = f"bimtooltax:{secondary_name}"
        
        secondary_block = f"""
    UNION
    # Secondary category matching (if provided)
    {{
        VALUES ?bim_concept {{ {bim_thesaurus_secondary} }}
        BIND("secondary" AS ?category_type)
        
        # Exact matches
        {{
            ?bim_concept skos:exactMatch ?epd_concept .
            BIND("exactMatch" AS ?match_type)
            BIND(1.0 AS ?confidence)
        }}
        UNION
        # Close matches
        {{
            ?bim_concept skos:closeMatch ?epd_concept .
            BIND("closeMatch" AS ?match_type)
            BIND(0.8 AS ?confidence)
        }}
        
        # Get labels - ENGLISH ONLY (NO FALLBACK)
        ?bim_concept skos:prefLabel ?bim_label .
        FILTER(LANG(?bim_label) = "en")
        
        ?epd_concept skos:prefLabel ?epd_label .
        FILTER(LANG(?epd_label) = "en")
        
        # Ensure EPD concept is in EPD taxonomy - ✅ FIXED!
        FILTER(STRSTARTS(STR(?epd_concept), "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#"))
    }}
"""
    
    query = f"""{THESAURUS_PREFIXES}

SELECT DISTINCT
    ?category_type
    ?bim_concept
    ?bim_label
    ?epd_concept
    ?epd_label
    ?match_type
    ?confidence
WHERE {{
    # Primary category matching
    {{
        VALUES ?bim_concept {{ {bim_thesaurus_uri} }}
        BIND("primary" AS ?category_type)
        
        # Exact matches (confidence 1.0)
        {{
            ?bim_concept skos:exactMatch ?epd_concept .
            BIND("exactMatch" AS ?match_type)
            BIND(1.0 AS ?confidence)
        }}
        UNION
        # Close matches (confidence 0.8)
        {{
            ?bim_concept skos:closeMatch ?epd_concept .
            BIND("closeMatch" AS ?match_type)
            BIND(0.8 AS ?confidence)
        }}
        
        # Get labels - ENGLISH ONLY (NO FALLBACK)
        ?bim_concept skos:prefLabel ?bim_label .
        FILTER(LANG(?bim_label) = "en")
        
        ?epd_concept skos:prefLabel ?epd_label .
        FILTER(LANG(?epd_label) = "en")
        
        # Ensure EPD concept is in EPD taxonomy - ✅ FIXED!
        FILTER(STRSTARTS(STR(?epd_concept), "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#"))
    }}
    {secondary_block}
}}
ORDER BY ?confidence DESC, ?category_type
"""
    return query

def build_bim_ontology_to_thesaurus_mapping_query(bim_ontology_uri: str) -> str:
    """
    Build query to find thesaurus taxonomy URI for a BIM ontology URI
    
    Uses owl:equivalentClass to find the mapping
    
    Args:
        bim_ontology_uri: BIM ontology URI (e.g., "btml:Concrete")
        
    Returns:
        SPARQL query string
    """
    query = f"""{THESAURUS_PREFIXES}

SELECT ?thesaurus_uri ?label
WHERE {{
    # Find thesaurus concept equivalent to BIM ontology concept
    ?thesaurus_uri owl:equivalentClass <{bim_ontology_uri}> .
    
    # Ensure it's from bimtooltax namespace
    FILTER(STRSTARTS(STR(?thesaurus_uri), "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#"))
    
    # Get label (English only)
    OPTIONAL {{
        ?thesaurus_uri skos:prefLabel ?label .
        FILTER(LANG(?label) = "en")
    }}
}}
LIMIT 1
"""
    return query


def build_all_concept_mappings_query() -> str:
    """
    Build query to get all concept mappings between taxonomies
    
    Returns:
        SPARQL query string
    """
    query = f"""{THESAURUS_PREFIXES}

SELECT DISTINCT ?source_concept ?source_label ?target_concept ?target_label ?match_type
WHERE {{
    # Get all mappings
    {{
        ?source_concept skos:exactMatch ?target_concept .
        BIND("exactMatch" AS ?match_type)
    }}
    UNION
    {{
        ?source_concept skos:closeMatch ?target_concept .
        BIND("closeMatch" AS ?match_type)
    }}
    UNION
    {{
        ?source_concept skos:broadMatch ?target_concept .
        BIND("broadMatch" AS ?match_type)
    }}
    UNION
    {{
        ?source_concept skos:narrowMatch ?target_concept .
        BIND("narrowMatch" AS ?match_type)
    }}
    
    # Get labels (English only)
    OPTIONAL {{
        ?source_concept skos:prefLabel ?source_label .
        FILTER(LANG(?source_label) = "en")
    }}
    
    OPTIONAL {{
        ?target_concept skos:prefLabel ?target_label .
        FILTER(LANG(?target_label) = "en")
    }}
}}
ORDER BY ?match_type ?source_label
LIMIT 100
"""
    return query


def build_concept_hierarchy_query(concept_uri: str) -> str:
    """
    Build query to get hierarchical relationships for a concept
    
    Args:
        concept_uri: URI of the concept
        
    Returns:
        SPARQL query string
    """
    query = f"""{THESAURUS_PREFIXES}

SELECT DISTINCT ?relation ?related_concept ?related_label
WHERE {{
    # Get broader concepts
    {{
        <{concept_uri}> skos:broader ?related_concept .
        BIND("broader" AS ?relation)
    }}
    UNION
    # Get narrower concepts
    {{
        <{concept_uri}> skos:narrower ?related_concept .
        BIND("narrower" AS ?relation)
    }}
    UNION
    # Get related concepts
    {{
        <{concept_uri}> skos:related ?related_concept .
        BIND("related" AS ?relation)
    }}
    
    # Get label (English only)
    OPTIONAL {{
        ?related_concept skos:prefLabel ?related_label .
        FILTER(LANG(?related_label) = "en")
    }}
}}
ORDER BY ?relation ?related_label
"""
    return query


def build_search_concepts_query(search_term: str, taxonomy: Optional[str] = None) -> str:
    """
    Build query to search for concepts by label
    
    Args:
        search_term: Term to search for
        taxonomy: Optional taxonomy to limit search (bimtooltax, epdtax, berrtax, dcmtax)
        
    Returns:
        SPARQL query string
    """
    # Build taxonomy filter if specified
    taxonomy_filter = ""
    if taxonomy:
        taxonomy_map = {
            "bimtool": "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#",
            "epd": "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#",
            "berr": "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/berr#",
            "dcm": "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/dcm#"
        }
        
        if taxonomy.lower() in taxonomy_map:
            namespace_uri = taxonomy_map[taxonomy.lower()]
            taxonomy_filter = f'FILTER(STRSTARTS(STR(?concept), "{namespace_uri}"))'
    
    query = f"""{THESAURUS_PREFIXES}

SELECT DISTINCT ?concept ?label ?definition
WHERE {{
    ?concept a skos:Concept ;
             skos:prefLabel ?label .
    
    # English labels only
    FILTER(LANG(?label) = "en")
    
    # Case-insensitive search
    FILTER(CONTAINS(LCASE(?label), LCASE("{search_term}")))
    
    {taxonomy_filter}
    
    # Get definition if available
    OPTIONAL {{
        ?concept skos:definition ?definition .
        FILTER(LANG(?definition) = "en")
    }}
}}
ORDER BY ?label
LIMIT 50
"""
    return query


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


def validate_concept_uri(uri: str) -> bool:
    """
    Validate concept URI format
    
    Args:
        uri: Concept URI to validate
        
    Returns:
        True if valid, False otherwise
    """
    valid_prefixes = [
        "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/bimtool#",
        "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/epd#",
        "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/berr#",
        "http://bimlcaintegration/buildingmaterialsepdilcd/thesaurus/dcm#",
        "http://www.BimToolsMaterialLibrary.com/BimBuildingMaterialsOntology#",
        "http://www.EpdLcaOntology.com/EpdLcaDataSetOntology/"
    ]
    
    return any(uri.startswith(prefix) for prefix in valid_prefixes)