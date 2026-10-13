"""Main FastAPI Application Entrypoint.

Configures application lifecycle, CORS middleware, API routers,
error handlers, and operational logging.
"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import ALLOWED_ORIGINS, UPLOAD_DIR, RESULTS_DIR, MODELS_DIR
from app.routes.health import router as health_router
from app.routes.inspection import router as inspection_router
from app.routes.reports import router as reports_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pcb_defect_detection")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle manager."""
    logger.info("=" * 60)
    logger.info("Starting AI-Powered PCB Defect Detection API Server")
    logger.info(f"Uploads Directory: {UPLOAD_DIR}")
    logger.info(f"Results Directory: {RESULTS_DIR}")
    logger.info(f"Models Directory : {MODELS_DIR}")
    logger.info("=" * 60)
    # Pre-warm AI model during container boot so incoming user requests face zero cold start
    try:
        from app.services.detector import detector_service
        if detector_service.model_file_exists:
            detector_service.warmup()
            logger.info("YOLOv8 defect detector preloaded and ready.")
        else:
            logger.warning("YOLOv8 weights file not found on disk at startup.")
    except Exception as warmup_err:
        logger.warning(f"Engine warm-up skipped on startup: {warmup_err}")
    yield
    logger.info("Stopping PCB Defect Detection API Server - Cleanup completed")

# Initialize FastAPI application
app = FastAPI(
    title="AI-Powered PCB Defect Detection API",
    description="Industrial Printed Circuit Board defect detection service utilizing YOLOv8 and computer vision.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS) for Vite frontend and Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(health_router)
app.include_router(inspection_router)
app.include_router(reports_router)

from fastapi.responses import JSONResponse, RedirectResponse

@app.get("/docs", include_in_schema=False)
async def redirect_docs():
    """Redirect standard /docs to /api/docs."""
    return RedirectResponse(url="/api/docs")

@app.get("/", tags=["Root"])
async def root():
    """Root entrypoint providing service status and quick documentation links."""
    return {
        "service": "AI-Powered PCB Defect Detection API",
        "status": "online",
        "documentation": "/api/docs",
        "health_check": "/api/health",
        "version": "1.0.0",
    }

# Centralized error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic and request parameter validation failures."""
    logger.warning(f"Request validation failure on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_code": "VALIDATION_ERROR",
            "detail": exc.errors(),
        },
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled exception handler to ensure consistent error format."""
    logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "detail": "An internal server error occurred. Please consult the backend logs.",
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
