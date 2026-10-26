"""
WindLens UK - Unified Local Development Server Runner.
Launches both the FastAPI Python Backend and Vite React Frontend concurrently.
"""
import sys
import os
import subprocess
import time
import signal

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

processes = []

def cleanup(sig=None, frame=None):
    print("\n[WindLens UK] Shutting down development servers...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            p.kill()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    print("=" * 65)
    print("  WindLens UK - Starting Full-Stack Development Environment")
    print("=" * 65)

    # 1. Start FastAPI Backend
    print("[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = f"{BACKEND_DIR};{ROOT_DIR}"
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR,
        env=backend_env,
    )
    processes.append(backend_proc)

    # Allow backend to bind port
    time.sleep(1.5)

    # 2. Start Vite Frontend
    print("[2/2] Starting Vite React Frontend on http://127.0.0.1:5173 ...")
    shell_cmd = "npm run dev"
    frontend_proc = subprocess.Popen(
        shell_cmd,
        cwd=FRONTEND_DIR,
        shell=True,
    )
    processes.append(frontend_proc)

    print("\n" + "=" * 65)
    print("  >> FULL-STACK APPLICATION READY")
    print("  * Frontend UI:    http://localhost:5173")
    print("  * Backend API:    http://127.0.0.1:8000/api")
    print("  * Swagger Docs:   http://127.0.0.1:8000/api/docs")
    print("  Press Ctrl+C to stop both servers.")
    print("=" * 65 + "\n")

    try:
        while True:
            time.sleep(1)
            # Check if any process exited unexpectedly
            if backend_proc.poll() is not None:
                print("[WindLens UK] Backend process exited unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("[WindLens UK] Frontend process exited unexpectedly.")
                break
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
