#!/usr/bin/env python3
"""Gradually add components to find what breaks"""
from fastapi import FastAPI
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("Step 1: Creating FastAPI app...")
app = FastAPI(title="Gradual Test API")
print("✓ App created")

print("\nStep 2: Adding health routes...")
try:
    from api.routes import health
    app.include_router(health.router, prefix="/api", tags=["health"])
    print("✓ Health routes added")
except Exception as e:
    print(f"✗ Failed to add health routes: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 3: Adding config routes...")
try:
    from api.routes import config
    app.include_router(config.router, prefix="/api", tags=["config"])
    print("✓ Config routes added")
except Exception as e:
    print(f"✗ Failed to add config routes: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 4: Adding chat routes...")
try:
    from api.routes import chat
    app.include_router(chat.router, prefix="/api", tags=["chat"])
    print("✓ Chat routes added")
except Exception as e:
    print(f"✗ Failed to add chat routes: {e}")
    import traceback
    traceback.print_exc()

@app.get("/")
def root():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    print("\nStarting server on http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)