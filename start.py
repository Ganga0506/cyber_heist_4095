"""Start the Cyber Heist API and frontend together: python start.py."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def run(command, cwd):
    subprocess.run([str(part) for part in command], cwd=cwd, check=True)


def stop(process):
    if os.name == "nt":
        # Include Uvicorn's reloader and Vite's child Node process.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    elif process.poll() is None:
        import signal

        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install", action="store_true", help="Reinstall project dependencies."
    )
    args = parser.parse_args()
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm:
        print("Node.js/npm is required. Install Node.js, then reopen your terminal.")
        return 1

    python = BACKEND / ".venv" / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    marker = BACKEND / ".venv" / ".cyberheist-dependencies"
    processes = []
    try:
        if not python.exists():
            print("Creating the backend virtual environment...", flush=True)
            run([sys.executable, "-m", "venv", BACKEND / ".venv"], ROOT)
        if args.install or not marker.exists():
            print("Installing backend dependencies...", flush=True)
            run([python, "-m", "pip", "install", "-r", "requirements.txt"], BACKEND)
            marker.touch()
        if args.install or not (FRONTEND / "node_modules" / ".bin" / "vite").exists():
            print("Installing frontend dependencies...", flush=True)
            run([npm, "install"], FRONTEND)

        print("\nFrontend: http://localhost:5173\nAPI docs: http://127.0.0.1:8000/docs")
        print("Press Ctrl+C to stop both servers.\n", flush=True)
        options = (
            {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
            if os.name == "nt"
            else {"start_new_session": True}
        )
        for command, cwd in [
            ([str(python), "-m", "uvicorn", "main:app", "--reload"], BACKEND),
            ([npm, "run", "dev", "--", "--strictPort"], FRONTEND),
        ]:
            processes.append(subprocess.Popen(command, cwd=cwd, **options))
        while all(process.poll() is None for process in processes):
            time.sleep(0.25)
        print("A server exited; stopping both servers.", flush=True)
        return next((p.returncode for p in processes if p.returncode), 1)
    except KeyboardInterrupt:
        print("\nStopping Cyber Heist...", flush=True)
        return 0
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Could not start Cyber Heist: {exc}", file=sys.stderr)
        return 1
    finally:
        for process in reversed(processes):
            stop(process)


if __name__ == "__main__":
    sys.exit(main())
