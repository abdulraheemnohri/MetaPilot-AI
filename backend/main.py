"""
MetaPilot AI - Main Application Entry Point

FastAPI application with all routers, middleware, and configuration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn

from .config import settings, get_settings
from .database.connection import init_db, close_db
from .api import ai_router, auth_router
from .api import admin_router
from .api import knowledge_router, export_router
from .providers.registry import provider_registry
from .api.auth_router import get_current_user

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize providers
    await provider_registry.initialize()
    logger.info(f"Initialized {len(provider_registry.providers)} AI providers")
    
    logger.info(f"Server running on http://{settings.HOST}:{settings.PORT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_db()
    await provider_registry.shutdown()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    MetaPilot AI - Multi-AI Orchestrator
    
    Combine results from multiple AI providers (OpenAI, Anthropic, Mistral, Google, Perplexity, Local GGUF)
    to get the best possible answer for any query.
    
    Features:
    - Multi-provider AI inference
    - Intelligent response merging
    - Conversation memory
    - Document processing
    - Knowledge base integration
    - Task scheduling
    - Rate limiting
    - JWT Authentication
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Include API routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(ai_router, prefix="/api/ai", tags=["AI"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["Admin"])
app.include_router(knowledge_router.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(export_router.router, prefix="/api/export", tags=["Export"])


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler."""
    logger.error(f"HTTP Error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


# Global exception handler for other exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Server Error: {type(exc).__name__} - {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if settings.DEBUG else None,
        },
    )


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }


# Config endpoint (debug only)
@app.get("/api/config")
async def get_config(current_user: dict = Depends(get_current_user)):
    """Get application configuration (debug only)."""
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Config endpoint disabled in production")
    
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "database_url": settings.DATABASE_URL,
        "cors_origins": settings.CORS_ORIGINS,
    }


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Run server (for development)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )