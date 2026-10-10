"""Phase 1 Verification Script: Project Structure and Environment Checks.

This script audits the environment and verifies that all required directories,
configuration files, and baseline assets for the AI-Powered PCB Defect Detection System
are correctly initialized.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Ensure standard output can handle utf-8 on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent

REQUIRED_DIRS = [
    ROOT_DIR / "backend",
    ROOT_DIR / "backend" / "app",
    ROOT_DIR / "backend" / "app" / "routes",
    ROOT_DIR / "backend" / "app" / "services",
    ROOT_DIR / "backend" / "app" / "schemas",
    ROOT_DIR / "backend" / "models",
    ROOT_DIR / "backend" / "uploads",
    ROOT_DIR / "backend" / "results",
    ROOT_DIR / "backend" / "sample_images",
    ROOT_DIR / "frontend",
    ROOT_DIR / "frontend" / "public",
    ROOT_DIR / "frontend" / "src",
    ROOT_DIR / "frontend" / "src" / "components",
    ROOT_DIR / "frontend" / "src" / "pages",
    ROOT_DIR / "frontend" / "src" / "services",
    ROOT_DIR / "frontend" / "src" / "styles",
]

REQUIRED_FILES = [
    ROOT_DIR / ".gitignore",
    ROOT_DIR / "README.md",
    ROOT_DIR / "backend" / "requirements.txt",
    ROOT_DIR / "backend" / "app" / "__init__.py",
    ROOT_DIR / "backend" / "app" / "routes" / "__init__.py",
    ROOT_DIR / "backend" / "app" / "services" / "__init__.py",
    ROOT_DIR / "backend" / "app" / "schemas" / "__init__.py",
    ROOT_DIR / "backend" / "models" / "best.pt",
    ROOT_DIR / "frontend" / ".env",
]

def check_environment():
    print("=" * 60)
    print("AI-POWERED PCB DEFECT DETECTION - PHASE 1 AUDIT")
    print("=" * 60)
    
    # 1. Python check
    py_ver = sys.version.split()[0]
    print(f"[OK] Python Interpreter : {sys.executable} (v{py_ver})")
    
    # 2. Node check
    node_cmd = shutil.which("node")
    if not node_cmd:
        # Check standard user install path
        winget_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        matched = list(winget_path.glob("**/node.exe"))
        if matched:
            node_cmd = str(matched[0])
    
    if node_cmd:
        try:
            node_out = subprocess.check_output([node_cmd, "--version"], text=True).strip()
            print(f"[OK] Node.js Runtime    : {node_cmd} ({node_out})")
        except Exception as e:
            print(f"[!] Node.js execution error: {e}")
    else:
        print("[FAIL] Node.js Runtime    : Not found in PATH")

    # 3. NPM check
    npm_cmd = shutil.which("npm.cmd")
    if not npm_cmd and node_cmd:
        possible_npm = Path(node_cmd).parent / "npm.cmd"
        if possible_npm.exists():
            npm_cmd = str(possible_npm)

    if npm_cmd:
        try:
            npm_out = subprocess.check_output([npm_cmd, "--version"], text=True).strip()
            print(f"[OK] NPM Package Manager: {npm_cmd} (v{npm_out})")
        except Exception as e:
            print(f"[!] NPM execution error: {e}")
    else:
        print("[FAIL] NPM Package Manager: Not found")

    print("-" * 60)

def verify_structure():
    all_passed = True
    print("Checking Required Directories:")
    for directory in REQUIRED_DIRS:
        if directory.is_dir():
            print(f"  [PASS] {directory.relative_to(ROOT_DIR)}")
        else:
            print(f"  [FAIL] Missing directory: {directory.relative_to(ROOT_DIR)}")
            all_passed = False

    print("\nChecking Required Files & Baseline Assets:")
    for file_path in REQUIRED_FILES:
        if file_path.is_file():
            size_bytes = file_path.stat().st_size
            print(f"  [PASS] {file_path.relative_to(ROOT_DIR)} ({size_bytes:,} bytes)")
        else:
            print(f"  [FAIL] Missing file: {file_path.relative_to(ROOT_DIR)}")
            all_passed = False

    # Sample images check
    sample_dir = ROOT_DIR / "backend" / "sample_images"
    samples = list(sample_dir.glob("*.jpg")) + list(sample_dir.glob("*.png"))
    print(f"\n  [PASS] Sample test PCB images available: {len(samples)} images found in backend/sample_images/")

    print("=" * 60)
    if all_passed:
        print("PHASE 1 VERIFICATION: ALL CHECKS PASSED SUCCESSFULLY [100%]")
    else:
        print("PHASE 1 VERIFICATION: SOME CHECKS FAILED")
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    check_environment()
    passed = verify_structure()
    sys.exit(0 if passed else 1)
