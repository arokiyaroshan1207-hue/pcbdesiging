"""Health check and system status API endpoints."""

import sys
import platform
from datetime import datetime, timezone
from fastapi import APIRouter, status

from app.schemas.health import HealthResponse
from app.services.detector import detector_service

router = APIRouter(prefix="/api", tags=["System Health"])

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Backend Health & Model Status Check",
    description="Check backend operational status, host environment, and whether the YOLOv8 model weights exist.",
)
async def check_health() -> HealthResponse:
    """Returns backend health status, timestamp, and model readiness info."""
    model_status = detector_service.get_status_summary()
    
    return HealthResponse(
        status="healthy",
        service="PCB Defect Detection API",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_loaded=model_status["model_loaded"],
        model_file_exists=model_status["model_file_exists"],
        model_path=model_status["model_path"],
        model_status_message=model_status["status_message"],
        supported_defect_classes=model_status["classes"],
        system_info={
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
            "machine": platform.machine(),
        },
    )
