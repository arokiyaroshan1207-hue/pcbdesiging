"""PCB Image upload, validation, and detection route endpoints."""

import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Query, HTTPException, status
from fastapi.responses import FileResponse

from app.services.image_service import ImageService
from app.services.detector import detector_service
from app.schemas.image import ImageValidationResponse
from app.schemas.detection import InspectionResult

logger = logging.getLogger("pcb_defect_detection.inspection_routes")
router = APIRouter(prefix="/api", tags=["PCB Inspection"])

@router.post(
    "/validate-image",
    response_model=ImageValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate Uploaded PCB Image",
    description="Validate image size, extension, dimensions, and integrity without running inference.",
)
async def validate_image(file: UploadFile = File(...)) -> ImageValidationResponse:
    """Validate uploaded PCB image integrity and format."""
    saved_path, original_filename, (width, height), img_format = (
        await ImageService.validate_and_save_upload(file)
    )
    file_size = saved_path.stat().st_size

    return ImageValidationResponse(
        valid=True,
        filename=original_filename,
        saved_filename=saved_path.name,
        format=img_format,
        width=width,
        height=height,
        size_bytes=file_size,
        message="PCB image validated successfully and stored for inspection.",
    )

@router.post(
    "/detect",
    response_model=InspectionResult,
    status_code=status.HTTP_200_OK,
    summary="Detect PCB Defects",
    description="Upload a PCB image and execute YOLOv8 defect detection with bounding boxes and defect metrics.",
)
async def detect_defects(
    file: UploadFile = File(...),
    conf_threshold: float = Query(
        default=0.25,
        ge=0.01,
        le=1.0,
        description="Confidence threshold for defect detection (0.01 to 1.0)",
    ),
    iou_threshold: float = Query(
        default=0.45,
        ge=0.01,
        le=1.0,
        description="Non-Maximum Suppression (IoU) threshold",
    ),
) -> InspectionResult:
    """Accepts a PCB image, validates it, and runs YOLOv8 inference."""
    # Step 1: Validate and save uploaded file
    saved_path, original_filename, (width, height), img_format = (
        await ImageService.validate_and_save_upload(file)
    )

    # Step 2: Verify model file presence before running inference
    if not detector_service.model_file_exists:
        model_status = detector_service.get_status_summary()
        logger.error(f"Detection rejected: {model_status['status_message']}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ModelNotFound",
                "message": model_status["status_message"],
                "model_path": model_status["model_path"],
                "model_file_exists": False,
            },
        )

    # Step 3: Run YOLOv8 inference
    try:
        inspection_result = detector_service.detect(
            image_path=saved_path,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
        )
        # Update original filename to user's uploaded name and retain saved raw image filename
        inspection_result.original_filename = original_filename
        inspection_result.raw_image_filename = saved_path.name
        return inspection_result

    except FileNotFoundError as fnf_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "ModelUnavailable", "message": str(fnf_err)},
        )
    except Exception as infer_err:
        logger.exception(f"Inference failure on '{saved_path}': {infer_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InferenceError", "message": str(infer_err)},
        )

@router.get(
    "/results/{filename}",
    summary="Serve Annotated Result Image",
    description="Securely serve an annotated PCB detection image by filename.",
)
async def get_result_image(filename: str):
    """Retrieve and stream an annotated result image securely."""
    image_path = ImageService.get_result_image_path(filename)

    ext = image_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(image_path),
        media_type=media_type,
        filename=image_path.name,
    )

@router.get(
    "/sample-images",
    summary="List Available Sample PCB Images",
    description="List filenames of bundled test PCB samples for testing inspection.",
)
async def list_sample_images():
    """Returns list of bundled sample test PCB images."""
    from app.config import SAMPLE_IMAGES_DIR
    if not SAMPLE_IMAGES_DIR.exists():
        return {"samples": []}
    files = sorted([f.name for f in SAMPLE_IMAGES_DIR.glob("*.*") if f.suffix.lower() in [".jpg", ".png", ".jpeg"]])
    return {"samples": files}

@router.get(
    "/sample-images/{filename}",
    summary="Fetch Sample PCB Image",
    description="Retrieve a bundled test PCB image by filename.",
)
async def get_sample_image(filename: str):
    """Serve a sample PCB image file securely."""
    from app.config import SAMPLE_IMAGES_DIR
    clean_name = Path(filename).name
    target = (SAMPLE_IMAGES_DIR / clean_name).resolve()
    try:
        target.relative_to(SAMPLE_IMAGES_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sample image path.")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample image not found.")

    ext = target.suffix.lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"
    return FileResponse(path=str(target), media_type=media_type, filename=target.name)

