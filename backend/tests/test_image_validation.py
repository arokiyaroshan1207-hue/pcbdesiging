"""Unit tests for Image Upload Validation and Detection Safety."""

import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import SAMPLE_IMAGES_DIR

@pytest.mark.anyio
async def test_validate_image_with_sample_pcb():
    """Verify that uploading a genuine PCB sample passes validation."""
    sample_file = SAMPLE_IMAGES_DIR / "pcb1.jpg"
    assert sample_file.exists(), f"Sample test image {sample_file} not found"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sample_file, "rb") as f:
            files = {"file": ("pcb1.jpg", f, "image/jpeg")}
            response = await client.post("/api/validate-image", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["filename"] == "pcb1.jpg"
        assert data["format"] == "JPEG"
        assert data["width"] > 0
        assert data["height"] > 0
        assert data["size_bytes"] > 0

@pytest.mark.anyio
async def test_validate_image_rejects_non_image():
    """Verify that uploading a text file or invalid extension is rejected with HTTP 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_file = b"This is plain text pretending to be an image."
        files = {"file": ("malicious.txt", fake_file, "text/plain")}
        response = await client.post("/api/validate-image", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file extension" in data["detail"]

@pytest.mark.anyio
async def test_validate_image_rejects_empty_file():
    """Verify that uploading an empty file is rejected with HTTP 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("empty.jpg", b"", "image/jpeg")}
        response = await client.post("/api/validate-image", files=files)

        assert response.status_code == 400
        assert "empty (0 bytes)" in response.json()["detail"]

@pytest.mark.anyio
async def test_detect_endpoint_safety_when_model_missing(monkeypatch):
    """Verify that detect endpoint does NOT return fake results when model weights are missing."""
    # Temporarily point model to a non-existent file to simulate missing model
    from app.services.detector import detector_service
    monkeypatch.setattr(detector_service, "model_path", Path("missing/weights/best.pt"))

    sample_file = SAMPLE_IMAGES_DIR / "pcb1.jpg"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sample_file, "rb") as f:
            files = {"file": ("pcb1.jpg", f, "image/jpeg")}
            response = await client.post("/api/detect", files=files)

        # Must return 503 Service Unavailable rather than fake detections
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error"] == "ModelNotFound"

@pytest.mark.anyio
async def test_path_traversal_prevention_on_results():
    """Verify that requesting path traversal in results endpoint is rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/results/../../windows/system32/cmd.exe")
        # Should return 400 or 404, never 200 or allow path traversal
        assert response.status_code in [400, 404]
