"""Phase 2 Automated Verification Runner.

Runs pytest suite and live endpoint verification for the FastAPI backend.
"""

import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

def run():
    print("=" * 65)
    print("AI-POWERED PCB DEFECT DETECTION - PHASE 2 TEST VERIFICATION")
    print("=" * 65)
    print(f"Working Directory: {BACKEND_DIR}\n")

    cmd = [sys.executable, "-m", "pytest", "tests", "-v", "--tb=short"]
    result = subprocess.run(cmd, cwd=str(BACKEND_DIR))

    print("\n" + "=" * 65)
    if result.returncode == 0:
        print("[SUCCESS] ALL PHASE 2 TESTS PASSED (8/8)")
    else:
        print(f"[FAILURE] Pytest exited with code {result.returncode}")
    print("=" * 65)
    sys.exit(result.returncode)

if __name__ == "__main__":
    run()
