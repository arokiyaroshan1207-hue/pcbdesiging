"""Health check schema definitions."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    """Schema for GET /api/health response."""
    status: str = Field(..., description="Overall backend operational status (e.g. 'healthy')")
    service: str = Field(default="PCB Defect Detection API", description="Service identifier")
    version: str = Field(default="1.0.0", description="API version")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    model_loaded: bool = Field(..., description="Flag indicating whether YOLOv8 model is loaded in memory")
    model_file_exists: bool = Field(..., description="Flag indicating whether model weights exist on disk")
    model_path: str = Field(..., description="Absolute path to the configured model file")
    model_status_message: str = Field(..., description="Diagnostic model status or setup instruction")
    supported_defect_classes: Optional[list[str]] = Field(
        default=None,
        description="Defect classes loaded from model metadata, or None if model not yet loaded"
    )
    system_info: Dict[str, Any] = Field(..., description="Host environment diagnostics")
