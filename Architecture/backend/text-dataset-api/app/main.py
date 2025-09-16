"""
Main FastAPI application entry point
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware
import redis.asyncio as redis
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db, close_db
from app.api.v1.api import api_router
from app.api.websocket.manager import WebSocketManager
from app.services.monitoring.metrics import metrics_middleware, PrometheusMetrics
from app.services.monitoring.health import health_check_router
from app.utils.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    LoggingMiddleware,
    CompressionMiddleware,
)
from app.utils.exceptions import (
    custom_http_exception_handler,
    custom_validation_exception_handler,
    general_exception_handler,
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize WebSocket manager and metrics
websocket_manager = WebSocketManager()
metrics = PrometheusMetrics()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    logger.info("🚀 Starting Text Dataset API...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Initialize Redis connection
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30,
        )
        
        # Test Redis connection
        await redis_client.ping()
        app.state.redis = redis_client
        logger.info("✅ Redis connection established")
        
        # Initialize WebSocket manager
        app.state.websocket_manager = websocket_manager
        logger.info("✅ WebSocket manager initialized")
        
        # Initialize metrics
        app.state.metrics = metrics
        logger.info("✅ Metrics system initialized")
        
        logger.info("🎉 Application startup complete!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down application...")
        
        # Close Redis connection
        if hasattr(app.state, 'redis'):
            await app.state.redis.close()
            logger.info("✅ Redis connection closed")
        
        # Close database connections
        await close_db()
        logger.info("✅ Database connections closed")
        
        # Close WebSocket connections
        await websocket_manager.disconnect_all()
        logger.info("✅ WebSocket connections closed")
        
        logger.info("👋 Application shutdown complete")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI-powered text-to-dataset platform with real-time processing and analytics",
        version=settings.PROJECT_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
        debug=settings.DEBUG,
    )
    
    # Add middleware (order matters - added in reverse order of execution)
    
    # Security headers middleware (executed last)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Compression middleware
    app.add_middleware(CompressionMiddleware)
    
    # Logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.RATE_LIMIT_CALLS,
        period=settings.RATE_LIMIT_PERIOD,
    )
    
    # Session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        max_age=settings.SESSION_MAX_AGE,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
    )
    
    # Trusted host middleware
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )
    
    # Metrics middleware (executed first)
    app.add_middleware(metrics_middleware, metrics=metrics)
    
    return app


# Create application instance
app = create_application()

# Add routers
app.include_router(health_check_router, prefix="/health", tags=["health"])
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add WebSocket routes
from app.api.websocket.routes import websocket_router
app.include_router(websocket_router)

# Add exception handlers
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.ENVIRONMENT != "production" else "Documentation disabled in production",
        "health": "/health/status",
        "websocket": "/ws",
    }


@app.get("/info", tags=["root"])
async def info() -> dict:
    """Application information endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "description": "AI-powered text-to-dataset platform",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "api_version": "v1",
        "features": {
            "authentication": True,
            "document_processing": True,
            "real_time_updates": True,
            "analytics": True,
            "chat_assistant": True,
            "aws_integration": True,
        },
        "limits": {
            "max_file_size": settings.MAX_FILE_SIZE,
            "max_files_per_upload": settings.MAX_FILES_PER_UPLOAD,
            "rate_limit": f"{settings.RATE_LIMIT_CALLS} calls per {settings.RATE_LIMIT_PERIOD} seconds",
        },
    }


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header to responses"""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    """Add request ID header to responses"""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Development server configuration
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
        server_header=False,
        date_header=False,
        workers=1 if settings.DEBUG else settings.WORKERS,
    )