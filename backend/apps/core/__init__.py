"""Core application module for Farda MCP."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.connectors import router as connectors_router

from .auth import router as auth_router
from .config import settings
from .routers import health


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.APP_ENV != "prod" else None,
        redoc_url="/redoc" if settings.APP_ENV != "prod" else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, tags=["health"])
    app.include_router(auth_router)
    app.include_router(connectors_router.router, prefix="/api")

    # MCP Manager routers
    from apps.mcp.router import mcp_router, policies_router, tools_router

    app.include_router(tools_router, prefix="/api")
    app.include_router(mcp_router, prefix="/api")
    app.include_router(policies_router, prefix="/api")

    return app


app = create_app()
