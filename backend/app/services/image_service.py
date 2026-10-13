"""Image processing and validation service."""

import io
import uuid
import logging
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
from fastapi import UploadFile, HTTPException, status

from app.config import (
    UPLOAD_DIR,
    RESULTS_DIR,
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
)

logger = logging.getLogger("pcb_defect_detection.image_service")

class ImageService:
    """Service handling image upload validation, storage, and secure retrieval."""

    @staticmethod
    async def validate_and_save_upload(file: UploadFile) -> Tuple[Path, str, Tuple[int, int], str]:
        """Validate an uploaded image file and save it to the uploads directory.

        Returns:
            Tuple containing:
            - saved_path (Path): Path to saved file on disk.
            - original_filename (str): Sanitized original filename.
            - dimensions (Tuple[int, int]): (width, height) of image.
            - format (str): Detected image format (JPEG, PNG, etc.).

        Raises:
            HTTPException: If file is missing, oversized, or not a valid image.
        """
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a valid filename."
            )

        original_ext = Path(file.filename).suffix.lower()
        if original_ext not in ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{original_ext}'. Allowed formats: {allowed_list}."
            )

        # Read contents
        try:
            contents = await file.read()
        except Exception as e:
            logger.error(f"Failed to read uploaded file stream: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read uploaded file contents."
            )

        # Check file size
        file_size = len(contents)
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        if file_size > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {max_mb:.1f} MB (uploaded: {actual_mb:.2f} MB)."
            )

        # Validate image integrity and dimensions using Pillow
        try:
            image_buffer = io.BytesIO(contents)
            with Image.open(image_buffer) as img:
                img.verify()  # Verifies image header & data integrity
                img_format = img.format or "JPEG"

            # Re-open for dimensions since verify() closes/resets some attributes
            image_buffer.seek(0)
            with Image.open(image_buffer) as img:
                width, height = img.size

        except Exception as e:
            logger.warning(f"Corrupt or invalid image upload '{file.filename}': {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid or readable image."
            )

        # Generate a collision-resistant unique filename
        unique_id = uuid.uuid4().hex[:12]
        safe_filename = f"pcb_{unique_id}{original_ext}"
        destination_path = UPLOAD_DIR / safe_filename

        try:
            # If uploaded image exceeds 2560px in either dimension, optimize to prevent
            # CPU thrashing and memory exhaustion on containerized instances (Render 512MB RAM)
            max_side = max(width, height)
            if max_side > 2560:
                scale = 2560.0 / max_side
                new_size = (int(width * scale), int(height * scale))
                image_buffer.seek(0)
                with Image.open(image_buffer) as pil_resize_img:
                    resized = pil_resize_img.convert("RGB").resize(new_size, Image.Resampling.LANCZOS)
                    resized.save(destination_path, format="JPEG", quality=90, optimize=True)
                width, height = new_size
                img_format = "JPEG"
                logger.info(f"Downsampled oversized upload to {width}x{height} for efficient inference: {destination_path}")
            else:
                destination_path.write_bytes(contents)
                logger.info(f"Saved uploaded PCB image to: {destination_path} ({width}x{height}, {file_size} bytes)")
        except Exception as e:
            logger.error(f"Failed to write image file to disk: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store uploaded image on server."
            )

        return destination_path, file.filename, (width, height), img_format

    @staticmethod
    def get_result_image_path(filename: str) -> Path:
        """Securely resolve and validate a result image file path.

        Prevents directory traversal (e.g. `../../etc/passwd`).

        Raises:
            HTTPException: If file path is invalid or does not exist.
        """
        # Strip directory components to prevent path traversal
        clean_filename = Path(filename).name
        target_path = (RESULTS_DIR / clean_filename).resolve()

        # Ensure target_path stays strictly within RESULTS_DIR
        try:
            target_path.relative_to(RESULTS_DIR.resolve())
        except ValueError:
            logger.warning(f"Path traversal attempt blocked: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path requested."
            )

        if not target_path.exists() or not target_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Result image '{clean_filename}' was not found."
            )

        return target_path
