"""Unit tests for the Health Check and Root API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.anyio
async def test_root_endpoint():
    """Verify root endpoint returns operational info and docs links."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "health_check" in data
        assert "documentation" in data

@pytest.mark.anyio
async def test_health_endpoint():
    """Verify GET /api/health returns 200 with required schema fields."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "model_loaded" in data
        assert "model_file_exists" in data
        assert "model_path" in data
        assert "model_status_message" in data
        assert "system_info" in data
        assert "python_version" in data["system_info"]
        assert isinstance(data["model_file_exists"], bool)

@pytest.mark.anyio
async def test_cors_headers():
    """Verify CORS headers are returned for allowed origins."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health", headers={"Origin": "http://localhost:5173"})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
