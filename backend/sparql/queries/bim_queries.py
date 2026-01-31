"""
BIM SPARQL Queries Module
Pre-built SPARQL query templates for BIMTool ontology

Contains all query patterns for extracting building material data:
- Material extraction (9+ fields)
- Category navigation
- Property retrieval
- Material search patterns

Based on BIMTool knowledge graph with 361 materials
"""
from typing import Optional


# Namespace prefixes for BIM ontology
BIM_PREFIXES = """
PREFIX dcm: <http://www.semanticweb.org/dani/ontologies/2024/9/bimclasses/>
PREFIX btml: <http://www.semanticweb.org/dani/ontologies/2024/9/BuildingMaterial/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
"""


def build_material_extraction_query(material_name: str) -> str:
    """
    Build comprehensive query to extract all BIM material data (9+ fields)
    
    Extracts:
    1. Material URI and name
    2. Asset name (optional)
    3. Description (optional)
    4. Keywords (optional)
    5. Comment (material definition - optional but critical)
    6. Primary category URI and label
    7. Secondary category URI and label (optional - only 6.6% have it)
    8. Class and subclass (optional)
    9. Property set (optional)
    
    Args:
        material_name: Name of the material to search for
        
    Returns:
        Complete SPARQL query string
    """
    query = f"""{BIM_PREFIXES}

SELECT DISTINCT 
    ?material 
    ?name
    ?materialAssetName
    ?description
    ?keywords
    ?comment
    ?primaryCategoryUri
    ?primaryCategoryLabel
    ?secondaryCategoryUri
    ?secondaryCategoryLabel
    ?class
    ?subclass
    ?propertySet
WHERE {{
    # Find material by name (case-insensitive partial match)
    ?material a dcm:BuildingMaterial ;
              btml:Name ?name .
    
    FILTER(CONTAINS(LCASE(?name), LCASE("{material_name}")))
    
    # Get asset name (optional)
    OPTIONAL {{
        ?material btml:MaterialAssetName ?materialAssetName .
    }}
    
    # Get description (optional)
    OPTIONAL {{
        ?material btml:Description ?description .
    }}
    
    # Get keywords (optional)
    OPTIONAL {{
        ?material btml:Keywords ?keywords .
    }}
    
    # Get material definition comment (CRITICAL for understanding composition)
    OPTIONAL {{
        ?material rdfs:comment ?comment .
    }}
    
    # Get primary category (required)
    ?material btml:hasPrimaryCategory ?primaryCategoryUri .
    ?primaryCategoryUri rdfs:label ?primaryCategoryLabel .
    
    # Get secondary category (OPTIONAL - only 6.6% of materials have this)
    OPTIONAL {{
        ?material btml:hasSecondaryCategory ?secondaryCategoryUri .
        ?secondaryCategoryUri rdfs:label ?secondaryCategoryLabel .
    }}
    
    # Get class and subclass (optional)
    OPTIONAL {{
        ?material btml:Class ?class .
    }}
    OPTIONAL {{
        ?material btml:Subclass ?subclass .
    }}
    
    # Get property set (optional)
    OPTIONAL {{
        ?material btml:Pset_MaterialCommon ?propertySet .
    }}
}}
LIMIT 10
"""
    return query


def build_material_properties_query(material_uri: str) -> str:
    """
    Build query to fetch all properties for a specific material
    
    Properties in BIM are separate objects linked via hasMaterialProperty.
    This query retrieves all property objects and their values.
    
    Args:
        material_uri: Full URI of the material
        
    Returns:
        SPARQL query to get material properties
    """
    query = f"""{BIM_PREFIXES}

SELECT ?propertyType ?propertyValue
WHERE {{
    <{material_uri}> btml:hasMaterialProperty ?property .
    ?property a ?propertyType ;
              ?predicate ?propertyValue .
    
    # Filter out type statements
    FILTER(?predicate != rdf:type)
}}
"""
    return query


def build_category_materials_query(category_label: str) -> str:
    """
    Build query to find all materials in a specific category
    
    Args:
        category_label: Label of the category (e.g., "Concrete", "Metal")
        
    Returns:
        SPARQL query string
    """
    query = f"""{BIM_PREFIXES}

SELECT DISTINCT ?material ?name ?categoryLabel
WHERE {{
    ?material a dcm:BuildingMaterial ;
              btml:Name ?name ;
              btml:hasPrimaryCategory ?category .
    
    ?category rdfs:label ?categoryLabel .
    
    FILTER(CONTAINS(LCASE(?categoryLabel), LCASE("{category_label}")))
}}
ORDER BY ?name
"""
    return query


def build_materials_by_keyword_query(keyword: str) -> str:
    """
    Build query to search materials by keyword
    
    Searches across name, description, keywords, and asset name fields.
    
    Args:
        keyword: Search keyword
        
    Returns:
        SPARQL query string
    """
    query = f"""{BIM_PREFIXES}

SELECT DISTINCT ?material ?name ?description ?keywords
WHERE {{
    ?material a dcm:BuildingMaterial ;
              btml:Name ?name .
    
    OPTIONAL {{ ?material btml:Description ?description . }}
    OPTIONAL {{ ?material btml:Keywords ?keywords . }}
    OPTIONAL {{ ?material btml:MaterialAssetName ?assetName . }}
    
    # Search across all text fields
    FILTER(
        CONTAINS(LCASE(?name), LCASE("{keyword}")) ||
        CONTAINS(LCASE(?description), LCASE("{keyword}")) ||
        CONTAINS(LCASE(?keywords), LCASE("{keyword}")) ||
        CONTAINS(LCASE(?assetName), LCASE("{keyword}"))
    )
}}
ORDER BY ?name
"""
    return query


def build_material_by_uri_query(material_uri: str) -> str:
    """
    Build query to get complete material data by URI
    
    Args:
        material_uri: Full URI of the material
        
    Returns:
        SPARQL query string
    """
    query = f"""{BIM_PREFIXES}

SELECT DISTINCT 
    ?name
    ?materialAssetName
    ?description
    ?keywords
    ?comment
    ?primaryCategoryLabel
    ?secondaryCategoryLabel
WHERE {{
    <{material_uri}> a dcm:BuildingMaterial ;
                     btml:Name ?name .
    
    OPTIONAL {{ <{material_uri}> btml:MaterialAssetName ?materialAssetName . }}
    OPTIONAL {{ <{material_uri}> btml:Description ?description . }}
    OPTIONAL {{ <{material_uri}> btml:Keywords ?keywords . }}
    OPTIONAL {{ <{material_uri}> rdfs:comment ?comment . }}
    
    <{material_uri}> btml:hasPrimaryCategory ?primaryCategory .
    ?primaryCategory rdfs:label ?primaryCategoryLabel .
    
    OPTIONAL {{
        <{material_uri}> btml:hasSecondaryCategory ?secondaryCategory .
        ?secondaryCategory rdfs:label ?secondaryCategoryLabel .
    }}
}}
"""
    return query


def build_all_categories_query() -> str:
    """
    Build query to get all available material categories
    
    Returns:
        SPARQL query string
    """
    query = f"""{BIM_PREFIXES}

SELECT DISTINCT ?category ?label
WHERE {{
    ?material a dcm:BuildingMaterial ;
              btml:hasPrimaryCategory ?category .
    
    ?category rdfs:label ?label .
}}
ORDER BY ?label
"""
    return query


def build_material_count_query(category_label: Optional[str] = None) -> str:
    """
    Build query to count materials, optionally filtered by category
    
    Args:
        category_label: Optional category to filter by
        
    Returns:
        SPARQL query string
    """
    if category_label:
        query = f"""{BIM_PREFIXES}

SELECT (COUNT(DISTINCT ?material) AS ?count)
WHERE {{
    ?material a dcm:BuildingMaterial ;
              btml:hasPrimaryCategory ?category .
    
    ?category rdfs:label ?categoryLabel .
    
    FILTER(CONTAINS(LCASE(?categoryLabel), LCASE("{category_label}")))
}}
"""
    else:
        query = f"""{BIM_PREFIXES}

SELECT (COUNT(DISTINCT ?material) AS ?count)
WHERE {{
    ?material a dcm:BuildingMaterial .
}}
"""
    return query


# Query validation helper
def validate_material_name(name: str) -> bool:
    """
    Validate material name input
    
    Args:
        name: Material name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Remove dangerous characters that could break SPARQL
    dangerous_chars = ["'", '"', "{", "}", "<", ">"]
    for char in dangerous_chars:
        if char in name:
            return False
    
    return True