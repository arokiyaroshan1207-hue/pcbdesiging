"""Schemas for PCB defect detection results and metrics."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    """Bounding box pixel coordinates in image coordinate space."""
    x1: float = Field(..., description="Top-left X coordinate")
    y1: float = Field(..., description="Top-left Y coordinate")
    x2: float = Field(..., description="Bottom-right X coordinate")
    y2: float = Field(..., description="Bottom-right Y coordinate")
    width: float = Field(..., description="Bounding box width")
    height: float = Field(..., description="Bounding box height")

class DefectDetection(BaseModel):
    """Single detected PCB defect occurrence."""
    defect_id: int = Field(..., description="1-indexed defect sequence identifier")
    class_id: int = Field(..., description="Zero-indexed numeric class ID from model")
    class_name: str = Field(..., description="Model label (e.g. 'Mouse Bite')")
    standard_class: str = Field(..., description="Normalized snake_case class (e.g. 'mouse_bite')")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    confidence_percentage: float = Field(..., description="Confidence formatted as percentage (0-100)")
    bbox: BoundingBox = Field(..., description="Bounding box coordinates")

class DefectSummary(BaseModel):
    """Aggregated defect statistics and inspection outcome."""
    total_defects: int = Field(..., description="Total defect count found on the PCB")
    defects_by_class: Dict[str, int] = Field(..., description="Defect breakdown counts mapped by class name")
    max_confidence: Optional[float] = Field(None, description="Highest confidence detected")
    average_confidence: Optional[float] = Field(None, description="Average confidence score across all defects")
    status: str = Field(..., description="'DEFECT_FREE' or 'DEFECTIVE'")
    pass_inspection: bool = Field(..., description="True if no defects detected, False otherwise")

class InspectionResult(BaseModel):
    """Comprehensive inspection report payload returned to client."""
    inspection_id: str = Field(..., description="Unique inspection transaction UUID")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    original_filename: str = Field(..., description="Original name of uploaded PCB image")
    image_width: int = Field(..., description="Input image width in pixels")
    image_height: int = Field(..., description="Input image height in pixels")
    annotated_image_filename: str = Field(..., description="Filename of stored annotated image in results/")
    annotated_image_url: str = Field(..., description="Usable relative URL for fetching annotated image")
    raw_image_filename: Optional[str] = Field(None, description="Storage filename of raw uploaded image in uploads/")
    inference_time_ms: float = Field(..., description="Execution time of YOLOv8 inference in milliseconds")
    detections: List[DefectDetection] = Field(..., description="List of detected defect instances")
    summary: DefectSummary = Field(..., description="Aggregated inspection metrics")
