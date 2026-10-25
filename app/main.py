"""Students Database CRUD Application.

FastAPI main application entry point.
"""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator, Dict

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers.students import router as students_router

# Configure sanitized logging (exclude PII from logs)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("students_app")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Execute startup and shutdown lifecycle events."""
    # Ensure database table and indexes exist on startup
    init_db()
    yield


app = FastAPI(
    title="Students Database CRUD Application",
    description="A clean, dependable backend REST API to store and manage student records.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled errors, log safe diagnostic information, and return generic 500."""
    logger.error("Unhandled error processing request: %s %s (%s)", request.method, request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Include Students Router
app.include_router(students_router)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns service health status without touching the database.",
    status_code=200,
)
def health_check() -> Dict[str, str]:
    """Return health status."""
    return {"status": "ok"}
