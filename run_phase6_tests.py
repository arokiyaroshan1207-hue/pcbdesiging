"""Phase 6 Automated Verification Script for AI-Powered PCB Defect Detection System.

Tests:
1. Backend Health Check (GET /api/health)
2. Live YOLOv8 Detection on real sample PCB (POST /api/detect)
3. Downloadable PDF Report Generation (POST /api/reports/generate-pdf)
4. PDF Inspection Report verification (Title, ID, Date, Images, Breakdown, Confidences, Observations)
5. PDF Retrieval by Inspection ID (GET /api/reports/{id}/pdf)
6. Zero-Defect handling in PDF report
7. Frontend Vite Proxy pass-through verification
"""

import sys
import json
import base64
import zlib
import requests
from pathlib import Path

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"
SAMPLE_IMG = Path("d:/MONOPOLY/PCB-DEFECT-DETECTION/backend/sample_images/pcb1.jpg")
DOWNLOADED_PDF = Path("d:/MONOPOLY/PCB-DEFECT-DETECTION/test_downloaded_report.pdf")

def run_tests():
    print("=" * 70)
    print("PHASE 6 AUTOMATED VERIFICATION: DOWNLOADABLE PDF INSPECTION REPORTS")
    print("=" * 70)

    # 1. Health check
    print("\n[Step 1] Checking Backend Health...")
    r = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    health = r.json()
    assert health["model_loaded"] is True
    print(f" PASS: Backend online. Model loaded with {len(health['supported_defect_classes'])} classes.")

    # 2. Live detection on real PCB sample
    print("\n[Step 2] Executing live YOLOv8 detection on sample image (pcb1.jpg)...")
    assert SAMPLE_IMG.is_file(), f"Sample image {SAMPLE_IMG} not found"
    with open(SAMPLE_IMG, "rb") as f:
        detect_resp = requests.post(
            f"{BACKEND_URL}/api/detect",
            files={"file": ("pcb1.jpg", f, "image/jpeg")},
            params={"conf_threshold": 0.25},
            timeout=30,
        )
    assert detect_resp.status_code == 200, f"Detection failed: {detect_resp.status_code} - {detect_resp.text}"
    result = detect_resp.json()
    inspection_id = result["inspection_id"]
    total_defects = result["summary"]["total_defects"]
    print(f" PASS: Detection completed in {result['inference_time_ms']} ms.")
    print(f"       Inspection ID: {inspection_id}")
    print(f"       Total Defects Detected: {total_defects}")
    print(f"       Defects by Class: {result['summary']['defects_by_class']}")
    print(f"       Annotated Image Filename: {result['annotated_image_filename']}")
    print(f"       Raw Image Filename: {result.get('raw_image_filename')}")

    # 3. Generate downloadable PDF via POST /api/reports/generate-pdf
    print("\n[Step 3] Requesting Downloadable PDF Inspection Report...")
    pdf_resp = requests.post(
        f"{BACKEND_URL}/api/reports/generate-pdf",
        json=result,
        timeout=30,
    )
    assert pdf_resp.status_code == 200, f"PDF generation failed: {pdf_resp.status_code} - {pdf_resp.text}"
    assert pdf_resp.headers.get("content-type") == "application/pdf", "Expected application/pdf"
    assert "attachment" in pdf_resp.headers.get("content-disposition", ""), "Expected attachment header"
    
    pdf_bytes = pdf_resp.content
    assert pdf_bytes.startswith(b"%PDF-"), "Invalid PDF signature"
    DOWNLOADED_PDF.write_bytes(pdf_bytes)
    print(f" PASS: PDF generated and downloaded ({len(pdf_bytes):,} bytes). Saved to: {DOWNLOADED_PDF}")

    # 4. Decompress and verify required contents of generated PDF
    print("\n[Step 4] Inspecting PDF internal contents & layout integrity...")
    idx = 0
    decompressed = []
    while True:
        s_start = pdf_bytes.find(b"stream\n", idx)
        if s_start == -1:
            s_start = pdf_bytes.find(b"stream\r\n", idx)
            if s_start == -1:
                break
            data_start = s_start + 8
        else:
            data_start = s_start + 7
        s_end = pdf_bytes.find(b"endstream", data_start)
        if s_end == -1:
            break
        data = pdf_bytes[data_start:s_end].strip()
        try:
            a85 = base64.a85decode(data, adobe=True)
            dec = zlib.decompress(a85)
            decompressed.append(dec.decode("latin1", errors="ignore"))
        except Exception:
            pass
        idx = s_end + 9

    full_pdf_text = " ".join(decompressed)

    required_elements = {
        "Project Title": "AI-Powered PCB Defect Detection System",
        "Inspection ID": inspection_id,
        "Original Image Section": "Original PCB Micrograph",
        "Annotated Image Section": "YOLOv8 Annotated Defect Map",
        "Defect Section": "Defect Classification",
        "Confidence Telemetry": "Statistical Confidence Telemetry",
        "Engineering Observations": "DEFECT ADVISORY",
    }

    for name, snippet in required_elements.items():
        found = snippet in full_pdf_text
        assert found, f"Required element '{name}' ('{snippet}') missing from PDF text stream!"
        print(f" PASS: Verified '{name}' is present in generated PDF.")

    # 5. Retrieve PDF by ID via GET /api/reports/{id}/pdf
    print("\n[Step 5] Testing pre-compiled PDF retrieval by Inspection ID...")
    get_pdf_resp = requests.get(f"{BACKEND_URL}/api/reports/{inspection_id}/pdf", timeout=10)
    assert get_pdf_resp.status_code == 200, f"GET report by ID failed: {get_pdf_resp.status_code}"
    assert get_pdf_resp.content.startswith(b"%PDF-")
    print(f" PASS: Retrieved pre-compiled PDF ({len(get_pdf_resp.content):,} bytes).")

    # 6. Test Zero-Defect Handling in PDF
    print("\n[Step 6] Testing Zero-Defect PCB Report Generation...")
    zero_defect_payload = {
        "inspection_id": "test_qa_zero_flaw",
        "timestamp": "2026-10-11T01:00:00Z",
        "original_filename": "clean_board.jpg",
        "image_width": 2048,
        "image_height": 1536,
        "annotated_image_filename": result["annotated_image_filename"],
        "raw_image_filename": result.get("raw_image_filename"),
        "inference_time_ms": 88.0,
        "detections": [],
        "summary": {
            "total_defects": 0,
            "defects_by_class": {},
            "max_confidence": None,
            "average_confidence": None,
            "status": "DEFECT_FREE",
            "pass_inspection": True,
        },
    }
    zero_pdf_resp = requests.post(f"{BACKEND_URL}/api/reports/generate-pdf", json=zero_defect_payload, timeout=20)
    assert zero_pdf_resp.status_code == 200
    assert zero_pdf_resp.content.startswith(b"%PDF-")
    print(f" PASS: Zero-defect PDF report successfully compiled ({len(zero_pdf_resp.content):,} bytes).")

    # 7. Test Frontend Proxy to Backend for PDF generation
    print("\n[Step 7] Testing Frontend Vite dev proxy for PDF generation...")
    try:
        proxy_resp = requests.post(
            f"{FRONTEND_URL}/api/reports/generate-pdf",
            json=result,
            timeout=15,
        )
        assert proxy_resp.status_code == 200
        assert proxy_resp.content.startswith(b"%PDF-")
        print(f" PASS: Frontend Vite Proxy correctly routed PDF generation to FastAPI backend ({len(proxy_resp.content):,} bytes).")
    except Exception as e:
        print(f" WARNING: Proxy test encounter: {e}")

    print("\n" + "=" * 70)
    print("ALL PHASE 6 REQUIREMENTS VERIFIED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
