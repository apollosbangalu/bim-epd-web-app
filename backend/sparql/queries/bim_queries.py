"""
BIM SPARQL Queries Module - CORRECTED VERSION
Pre-built SPARQL query templates for BIMTool ontology with CORRECT namespaces

CRITICAL FIXES:
1. Correct namespace URIs from original Python app
2. Correct data structure using btml:hasMaterialProperty
3. Property objects (btml:GeneralInformation)
4. Extracts rdfs:comment for material definitions

Based on BIMTool knowledge graph with 361 materials
"""
from typing import Optional


# Namespace prefixes for BIM ontology - CORRECTED NAMESPACES
BIM_PREFIXES = """
PREFIX btml: <http://www.BimToolsMaterialLibrary.com/BimBuildingMaterialsOntology#>
PREFIX dcm: <https://w3id.org/digitalconstruction/0.3/BuildingMaterials#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
"""


def build_material_extraction_query(material_name: str) -> str:
    """
    Build comprehensive query to extract all BIM material data (10+ fields)
    
    CORRECTED STRUCTURE:
    - Root class: dcm:BuildingMaterial
    - Links to property object: btml:hasMaterialProperty
    - Property object type: btml:GeneralInformation
    - Property values: btml:MaterialName, btml:MaterialAssetName, etc.
    
    Extracts:
    1. Material URI
    2. Material name (from GeneralInformation)
    3. Asset name (optional)
    4. Property set name (optional)
    5. Description (optional)
    6. Keywords (optional)
    7. Comment (material definition - optional but critical)
    8. Primary category URI and label
    9. Secondary category URI and label (optional - only 6.6% have it)
    10. Class and subclass labels
    
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
    ?propertySetName
    ?description
    ?keywords
    ?comment
    ?primaryCategoryUri
    ?primaryCategoryLabel
    ?secondaryCategoryUri
    ?secondaryCategoryLabel
WHERE {{
    # Find material by MaterialName (case-insensitive partial match)
    ?material a dcm:BuildingMaterial ;
              btml:hasMaterialProperty ?genInfo .
    
    # GeneralInformation property object
    ?genInfo a btml:GeneralInformation ;
             btml:MaterialName ?name .
    
    # Fuzzy search on name
    FILTER(CONTAINS(LCASE(?name), LCASE("{material_name}")))
    
    # Optional fields from GeneralInformation
    OPTIONAL {{ ?genInfo btml:MaterialAssetName ?materialAssetName . }}
    OPTIONAL {{ ?genInfo btml:PropertySetName ?propertySetName . }}
    OPTIONAL {{ ?genInfo btml:Description ?description . }}
    OPTIONAL {{ ?genInfo btml:Keywords ?keywords . }}
    
    # Material definition comment (CRITICAL for understanding composition)
    OPTIONAL {{ ?material rdfs:comment ?comment . }}
    
    # Get primary category (required)
    ?material btml:hasPrimaryCategory ?primaryCategoryUri .
    ?primaryCategoryUri rdfs:label ?primaryCategoryLabel .
    
    # Get secondary category (OPTIONAL - only 6.6% of materials have this)
    OPTIONAL {{
        ?material btml:hasSecondaryCategory ?secondaryCategoryUri .
        ?secondaryCategoryUri rdfs:label ?secondaryCategoryLabel .
    }}
}}
LIMIT 10
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
    ?propertySetName
    ?description
    ?keywords
    ?comment
    ?primaryCategoryLabel
    ?secondaryCategoryLabel
WHERE {{
    # Get GeneralInformation property object
    <{material_uri}> a dcm:BuildingMaterial ;
                     btml:hasMaterialProperty ?genInfo .
    
    ?genInfo a btml:GeneralInformation ;
             btml:MaterialName ?name .
    
    # Optional fields
    OPTIONAL {{ ?genInfo btml:MaterialAssetName ?materialAssetName . }}
    OPTIONAL {{ ?genInfo btml:PropertySetName ?propertySetName . }}
    OPTIONAL {{ ?genInfo btml:Description ?description . }}
    OPTIONAL {{ ?genInfo btml:Keywords ?keywords . }}
    OPTIONAL {{ <{material_uri}> rdfs:comment ?comment . }}
    
    # Primary category
    <{material_uri}> btml:hasPrimaryCategory ?primaryCategory .
    ?primaryCategory rdfs:label ?primaryCategoryLabel .
    
    # Secondary category (optional)
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


def build_material_properties_query(material_uri: str) -> str:
    """
    Build query to fetch all property types for a specific material
    
    Returns property objects for Mechanical, Physical, Thermal, Behavior properties
    
    Args:
        material_uri: Full URI of the material
        
    Returns:
        SPARQL query to get material properties
    """
    query = f"""{BIM_PREFIXES}

SELECT ?propertyType ?property
WHERE {{
    <{material_uri}> btml:hasMaterialProperty ?property .
    ?property a ?propertyType .
    
    # Filter to known property types
    FILTER(?propertyType IN (
        btml:GeneralInformation,
        btml:MechanicalProperty,
        btml:PhysicalProperty,
        btml:ThermalProperty,
        btml:BehaviorProperty
    ))
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
              btml:hasPrimaryCategory ?category ;
              btml:hasMaterialProperty ?genInfo .
    
    ?genInfo a btml:GeneralInformation ;
             btml:MaterialName ?name .
    
    ?category rdfs:label ?categoryLabel .
    
    FILTER(CONTAINS(LCASE(?categoryLabel), LCASE("{category_label}")))
}}
ORDER BY ?name
"""
    return query


def build_materials_by_keyword_query(keyword: str) -> str:
    """
    Build query to search materials by keyword
    
    Searches across name, description, and keywords fields in GeneralInformation.
    
    Args:
        keyword: Search keyword
        
    Returns:
        SPARQL query string
    """
    query = f"""{BIM_PREFIXES}

SELECT DISTINCT ?material ?name ?description ?keywords
WHERE {{
    ?material a dcm:BuildingMaterial ;
              btml:hasMaterialProperty ?genInfo .
    
    ?genInfo a btml:GeneralInformation ;
             btml:MaterialName ?name .
    
    OPTIONAL {{ ?genInfo btml:Description ?description . }}
    OPTIONAL {{ ?genInfo btml:Keywords ?keywords . }}
    
    # Search across all text fields
    FILTER(
        CONTAINS(LCASE(?name), LCASE("{keyword}")) ||
        CONTAINS(LCASE(?description), LCASE("{keyword}")) ||
        CONTAINS(LCASE(?keywords), LCASE("{keyword}"))
    )
}}
ORDER BY ?name
"""
    return query


def validate_material_name(material_name: str) -> bool:
    """
    Validate material name input
    
    Args:
        material_name: Material name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not material_name or not material_name.strip():
        return False
    
    # Check for dangerous characters
    dangerous_chars = ["<", ">", "{", "}", ";", "'", '"', "\\"]
    for char in dangerous_chars:
        if char in material_name:
            return False
    
    return True