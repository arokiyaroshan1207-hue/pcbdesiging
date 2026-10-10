"""Unit and integration tests for Phase 6: PDF Report Generation Service."""

import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import SAMPLE_IMAGES_DIR, RESULTS_DIR, REPORTS_DIR
from app.services.pdf_generator import create_inspection_pdf, generate_inspection_observations

SAMPLE_DEFECT_RESULT = {
    "inspection_id": "test_pdf_qa_999",
    "timestamp": "2026-10-11T00:30:00Z",
    "original_filename": "pcb1.jpg",
    "image_width": 3056,
    "image_height": 2464,
    "annotated_image_filename": "sample_annotated.jpg",
    "inference_time_ms": 115.4,
    "detections": [
        {
            "defect_id": 1,
            "class_id": 2,
            "class_name": "Mouse Bite",
            "standard_class": "mouse_bite",
            "confidence": 0.4222,
            "confidence_percentage": 42.22,
            "bbox": {"x1": 2847.1, "y1": 1616.4, "x2": 2975.1, "y2": 1737.8, "width": 128.0, "height": 121.4},
        },
        {
            "defect_id": 2,
            "class_id": 1,
            "class_name": "Short Circuit",
            "standard_class": "short",
            "confidence": 0.3525,
            "confidence_percentage": 35.25,
            "bbox": {"x1": 1500.0, "y1": 1200.0, "x2": 1550.0, "y2": 1250.0, "width": 50.0, "height": 50.0},
        },
    ],
    "summary": {
        "total_defects": 2,
        "defects_by_class": {"Mouse Bite": 1, "Short Circuit": 1},
        "max_confidence": 0.4222,
        "average_confidence": 0.3874,
        "status": "DEFECTIVE",
        "pass_inspection": False,
    },
}

SAMPLE_CLEAN_RESULT = {
    "inspection_id": "test_clean_qa_000",
    "timestamp": "2026-10-11T00:35:00Z",
    "original_filename": "pcb_clean.jpg",
    "image_width": 2048,
    "image_height": 1536,
    "annotated_image_filename": "clean_annotated.jpg",
    "inference_time_ms": 95.2,
    "detections": [],
    "summary": {
        "total_defects": 0,
        "defects_by_class": {},
        "max_confidence": None,
        "average_confidence": None,
        "status": "DEFECTIVE_FREE",
        "pass_inspection": True,
    },
}

def test_observation_text_generation():
    """Verify observations reflect true defect statistics."""
    defect_obs = generate_inspection_observations(SAMPLE_DEFECT_RESULT["summary"], 2)
    assert "DEFECT ADVISORY" in defect_obs
    assert "Short Circuit" in defect_obs
    assert "Mouse Bite" in defect_obs
    assert "NON-COMPLIANT" in defect_obs

    clean_obs = generate_inspection_observations(SAMPLE_CLEAN_RESULT["summary"], 0)
    assert "COMPLIANCE DETERMINATION" in clean_obs
    assert "IPC-A-600 Class 3" in clean_obs
    assert "Approved" in clean_obs

def test_generate_pdf_file_creation():
    """Verify create_inspection_pdf generates a valid, properly sized PDF file."""
    sample_img = SAMPLE_IMAGES_DIR / "pcb1.jpg"

    pdf_path = create_inspection_pdf(
        inspection_data=SAMPLE_DEFECT_RESULT,
        original_image_path=sample_img if sample_img.is_file() else None,
        annotated_image_path=sample_img if sample_img.is_file() else None,
    )

    assert pdf_path.exists()
    assert pdf_path.is_file()
    assert pdf_path.stat().st_size > 5000, "PDF output is suspiciously small"

    # Verify standard PDF header bytes
    content = pdf_path.read_bytes()
    assert content.startswith(b"%PDF-"), "Generated file does not have valid PDF magic bytes"

def test_generate_pdf_with_zero_defects():
    """Verify PDF generator handles 0-defect PCB without crashing."""
    pdf_path = create_inspection_pdf(
        inspection_data=SAMPLE_CLEAN_RESULT,
        original_image_path=None,
        annotated_image_path=None,
    )

    assert pdf_path.exists()
    content = pdf_path.read_bytes()
    assert content.startswith(b"%PDF-")

@pytest.mark.anyio
async def test_api_generate_pdf_endpoint():
    """Integration test: POST /api/reports/generate-pdf returns valid PDF stream."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/reports/generate-pdf",
            json=SAMPLE_DEFECT_RESULT,
            timeout=20.0
        )

        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert "attachment" in response.headers.get("content-disposition", "")
        assert response.content.startswith(b"%PDF-")
        assert len(response.content) > 5000

@pytest.mark.anyio
async def test_api_download_pdf_by_id_endpoint():
    """Integration test: GET /api/reports/{id}/pdf retrieves compiled report."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Pre-generate report
        await client.post("/api/reports/generate-pdf", json=SAMPLE_DEFECT_RESULT)

        # Download by ID
        response = await client.get("/api/reports/test_pdf_qa_999/pdf")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert response.content.startswith(b"%PDF-")
