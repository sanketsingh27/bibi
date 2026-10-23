#!/usr/bin/env bash
set -e

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.12+ is required. Install it, then run ./dev install." >&2
  exit 1
fi

# Python's standard library provides portable process groups on macOS and Linux.
exec python3 - "$ROOT" "$@" <<'PY'
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import time


def bind_port(listener, preferred):
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        listener.bind(("127.0.0.1", preferred))
    except OSError:
        listener.bind(("127.0.0.1", 0))
    return listener.getsockname()[1]


def signal_group(child, signum):
    try:
        os.killpg(child.pid, signum)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # macOS can return EPERM for a group containing only exited zombies.
        if sys.platform != "darwin":
            raise
        groups = subprocess.check_output(["ps", "-axo", "pgid=,stat="], text=True)
        for line in groups.splitlines():
            group, status = line.split()
            if int(group) == child.pid and not status.startswith("Z"):
                raise
        return False


def serve(root):
    python = root / "backend/.venv/bin/python"
    if not python.is_file() or not (root / "frontend/node_modules/next/dist/bin/next").is_file():
        sys.exit("Dependencies are missing. Run ./dev install before starting Bibi.")
    subprocess.run([str(python), "-c", "import uvicorn, fastapi, httpx, keyring"],
                   cwd=root / "backend", check=True)
    # Reserve both choices together so fallback ports cannot collide with each other.
    with socket.socket() as backend_socket, socket.socket() as frontend_socket:
        backend_port = bind_port(backend_socket, 8000)
        frontend_port = bind_port(frontend_socket, 3000)

    stopped = None

    def stop(signum, frame):
        nonlocal stopped
        stopped = signum

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    children = []
    try:
        print(f"Backend:  http://127.0.0.1:{backend_port}", flush=True)
        print(f"Frontend: http://127.0.0.1:{frontend_port}", flush=True)
        print("Press Ctrl+C to stop both servers.", flush=True)
        commands = [
            ("Backend", [str(python), "-m", "uvicorn", "bibi.main:app", "--host", "127.0.0.1",
                         "--port", str(backend_port), "--workers", "1"], root / "backend"),
            ("Frontend", ["npm", "run", "dev", "--", "--hostname", "127.0.0.1",
                          "--port", str(frontend_port)], root / "frontend"),
        ]
        environment = dict(os.environ, BIBI_BACKEND_PORT=str(backend_port), NEXT_TELEMETRY_DISABLED="1")
        for name, command, directory in commands:
            if stopped is not None:
                break
            child = subprocess.Popen(command, cwd=directory, env=environment, start_new_session=True)
            children.append((name, child))
        while stopped is None:
            for name, child in children:
                if child.poll() is not None:
                    sys.exit(f"{name} server exited (status {child.returncode}); stopping both servers.")
            time.sleep(0.1)
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        # Each server owns a separate process group, including npm/Next descendants.
        # Clean the groups even if their original server process has already exited.
        for signum in (signal.SIGTERM, signal.SIGKILL):
            for name, child in children:
                signal_group(child, signum)
            if signum == signal.SIGTERM:
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    for name, child in children:
                        child.poll()
                    groups_alive = False
                    for name, child in children:
                        if signal_group(child, 0):
                            groups_alive = True
                    if not groups_alive:
                        break
                    time.sleep(0.05)
        for name, child in children:
            child.wait()
    return 128 + stopped


def main():
    root = Path(sys.argv[1])
    args = sys.argv[2:]
    if args not in ([], ["install"]):
        sys.exit("Usage: ./dev [install] (or ./dev.sh [install])")
    if sys.version_info < (3, 12):
        sys.exit("Python 3.12+ is required. Install it, then run ./dev install.")
    for tool, minimum in (("node", 22), ("npm", 11)):
        if not shutil.which(tool):
            sys.exit(f"{tool} {minimum}+ is required. Install it, then run ./dev install.")
        version = subprocess.check_output([tool, "--version"], text=True)
        if int(re.search(r"\d+", version)[0]) < minimum:
            sys.exit(f"{tool} {minimum}+ is required. Upgrade it, then run ./dev install.")
    if args == ["install"]:
        if not shutil.which("uv"):
            sys.exit("uv is required. Install uv, then run ./dev install.")
        subprocess.run(["uv", "sync", "--frozen"], cwd=root / "backend", check=True)
        subprocess.run(["npm", "ci", "--ignore-scripts"], cwd=root / "frontend", check=True)
        print("Dependencies installed. Run ./dev to start Bibi.", flush=True)
        return
    return serve(root)


try:
    sys.exit(main())
except (OSError, subprocess.CalledProcessError) as error:
    sys.exit(f"Development command failed: {error}. Check the output above and run ./dev install.")
PY
