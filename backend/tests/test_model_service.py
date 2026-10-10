"""Comprehensive unit and integration tests for Phase 3: YOLOv8 Model Service."""

import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import SAMPLE_IMAGES_DIR, RESULTS_DIR, MODELS_DIR
from app.services.detector import PCBDetectorService, detector_service, EXPECTED_DEFECT_CLASSES

# --------------------------------------------------------------------------
# 1. Tests that DO NOT require model weights
# --------------------------------------------------------------------------

def test_missing_model_raises_file_not_found(tmp_path: Path):
    """Verify that a non-existent model path raises FileNotFoundError with setup guidance."""
    fake_path = tmp_path / "missing_model.pt"
    service = PCBDetectorService(model_path=fake_path)

    assert service.model_file_exists is False
    assert service.is_loaded is False

    status = service.get_status_summary()
    assert status["model_file_exists"] is False
    assert status["model_loaded"] is False
    assert "Setup instruction" in status["status_message"]

    with pytest.raises(FileNotFoundError) as exc_info:
        service.load_model()
    assert "Setup instruction" in str(exc_info.value)

def test_corrupted_model_file_handled_gracefully(tmp_path: Path):
    """Verify that a corrupt or truncated weights file raises RuntimeError and does not crash service."""
    corrupt_file = tmp_path / "corrupt.pt"
    corrupt_file.write_bytes(b"NOT_A_VALID_PYTORCH_WEIGHTS_FILE")

    service = PCBDetectorService(model_path=corrupt_file)
    assert service.model_file_exists is True

    with pytest.raises(RuntimeError):
        service.load_model()

    assert service.is_loaded is False
    status = service.get_status_summary()
    assert status["model_loaded"] is False

def test_inference_rejects_missing_image(tmp_path: Path):
    """Verify that attempting inference on a non-existent image path raises FileNotFoundError."""
    service = PCBDetectorService()
    non_existent_image = tmp_path / "ghost_pcb.jpg"

    with pytest.raises(FileNotFoundError):
        service.detect(non_existent_image)


# --------------------------------------------------------------------------
# 2. Tests requiring model weights (best.pt)
# --------------------------------------------------------------------------

def test_weights_exist_and_are_non_empty():
    """Verify backend/models/best.pt exists and has valid size."""
    weights_path = MODELS_DIR / "best.pt"
    assert weights_path.exists(), f"Model weights {weights_path} not found"
    assert weights_path.stat().st_size > 1_000_000, "Model weights file is unexpectedly small (<1MB)"

def test_model_loads_and_inspects_classes():
    """Verify YOLOv8 loads once and inspects actual class metadata matching PCB defects."""
    model = detector_service.load_model()
    assert model is not None
    assert detector_service.is_loaded is True

    # Retrieve supported classes directly from model metadata
    classes = detector_service.get_supported_classes()
    assert len(classes) == 6, f"Expected 6 defect classes, got {len(classes)}: {classes}"

    # Verify semantic taxonomy mapping
    matches_taxonomy, details = detector_service.verify_class_taxonomy()
    assert matches_taxonomy is True, f"Model classes did not match expected taxonomy: {details}"
    assert set(details["expected_classes"]) == EXPECTED_DEFECT_CLASSES

def test_real_inference_on_sample_pcb():
    """Execute live YOLOv8 inference on a sample PCB image and verify detections."""
    sample_img = SAMPLE_IMAGES_DIR / "pcb1.jpg"
    assert sample_img.exists(), f"Sample image {sample_img} missing"

    result = detector_service.detect(sample_img, conf_threshold=0.25)

    assert result.inspection_id is not None
    assert result.image_width > 0
    assert result.image_height > 0
    assert result.inference_time_ms > 0

    # Verify detections
    assert len(result.detections) > 0, "Expected at least 1 defect on pcb1.jpg"
    for d in result.detections:
        assert d.confidence >= 0.25
        assert d.bbox.width > 0
        assert d.bbox.height > 0
        assert d.standard_class in EXPECTED_DEFECT_CLASSES

    # Verify summary
    assert result.summary.total_defects == len(result.detections)
    assert result.summary.status == "DEFECTIVE"
    assert result.summary.pass_inspection is False
    assert result.summary.average_confidence is not None

    # Verify annotated result image exists and is non-empty
    annotated_path = RESULTS_DIR / result.annotated_image_filename
    assert annotated_path.exists()
    assert annotated_path.stat().st_size > 0

def test_zero_detections_handling_clean():
    """Verify that inference handling with zero detections returns DEFECT_FREE status without crashing."""
    sample_img = SAMPLE_IMAGES_DIR / "pcb1.jpg"
    # An extreme threshold of 0.999 will yield 0 detections
    result = detector_service.detect(sample_img, conf_threshold=0.999)

    assert result.summary.total_defects == 0
    assert result.summary.status == "DEFECT_FREE"
    assert result.summary.pass_inspection is True
    assert result.summary.average_confidence is None
    assert len(result.detections) == 0

    # Ensure clean result image is still produced
    annotated_path = RESULTS_DIR / result.annotated_image_filename
    assert annotated_path.exists()
    assert annotated_path.stat().st_size > 0

@pytest.mark.anyio
async def test_detect_endpoint_live_api_integration():
    """End-to-end integration test: POST /api/detect with sample image, then fetch result image."""
    sample_img = SAMPLE_IMAGES_DIR / "pcb1.jpg"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sample_img, "rb") as f:
            files = {"file": ("pcb1.jpg", f, "image/jpeg")}
            response = await client.post("/api/detect?conf_threshold=0.25", files=files)

        assert response.status_code == 200
        data = response.json()

        assert "inspection_id" in data
        assert "detections" in data
        assert len(data["detections"]) > 0
        assert "summary" in data
        assert data["summary"]["total_defects"] > 0
        assert data["summary"]["status"] == "DEFECTIVE"
        assert "annotated_image_url" in data

        # Test retrieving the generated annotated image via GET /api/results/{filename}
        annotated_filename = data["annotated_image_filename"]
        img_res = await client.get(f"/api/results/{annotated_filename}")
        assert img_res.status_code == 200
        assert img_res.headers.get("content-type") == "image/jpeg"
        assert len(img_res.content) > 0
