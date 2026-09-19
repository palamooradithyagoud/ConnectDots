from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine, Base
from app.db import base  # Ensures all models are registered

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crime_analysis_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database extensions and tables on startup."""
    logger.info("Initializing database and spatial extensions...")
    try:
        # If Postgres, ensure PostGIS extension is available
        if "postgres" in settings.DATABASE_URL:
            with engine.connect() as conn:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                    conn.commit()
                    logger.info("PostGIS extension verified.")
                except Exception as e:
                    logger.warning(f"Could not auto-create PostGIS extension (might already exist or need superuser): {e}")

        # Create all tables if they do not already exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database startup initialization: {e}")

    yield

    logger.info("Shutting down AI Crime Analysis Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.exception(f"Unhandled server error: {exc}")
    from fastapi.responses import JSONResponse
    origin = request.headers.get("origin") or "*"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/", tags=["Root"])
def root():
    return {
        "system": settings.PROJECT_NAME,
        "phase": "Phase 4: Knowledge Graph + Graph RAG + LLM Investigation Intelligence",
        "documentation": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
