"""YOLOv8 Defect Detection Service.

Manages YOLOv8 lifecycle, model weight verification, defect inference,
bounding-box parsing, defect classification, and annotated result rendering.
"""

import time
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
import cv2
from PIL import Image

from app.config import MODEL_PATH, RESULTS_DIR
from app.schemas.detection import (
    BoundingBox,
    DefectDetection,
    DefectSummary,
    InspectionResult,
)

logger = logging.getLogger("pcb_defect_detection.detector")

# Standardized mapping from model defect label variations to canonical keys
CANONICAL_CLASS_MAP = {
    "open circuit": "open",
    "open": "open",
    "short circuit": "short",
    "short": "short",
    "mouse bite": "mouse_bite",
    "mouse_bite": "mouse_bite",
    "spur": "spur",
    "spurious copper": "spurious_copper",
    "spurious_copper": "spurious_copper",
    "missing hole": "missing_hole",
    "missing_hole": "missing_hole",
}

EXPECTED_DEFECT_CLASSES = {
    "open",
    "short",
    "mouse_bite",
    "spur",
    "spurious_copper",
    "missing_hole",
}

class PCBDetectorService:
    """Manages the YOLOv8 model loading, lifecycle, and defect inference."""

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = Path(model_path) if model_path else MODEL_PATH
        self._model = None
        self._is_loaded = False
        self._class_names: Dict[int, str] = {}
        self._load_error: Optional[str] = None
        logger.info(f"Initialized PCBDetectorService with target model path: {self.model_path}")

    @property
    def model_file_exists(self) -> bool:
        """Check whether the model weights file exists on disk and is non-empty."""
        return self.model_path.is_file() and self.model_path.stat().st_size > 0

    @property
    def is_loaded(self) -> bool:
        """Check whether the model has been successfully loaded into memory."""
        return self._is_loaded and self._model is not None

    def load_model(self, force_reload: bool = False):
        """Load the YOLOv8 model weights from disk.

        Loads the model only once unless `force_reload` is explicitly True.

        Raises:
            FileNotFoundError: If model file does not exist on disk.
            RuntimeError: If weights file is corrupted or fails to initialize.
        """
        if self.is_loaded and not force_reload:
            return self._model

        if not self.model_file_exists:
            self._load_error = (
                f"Model weights file '{self.model_path.name}' was not found at '{self.model_path}'. "
                "Setup instruction: Please place your trained YOLOv8 weights (best.pt) at "
                f"'{self.model_path}' before attempting detection."
            )
            logger.error(self._load_error)
            raise FileNotFoundError(self._load_error)

        try:
            logger.info(f"Loading YOLOv8 model from '{self.model_path}'...")
            from ultralytics import YOLO

            # Load YOLO model
            model = YOLO(str(self.model_path))

            # Cache class names dictionary
            if hasattr(model, "names") and isinstance(model.names, dict):
                self._class_names = model.names
            else:
                self._class_names = {}

            self._model = model
            self._is_loaded = True
            self._load_error = None

            logger.info(
                f"YOLOv8 model successfully loaded. Detected {len(self._class_names)} defect classes: {self._class_names}"
            )
            return self._model

        except Exception as e:
            self._model = None
            self._is_loaded = False
            self._load_error = f"Failed to load YOLOv8 model from '{self.model_path}': {str(e)}"
            logger.exception(self._load_error)
            raise RuntimeError(self._load_error) from e

    def get_supported_classes(self) -> List[str]:
        """Return the list of class names loaded from model metadata."""
        if not self.is_loaded:
            if self.model_file_exists:
                try:
                    self.load_model()
                except Exception:
                    return []
            else:
                return []
        return list(self._class_names.values())

    def verify_class_taxonomy(self) -> Tuple[bool, Dict[str, Any]]:
        """Verify whether the loaded model matches the expected 6 PCB defect classes."""
        classes = self.get_supported_classes()
        normalized = {
            CANONICAL_CLASS_MAP.get(c.strip().lower(), c.strip().lower())
            for c in classes
        }
        missing = EXPECTED_DEFECT_CLASSES - normalized
        matches_expected = len(missing) == 0

        return matches_expected, {
            "model_classes": classes,
            "normalized_classes": sorted(list(normalized)),
            "expected_classes": sorted(list(EXPECTED_DEFECT_CLASSES)),
            "missing_classes": sorted(list(missing)),
            "all_classes_supported": matches_expected,
        }

    def get_status_summary(self) -> Dict[str, Any]:
        """Return diagnostic status information regarding model availability."""
        exists = self.model_file_exists
        if exists and not self.is_loaded:
            try:
                self.load_model()
            except Exception as e:
                logger.warning(f"Model auto-load on status check failed: {e}")

        loaded = self.is_loaded

        if not exists:
            message = (
                f"Model weights file '{self.model_path.name}' was not found at '{self.model_path}'. "
                "Setup instruction: Please place your trained YOLOv8 weights (best.pt) in "
                "backend/models/best.pt."
            )
        elif not loaded:
            if self._load_error:
                message = self._load_error
            else:
                message = f"Model weights '{self.model_path.name}' available on disk. Ready for inference."
        else:
            message = f"YOLOv8 model active with {len(self._class_names)} defect classes."

        classes = list(self._class_names.values()) if self.is_loaded else None

        return {
            "model_path": str(self.model_path),
            "model_file_exists": exists,
            "model_loaded": loaded,
            "status_message": message,
            "classes": classes,
        }

    def detect(
        self,
        image_path: Path,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ) -> InspectionResult:
        """Run YOLOv8 inference on a PCB image and generate an annotated result image.

        Args:
            image_path (Path): Path to the target PCB image.
            conf_threshold (float): Minimum confidence threshold (default: 0.25).
            iou_threshold (float): Non-maximum suppression IoU threshold (default: 0.45).

        Returns:
            InspectionResult: Complete inspection summary, bounding boxes, and annotated image path.

        Raises:
            FileNotFoundError: If image file or model weights do not exist.
            RuntimeError: If model inference fails.
        """
        image_path = Path(image_path)
        if not image_path.is_file():
            raise FileNotFoundError(f"Input image not found at '{image_path}'.")

        # Ensure model is loaded (loads once)
        if not self.is_loaded:
            self.load_model()

        # Read image dimensions
        try:
            with Image.open(image_path) as pil_img:
                img_width, img_height = pil_img.size
        except Exception as e:
            raise RuntimeError(f"Failed to inspect image dimensions: {e}") from e

        # Run inference
        t0 = time.perf_counter()
        try:
            results = self._model.predict(
                source=str(image_path),
                conf=conf_threshold,
                iou=iou_threshold,
                verbose=False,
            )
        except Exception as e:
            logger.error(f"Inference execution failed on '{image_path}': {e}")
            raise RuntimeError(f"YOLOv8 inference execution failed: {e}") from e

        inference_time_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        if not results:
            raise RuntimeError("YOLOv8 returned empty result container.")

        yolo_result = results[0]
        inspection_id = uuid.uuid4().hex[:12]
        timestamp_str = datetime.now(timezone.utc).isoformat()

        # Parse detected defect boxes
        detections: List[DefectDetection] = []
        defects_by_class: Dict[str, int] = {}
        all_confidences: List[float] = []

        if yolo_result.boxes is not None and len(yolo_result.boxes) > 0:
            for idx, box in enumerate(yolo_result.boxes, start=1):
                # Extract coordinates [x1, y1, x2, y2]
                xyxy = box.xyxy[0].tolist()
                x1, y1, x2, y2 = xyxy[0], xyxy[1], xyxy[2], xyxy[3]
                w = max(0.0, x2 - x1)
                h = max(0.0, y2 - y1)

                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                raw_class_name = self._class_names.get(cls_id, f"class_{cls_id}")
                standard_class = CANONICAL_CLASS_MAP.get(
                    raw_class_name.strip().lower(),
                    raw_class_name.strip().lower()
                )

                defects_by_class[raw_class_name] = defects_by_class.get(raw_class_name, 0) + 1
                all_confidences.append(conf)

                detections.append(
                    DefectDetection(
                        defect_id=idx,
                        class_id=cls_id,
                        class_name=raw_class_name,
                        standard_class=standard_class,
                        confidence=round(conf, 4),
                        confidence_percentage=round(conf * 100.0, 2),
                        bbox=BoundingBox(
                            x1=round(x1, 1),
                            y1=round(y1, 1),
                            x2=round(x2, 1),
                            y2=round(y2, 1),
                            width=round(w, 1),
                            height=round(h, 1),
                        ),
                    )
                )

        total_defects = len(detections)
        pass_inspection = total_defects == 0
        status_label = "DEFECT_FREE" if pass_inspection else "DEFECTIVE"

        max_conf = round(max(all_confidences), 4) if all_confidences else None
        avg_conf = round(sum(all_confidences) / len(all_confidences), 4) if all_confidences else None

        summary = DefectSummary(
            total_defects=total_defects,
            defects_by_class=defects_by_class,
            max_confidence=max_conf,
            average_confidence=avg_conf,
            status=status_label,
            pass_inspection=pass_inspection,
        )

        # Generate and save annotated visualization
        annotated_filename = f"result_{inspection_id}.jpg"
        annotated_path = RESULTS_DIR / annotated_filename

        try:
            # yolo_result.plot() renders bounding boxes with classes & confidence badges
            plotted_bgr = yolo_result.plot(line_width=2, font_size=1)
            cv2.imwrite(str(annotated_path), plotted_bgr)
            logger.info(f"Saved annotated detection image to: {annotated_path}")
        except Exception as e:
            logger.warning(f"Failed to plot bounding boxes using YOLO plotter: {e}. Falling back to copy.")
            try:
                # Fallback: copy original image so client still receives an image
                annotated_path.write_bytes(image_path.read_bytes())
            except Exception as copy_err:
                logger.error(f"Failed to create fallback result image: {copy_err}")
                raise RuntimeError("Failed to generate result visualization.") from copy_err

        return InspectionResult(
            inspection_id=inspection_id,
            timestamp=timestamp_str,
            original_filename=image_path.name,
            image_width=img_width,
            image_height=img_height,
            annotated_image_filename=annotated_filename,
            annotated_image_url=f"/api/results/{annotated_filename}",
            inference_time_ms=inference_time_ms,
            detections=detections,
            summary=summary,
        )

# Global singleton detector instance
detector_service = PCBDetectorService()
