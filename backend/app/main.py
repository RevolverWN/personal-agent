"""Main application entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1 import auth, chat, agent as agent_config, files, memory, agents, skills, mcp, models as model_api
from app.core.exceptions import setup_exception_handlers
from app.models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="A personal AI agent with multi-model support",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(agent_config.router, prefix="/api/v1/agent", tags=["agent_config"])
    app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
    app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(skills.router, prefix="/api/v1/skills", tags=["skills"])
    app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["mcp"])
    app.include_router(model_api.router, prefix="/api/v1/models", tags=["models"])
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "name": settings.APP_NAME,
        }
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to Personal Agent API",
            "version": settings.APP_VERSION,
            "docs_url": "/docs",
        }
    
    return app


app = create_application()


def main():
    """Entry point for the application."""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
