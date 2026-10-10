"""PDF Inspection Report API endpoints."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Body
from fastapi.responses import FileResponse

from app.config import REPORTS_DIR, RESULTS_DIR, UPLOAD_DIR, SAMPLE_IMAGES_DIR
from app.services.pdf_generator import create_inspection_pdf

logger = logging.getLogger("pcb_defect_detection.reports_routes")
router = APIRouter(prefix="/api/reports", tags=["Inspection Reports"])

@router.post(
    "/generate-pdf",
    summary="Generate Downloadable PDF Inspection Report",
    description="Generate an industrial PDF quality report containing original and annotated PCB images, defect metrics, and engineering observations.",
)
async def generate_pdf_report(inspection_data: Dict[str, Any] = Body(...)):
    """Generate and return a downloadable PDF inspection certificate."""
    inspection_id = inspection_data.get("inspection_id")
    if not inspection_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing inspection_id in report payload."
        )

    # 1. Resolve original image path if available on disk
    raw_filename = inspection_data.get("raw_image_filename")
    orig_filename = inspection_data.get("original_filename")
    original_path: Optional[Path] = None

    if raw_filename and (UPLOAD_DIR / Path(raw_filename).name).is_file():
        original_path = UPLOAD_DIR / Path(raw_filename).name
    elif orig_filename:
        # Check uploads, sample_images
        possible_paths = [
            UPLOAD_DIR / Path(orig_filename).name,
            SAMPLE_IMAGES_DIR / Path(orig_filename).name,
        ]
        for p in possible_paths:
            if p.is_file():
                original_path = p
                break

    # If original image is not directly found by name, look up latest matching upload
    if not original_path:
        upload_files = list(UPLOAD_DIR.glob("*.jpg")) + list(UPLOAD_DIR.glob("*.png"))
        if upload_files:
            original_path = sorted(upload_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]

    # 2. Resolve annotated image path
    ann_filename = inspection_data.get("annotated_image_filename")
    annotated_path: Optional[Path] = None
    if ann_filename:
        target = RESULTS_DIR / Path(ann_filename).name
        if target.is_file():
            annotated_path = target

    # 3. Generate PDF
    try:
        pdf_path = create_inspection_pdf(
            inspection_data=inspection_data,
            original_image_path=original_path,
            annotated_image_path=annotated_path,
        )

        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=pdf_path.name,
            headers={
                "Content-Disposition": f'attachment; filename="{pdf_path.name}"'
            }
        )

    except Exception as e:
        logger.exception(f"Failed to generate inspection PDF for ID {inspection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation error: {str(e)}"
        )

@router.get(
    "/{inspection_id}/pdf",
    summary="Download Generated PDF by Inspection ID",
    description="Retrieve previously compiled PDF report by its transaction UUID.",
)
async def download_pdf_by_id(inspection_id: str):
    """Retrieve pre-compiled PDF report."""
    clean_id = Path(inspection_id).name
    pdf_path = REPORTS_DIR / f"Inspection_Report_{clean_id}.pdf"

    if not pdf_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report for inspection ID '{clean_id}' was not found. Please generate it first."
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
        headers={
            "Content-Disposition": f'attachment; filename="{pdf_path.name}"'
        }
    )
