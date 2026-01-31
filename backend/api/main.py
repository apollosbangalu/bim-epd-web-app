"""
FastAPI Main Application - BIM-EPD Graph RAG Web Application
"""
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from api.routes import chat, config, health
from core.config import settings
from core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle management for FastAPI application
    """
    # Startup
    logger.info("Starting BIM-EPD Graph RAG Application")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"GraphDB URL: {settings.graphdb_url}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BIM-EPD Graph RAG Application")


# Create FastAPI application
app = FastAPI(
    title="BIM-EPD Graph RAG API",
    description="Building Material and LCA Product Data Material Recommendation Platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(config.router, prefix="/api", tags=["config"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BIM-EPD Graph RAG API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )