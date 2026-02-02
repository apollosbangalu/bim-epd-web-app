#!/usr/bin/env python3
"""Test if our changes broke imports"""
import sys
import traceback

print("=" * 80)
print("TESTING IMPORTS")
print("=" * 80)

# Test 1: Core imports
print("\n1. Testing core imports...")
try:
    from core.config import settings
    print("   ✓ core.config.settings")
except Exception as e:
    print(f"   ✗ core.config.settings: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from llm import create_llm_client
    print("   ✓ llm.create_llm_client")
except Exception as e:
    print(f"   ✗ llm.create_llm_client: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from sparql.client import SPARQLClient, SPARQLClientFactory
    print("   ✓ sparql.client")
except Exception as e:
    print(f"   ✗ sparql.client: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: BIM Extractor import
print("\n2. Testing BIM Extractor import...")
try:
    from agents.bim_extractor import BIMExtractorAgent
    print("   ✓ agents.bim_extractor.BIMExtractorAgent")
    
    # Check signature
    import inspect
    sig = inspect.signature(BIMExtractorAgent.__init__)
    params = list(sig.parameters.keys())
    print(f"   Parameters: {params}")
    
    if 'thesaurus_client' in params:
        print("   ✓ Has thesaurus_client parameter")
    else:
        print("   ✗ MISSING thesaurus_client parameter")
        print("   → This will cause initialization to fail")
    
except Exception as e:
    print(f"   ✗ agents.bim_extractor: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Orchestrator import
print("\n3. Testing Orchestrator import...")
try:
    from agents.orchestrator import AgentOrchestrator
    print("   ✓ agents.orchestrator.AgentOrchestrator")
except Exception as e:
    print(f"   ✗ agents.orchestrator: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create orchestrator
print("\n4. Testing Orchestrator creation...")
try:
    orchestrator = AgentOrchestrator(llm_provider="openai")
    print("   ✓ Orchestrator created")
    
    # Check if agents initialized
    if hasattr(orchestrator, 'bim_extractor'):
        print("   ✓ BIM Extractor initialized")
        if hasattr(orchestrator.bim_extractor, 'thesaurus_client'):
            print("   ✓ BIM Extractor has thesaurus_client")
        else:
            print("   ✗ BIM Extractor MISSING thesaurus_client")
    else:
        print("   ✗ BIM Extractor NOT initialized")
        
except Exception as e:
    print(f"   ✗ Orchestrator creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("ALL IMPORTS SUCCESSFUL")
print("=" * 80)
print("\nIf imports work but API still doesn't respond,")
print("the issue is likely in FastAPI startup or routing.")