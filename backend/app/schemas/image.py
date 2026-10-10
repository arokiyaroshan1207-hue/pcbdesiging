"""Schemas for image uploads and validation."""

from typing import Optional
from pydantic import BaseModel, Field

class ImageValidationResponse(BaseModel):
    """Schema returned when an uploaded image is validated."""
    valid: bool = Field(..., description="Whether the uploaded file is a valid image")
    filename: str = Field(..., description="Original filename")
    saved_filename: Optional[str] = Field(None, description="Assigned stored filename in uploads/")
    format: Optional[str] = Field(None, description="Image format (e.g. JPEG, PNG)")
    width: Optional[int] = Field(None, description="Width in pixels")
    height: Optional[int] = Field(None, description="Height in pixels")
    size_bytes: int = Field(..., description="File size in bytes")
    message: str = Field(..., description="Validation summary message")

class ErrorResponse(BaseModel):
    """Standardized API error response format."""
    status: str = Field(default="error", description="Error status indicator")
    detail: str = Field(..., description="Human-readable error description")
    error_code: Optional[str] = Field(None, description="Machine-readable error classification")
