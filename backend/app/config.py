"""Configuration settings for the PCB Defect Detection Backend."""

import os
from pathlib import Path

# Base backend directory: .../PCB-DEFECT-DETECTION/backend
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Storage and model directories
UPLOAD_DIR = BACKEND_DIR / "uploads"
RESULTS_DIR = BACKEND_DIR / "results"
REPORTS_DIR = BACKEND_DIR / "reports"
MODELS_DIR = BACKEND_DIR / "models"
SAMPLE_IMAGES_DIR = BACKEND_DIR / "sample_images"

# Model weights configuration
DEFAULT_MODEL_FILENAME = "best.pt"
MODEL_PATH = Path(os.getenv("PCB_MODEL_PATH", str(MODELS_DIR / DEFAULT_MODEL_FILENAME)))

# File upload constraints
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/bmp",
    "image/webp",
    "application/octet-stream",
}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit

# CORS configuration (reads comma-separated origins from environment, with local dev fallbacks)
_env_origins = os.getenv("ALLOWED_ORIGINS")
if _env_origins:
    ALLOWED_ORIGINS = [orig.strip() for orig in _env_origins.split(",") if orig.strip()]
else:
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# Ensure required runtime directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
