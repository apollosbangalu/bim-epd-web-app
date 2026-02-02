#!/usr/bin/env python3
"""Minimal FastAPI to test if server starts"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Minimal Test API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "Minimal API works"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("Starting minimal FastAPI on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)