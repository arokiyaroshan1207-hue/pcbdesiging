"""Phase 4 & 5 Integration Verification Runner.

Tests frontend-backend integration, API proxy, image upload & detection,
annotated image streaming, and system health telemetry.
"""

import sys
import httpx
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
SAMPLE_IMAGE = ROOT_DIR / "backend" / "sample_images" / "pcb1.jpg"

def run_integration_tests():
    print("=" * 65)
    print("AI-POWERED PCB DEFECT DETECTION - PHASES 4 & 5 INTEGRATION AUDIT")
    print("=" * 65)

    all_passed = True

    # 1. Frontend Server Check
    try:
        fe_res = httpx.get("http://127.0.0.1:5173/", timeout=5.0)
        if fe_res.status_code == 200 and "<div id=\"root\">" in fe_res.text:
            print("[PASS] Frontend Vite Server : http://127.0.0.1:5173/ (HTTP 200)")
        else:
            print(f"[FAIL] Frontend Vite Server returned unexpected status {fe_res.status_code}")
            all_passed = False
    except Exception as e:
        print(f"[FAIL] Could not connect to Frontend server on port 5173: {e}")
        all_passed = False

    # 2. Backend Health Check
    try:
        be_res = httpx.get("http://127.0.0.1:8000/api/health", timeout=5.0)
        data = be_res.json()
        if be_res.status_code == 200 and data.get("status") == "healthy":
            print(f"[PASS] Backend API Health   : http://127.0.0.1:8000/api/health (Model: {data.get('model_status_message')})")
        else:
            print(f"[FAIL] Backend health check failed: {be_res.status_code}")
            all_passed = False
    except Exception as e:
        print(f"[FAIL] Could not connect to Backend on port 8000: {e}")
        all_passed = False

    # 3. Frontend-to-Backend Proxy Route
    try:
        proxy_res = httpx.get("http://127.0.0.1:5173/api/health", timeout=5.0)
        if proxy_res.status_code == 200 and proxy_res.json().get("model_loaded") is True:
            print("[PASS] Vite API Reverse Proxy: http://127.0.0.1:5173/api/health -> Proxy Active")
        else:
            print(f"[FAIL] Vite proxy returned status {proxy_res.status_code}")
            all_passed = False
    except Exception as e:
        print(f"[FAIL] Vite proxy error: {e}")
        all_passed = False

    # 4. Live Defect Detection Through Frontend Proxy
    try:
        if not SAMPLE_IMAGE.exists():
            print(f"[FAIL] Test sample image missing: {SAMPLE_IMAGE}")
            all_passed = False
        else:
            with open(SAMPLE_IMAGE, "rb") as f:
                files = {"file": ("pcb1.jpg", f, "image/jpeg")}
                det_res = httpx.post(
                    "http://127.0.0.1:5173/api/detect?conf_threshold=0.25",
                    files=files,
                    timeout=30.0
                )

            if det_res.status_code == 200:
                det_data = det_res.json()
                n_defects = det_data.get("summary", {}).get("total_defects", 0)
                annotated_url = det_data.get("annotated_image_url", "")
                latency = det_data.get("inference_time_ms", 0)
                classes = det_data.get("summary", {}).get("defects_by_class", {})

                print(f"[PASS] Live Detection E2E   : {n_defects} defects detected in {latency} ms")
                print(f"       Defect Breakdown     : {classes}")

                # 5. Fetch Annotated Image via Frontend
                img_res = httpx.get(f"http://127.0.0.1:5173{annotated_url}", timeout=10.0)
                if img_res.status_code == 200 and len(img_res.content) > 100000:
                    print(f"[PASS] Annotated Image View : {annotated_url} ({len(img_res.content):,} bytes)")
                else:
                    print(f"[FAIL] Failed to retrieve annotated image: {img_res.status_code}")
                    all_passed = False
            else:
                print(f"[FAIL] Detect API returned status {det_res.status_code}: {det_res.text}")
                all_passed = False

    except Exception as e:
        print(f"[FAIL] End-to-end detection test error: {e}")
        all_passed = False

    print("=" * 65)
    if all_passed:
        print("[SUCCESS] ALL PHASE 4 & 5 INTEGRATION CHECKS PASSED (100%)")
    else:
        print("[FAILURE] SOME INTEGRATION CHECKS FAILED")
    print("=" * 65)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    run_integration_tests()
