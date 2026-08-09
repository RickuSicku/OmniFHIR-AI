"""
OmniFHIR-AI: Environment Setup & Dependency Verification Script

Checks that all prerequisites are met before running the pipeline:
  1. Python package dependencies (from requirements.txt)
  2. Ollama installation and server status
  3. Required LLM models (mistral, llama3.2-vision)
  4. Tesseract OCR (optional, for fallback)
  5. Database initialization

Run this once after cloning the repository:
    python setup_check.py
"""
import importlib
import json
import os
import shutil
import subprocess
import sys
import time


# ─── Configuration ───────────────────────────────────────────────────────────
REQUIRED_MODELS = ["mistral", "llama3.2-vision"]
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

REQUIRED_PACKAGES = [
    ("streamlit", "streamlit"),
    ("ollama", "ollama"),
    ("pypdf", "pypdf"),
    ("docx", "python-docx"),
    ("PIL", "Pillow"),
    ("pytesseract", "pytesseract"),
    ("fhir.resources", "fhir.resources"),
    ("pydantic", "pydantic"),
    ("reportlab", "reportlab"),
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def ok(msg):
    print(f"  {Colors.GREEN}[OK]{Colors.RESET}    {msg}")

def warn(msg):
    print(f"  {Colors.YELLOW}[WARN]{Colors.RESET}  {msg}")

def fail(msg):
    print(f"  {Colors.RED}[FAIL]{Colors.RESET}  {msg}")

def info(msg):
    print(f"  {Colors.CYAN}[INFO]{Colors.RESET}  {msg}")

def header(msg):
    print(f"\n{Colors.BOLD}{msg}{Colors.RESET}")
    print("-" * 55)


# ─── Check 1: Python Packages ───────────────────────────────────────────────

def check_python_packages() -> bool:
    """Verify all required Python packages are installed."""
    header("1. Python Package Dependencies")
    all_ok = True
    missing = []

    for import_name, pip_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(import_name)
            ok(f"{pip_name}")
        except ImportError:
            fail(f"{pip_name} — not installed")
            missing.append(pip_name)
            all_ok = False

    if missing:
        print()
        info(f"Install missing packages with:")
        print(f"       pip install {' '.join(missing)}")
        print(f"    or pip install -r requirements.txt")

    return all_ok


# ─── Check 2: Ollama Installation ───────────────────────────────────────────

def check_ollama_installed() -> bool:
    """Check if the Ollama CLI is available on PATH."""
    header("2. Ollama Installation")

    ollama_path = shutil.which("ollama")
    if ollama_path:
        ok(f"Ollama found at: {ollama_path}")
        # Get version
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            version = result.stdout.strip() or result.stderr.strip()
            if version:
                info(f"Version: {version}")
        except Exception:
            pass
        return True
    else:
        fail("Ollama is not installed or not on PATH")
        info("Install from: https://ollama.com/download")
        return False


# ─── Check 3: Ollama Server ─────────────────────────────────────────────────

def check_ollama_server() -> bool:
    """Check if the Ollama server is running and responsive."""
    header("3. Ollama Server Status")

    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            ok(f"Ollama server is running at {OLLAMA_BASE_URL}")
            return True
        else:
            fail(f"Ollama server returned status {response.status_code}")
            return False
    except ImportError:
        # requests not installed yet
        fail("Cannot check server — 'requests' package not installed")
        return False
    except Exception:
        fail(f"Ollama server is not running at {OLLAMA_BASE_URL}")
        info("Start it with: ollama serve")
        return False


# ─── Check 4: Required Models ───────────────────────────────────────────────

def check_and_pull_models() -> bool:
    """Check if required models are available. Pull any that are missing."""
    header("4. Required LLM Models")

    # Get list of installed models
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        installed = {m["name"].split(":")[0] for m in data.get("models", [])}
    except Exception as e:
        fail(f"Cannot query models — is Ollama running? ({e})")
        return False

    all_ok = True
    for model in REQUIRED_MODELS:
        model_base = model.split(":")[0]
        if model_base in installed:
            ok(f"{model} — already installed")
        else:
            warn(f"{model} — not found locally")
            info(f"Pulling {model}... (this may take several minutes)")
            if _pull_model(model):
                ok(f"{model} — pulled successfully")
            else:
                fail(f"{model} — pull failed")
                all_ok = False

    return all_ok


def _pull_model(model_name: str) -> bool:
    """Pull a model using the Ollama CLI with real-time progress."""
    try:
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        for raw_line in process.stdout:
            try:
                line = raw_line.decode("utf-8", errors="replace").strip()
            except Exception:
                line = str(raw_line).strip()
            if line:
                # Sanitize for Windows console — strip chars it can't render
                safe_line = line.encode(sys.stdout.encoding or "ascii", errors="replace").decode(sys.stdout.encoding or "ascii", errors="replace")
                print(f"       {safe_line}", end="\r")

        process.wait()
        print()  # New line after progress

        return process.returncode == 0

    except FileNotFoundError:
        fail("Ollama CLI not found — cannot pull models")
        return False
    except Exception as e:
        fail(f"Error pulling model: {e}")
        return False


# ─── Check 5: Tesseract OCR (Optional) ──────────────────────────────────────

def check_tesseract() -> bool:
    """Check if Tesseract OCR is available (optional fallback)."""
    header("5. Tesseract OCR (Optional Fallback)")

    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        ok(f"Tesseract found at: {tesseract_path}")
        try:
            result = subprocess.run(
                ["tesseract", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
            info(f"Version: {version_line}")
        except Exception:
            pass
        return True
    else:
        warn("Tesseract not installed — OCR will use vision model only")
        info("Install from: https://github.com/tesseract-ocr/tesseract")
        info("(Not required — the vision model is the primary OCR path)")
        return True  # Optional, so still OK


# ─── Check 6: Database Setup ────────────────────────────────────────────────

def check_database() -> bool:
    """Initialize the SQLite database."""
    header("6. Database Initialization")

    try:
        # Add project root to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from src.db.models import initialize_database, DB_PATH
        from src.config import DATA_DIR

        os.makedirs(DATA_DIR, exist_ok=True)
        initialize_database()
        ok(f"Database ready at: {DB_PATH}")
        return True
    except Exception as e:
        fail(f"Database initialization failed: {e}")
        return False


# ─── Check 7: Sample Data ───────────────────────────────────────────────────

def check_sample_data() -> bool:
    """Check if sample test data has been generated."""
    header("7. Sample Test Data")

    sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
    if os.path.isdir(sample_dir):
        files = os.listdir(sample_dir)
        if len(files) >= 10:
            ok(f"Found {len(files)} sample files in sample_data/")
            return True
        else:
            warn(f"Only {len(files)} files found — expected 12")
            info("Regenerate with: python generate_test_data.py")
            return True
    else:
        warn("No sample_data/ directory found")
        info("Generate with: python generate_test_data.py")
        return True  # Not critical


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print()
    print(f"{Colors.BOLD}{'=' * 55}{Colors.RESET}")
    print(f"{Colors.BOLD}  OmniFHIR-AI: Environment Setup & Verification{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 55}{Colors.RESET}")

    results = {}

    # Phase 1: Python packages
    results["packages"] = check_python_packages()

    # Phase 2: Ollama CLI
    results["ollama_cli"] = check_ollama_installed()

    # Phase 3: Ollama server
    if results["ollama_cli"]:
        results["ollama_server"] = check_ollama_server()
    else:
        results["ollama_server"] = False
        header("3. Ollama Server Status")
        fail("Skipped — Ollama not installed")

    # Phase 4: Models (only if server is running)
    if results["ollama_server"]:
        results["models"] = check_and_pull_models()
    else:
        results["models"] = False
        header("4. Required LLM Models")
        fail("Skipped — Ollama server not running")

    # Phase 5: Tesseract (optional)
    results["tesseract"] = check_tesseract()

    # Phase 6: Database
    if results["packages"]:
        results["database"] = check_database()
    else:
        results["database"] = False
        header("6. Database Initialization")
        fail("Skipped — missing Python packages")

    # Phase 7: Sample data
    results["sample_data"] = check_sample_data()

    # ── Summary ──────────────────────────────────────────────────────────
    print()
    print(f"{Colors.BOLD}{'=' * 55}{Colors.RESET}")
    print(f"{Colors.BOLD}  Setup Summary{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 55}{Colors.RESET}")

    critical_pass = all([
        results["packages"],
        results["ollama_cli"],
        results["ollama_server"],
        results["models"],
    ])

    for name, passed in results.items():
        icon = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
        label = name.replace("_", " ").title()
        print(f"  [{icon}] {label}")

    print()
    if critical_pass:
        print(f"  {Colors.GREEN}{Colors.BOLD}All critical checks passed!{Colors.RESET}")
        print()
        print("  You can now run the pipeline:")
        print(f"    {Colors.CYAN}python -m src.pipeline{Colors.RESET}      (CLI mode)")
        print(f"    {Colors.CYAN}streamlit run ui/app.py{Colors.RESET}     (Web UI)")
    else:
        print(f"  {Colors.RED}{Colors.BOLD}Some critical checks failed.{Colors.RESET}")
        print("  Fix the issues above and run this script again.")

    print()
    return 0 if critical_pass else 1


if __name__ == "__main__":
    sys.exit(main())
