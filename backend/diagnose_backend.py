"""
Backend Diagnostic Script
Run this to check if your FastAPI backend is set up correctly
"""

def diagnose_backend():
    """Run diagnostics on the backend setup"""
    import sys
    import os
    
    print("=" * 60)
    print("BIM-EPD Backend Diagnostic Tool")
    print("=" * 60)
    print()
    
    # Check 1: Import main app
    print("✓ Check 1: Importing FastAPI app...")
    try:
        from api.main import app
        print("  ✅ Successfully imported app from api.main")
    except ImportError as e:
        print(f"  ❌ Failed to import: {e}")
        print("  → Make sure you're running this from the backend directory")
        sys.exit(1)
    
    # Check 2: List all routes
    print("\n✓ Check 2: Registered routes...")
    config_routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  → {route.path}")
            if 'config' in route.path:
                config_routes.append(route.path)
    
    if config_routes:
        print(f"  ✅ Found {len(config_routes)} config routes:")
        for r in config_routes:
            print(f"     • {r}")
    else:
        print("  ❌ No /config routes found!")
        print("  → Check that config.router is included in main.py")
    
    # Check 3: Check config router
    print("\n✓ Check 3: Config router...")
    try:
        from api.routes import config
        print(f"  ✅ Config router imported successfully")
        print(f"  → Router has {len(config.router.routes)} routes")
        for route in config.router.routes:
            print(f"     • {route.path} {route.methods}")
    except ImportError as e:
        print(f"  ❌ Failed to import config router: {e}")
        print("  → Check that api/routes/config.py exists")
    
    # Check 4: Test endpoint directly
    print("\n✓ Check 4: Testing /config/agents endpoint directly...")
    try:
        from api.routes.config import get_agent_configurations
        import asyncio
        result = asyncio.run(get_agent_configurations())
        print(f"  ✅ Endpoint function works!")
        print(f"  → Returns {result.get('total_agents', 0)} agents")
    except Exception as e:
        print(f"  ❌ Error calling endpoint: {e}")
    
    # Check 5: File structure
    print("\n✓ Check 5: File structure...")
    required_files = [
        "api/main.py",
        "api/routes/__init__.py",
        "api/routes/config.py",
    ]
    for filepath in required_files:
        if os.path.exists(filepath):
            print(f"  ✅ {filepath}")
        else:
            print(f"  ❌ Missing: {filepath}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Diagnostic Summary")
    print("=" * 60)
    
    if config_routes and len(config_routes) >= 2:
        print("✅ Config routes are registered")
        print("\n🎯 Next steps:")
        print("1. Start server: pipenv run uvicorn api.main:app --reload --port 8000")
        print("2. Visit: http://localhost:8000/docs")
        print("3. Test: http://localhost:8000/api/config/agents")
    else:
        print("❌ Config routes are NOT properly registered")
        print("\n🔧 Fix:")
        print("1. Open backend/api/main.py")
        print("2. Add: from api.routes import config")
        print("3. Add: app.include_router(config.router, prefix='/api', tags=['config'])")
        print("4. Restart server")


if __name__ == "__main__":
    diagnose_backend()
