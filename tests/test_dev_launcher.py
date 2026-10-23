"""Behavioral checks at the development launcher command-line boundary."""
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import time
import subprocess
import sys
import tempfile
import unittest


SOURCE_ROOT = Path(__file__).resolve().parents[1]


class DevLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="bibi-launcher-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / "project"
        self.root.mkdir()
        for name in ("dev", "dev.sh"):
            source = SOURCE_ROOT / name
            self.assertTrue(source.exists(), f"Missing launcher entrypoint: {source}")
            shutil.copy2(source, self.root / name, follow_symlinks=True)
        for name in ("backend", "frontend"):
            (self.root / name).mkdir()
        for name in ("backend/pyproject.toml", "backend/uv.lock",
                     "frontend/package.json", "frontend/package-lock.json", "frontend/.npmrc"):
            source = SOURCE_ROOT / name
            if source.exists():
                shutil.copy2(source, self.root / name)
        self.bin = Path(self.temporary.name) / "bin"
        self.bin.mkdir()
        self.events = Path(self.temporary.name) / "events.jsonl"
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}",
                        LAUNCHER_TEST_EVENTS=str(self.events))
        recorder = f"#!{sys.executable}\n" + """import json, os, pathlib, runpy, sys
if sys.argv[1:] == ['--version']:
    print({'node': 'v22.0.0', 'npm': '11.0.0', 'uv': 'uv 0.8.0'}[pathlib.Path(sys.argv[0]).name])
    sys.exit(0)
if sys.argv[1:3] == ['run', 'dev']:
    runpy.run_path(os.environ['LAUNCHER_TEST_SERVER'], run_name='__main__')
    sys.exit(0)
with open(os.environ['LAUNCHER_TEST_EVENTS'], 'a') as stream:
    stream.write(json.dumps({'command': pathlib.Path(sys.argv[0]).name,
                            'args': sys.argv[1:], 'cwd': os.getcwd()}) + '\\n')
if os.environ.get('LAUNCHER_TEST_INSTALL_FAIL') == pathlib.Path(sys.argv[0]).name:
    sys.exit(7)
"""
        for command in ("uv", "npm", "node"):
            path = self.bin / command
            path.write_text(recorder)
            path.chmod(0o755)

    def install_fake_servers(self):
        server = Path(self.temporary.name) / "server.py"
        server.write_text("""import http.server, json, os, pathlib, subprocess, sys, threading, time
args = sys.argv[1:]
role = pathlib.Path.cwd().name
if os.environ.get('LAUNCHER_TEST_FAIL_START') == role:
    print('deliberate startup failure', flush=True)
    sys.exit(9)
port = int(args[args.index('--port') + 1])
if os.environ.get('LAUNCHER_TEST_BIND_RACE') == role:
    holder_code = ('import socket,sys,time; s=socket.socket(); '
                   's.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); '
                   's.bind(("127.0.0.1",int(sys.argv[1]))); s.listen(); '
                   'print("bound",flush=True); time.sleep(300)')
    child = subprocess.Popen([sys.executable, '-c', holder_code, str(port)],
                             stdout=subprocess.PIPE, text=True)
    if child.stdout.readline().strip() != 'bound':
        raise RuntimeError('Test holder failed to bind')
else:
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)'])
with open(os.environ['LAUNCHER_TEST_EVENTS'], 'a') as stream:
    stream.write(json.dumps({'command': 'server', 'args': args, 'cwd': os.getcwd(),
                            'pid': os.getpid(), 'child': child.pid, 'port': port,
                            'backend_url': os.environ.get('BIBI_BACKEND_PORT')}) + '\\n')
httpd = http.server.HTTPServer(('127.0.0.1', port), http.server.BaseHTTPRequestHandler)
print('test server listening', flush=True)
def fail_when_requested():
    trigger = pathlib.Path(os.environ['LAUNCHER_TEST_TRIGGER'])
    while not trigger.exists() or trigger.read_text() != role:
        time.sleep(0.02)
    os._exit(9)
threading.Thread(target=fail_when_requested, daemon=True).start()
httpd.serve_forever()
""")
        self.env["LAUNCHER_TEST_SERVER"] = str(server)
        self.env["LAUNCHER_TEST_TRIGGER"] = str(Path(self.temporary.name) / "failure-trigger")
        python = self.root / "backend/.venv/bin/python"
        python.parent.mkdir(parents=True)
        python.write_text(f"#!{sys.executable}\n" + """import os, runpy, sys
if sys.argv[1:3] == ['-m', 'uvicorn']:
    runpy.run_path(os.environ['LAUNCHER_TEST_SERVER'], run_name='__main__')
elif sys.argv[1:2] == ['-c']:
    sys.exit(1 if os.environ.get('LAUNCHER_TEST_MISSING_IMPORT') else 0)
else:
    os.execv(sys.executable, [sys.executable, *sys.argv[1:]])
""")
        python.chmod(0o755)
        next_bin = self.root / "frontend/node_modules/next/dist/bin/next"
        next_bin.parent.mkdir(parents=True)
        next_bin.write_text("installed")

    def start_launcher(self, entrypoint="dev"):
        output = tempfile.TemporaryFile(mode="w+")
        self.addCleanup(output.close)
        process = subprocess.Popen([str(self.root / entrypoint)],
                                   cwd=self.temporary.name, env=self.env,
                                   stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        self.addCleanup(self.cleanup_launcher, process)
        return process, output

    def cleanup_launcher(self, process):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=7)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
        for event in self.recorded_events():
            for field in ("pid", "child"):
                if field in event:
                    try:
                        os.kill(event[field], signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def wait_for_servers(self, process, output):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            servers = [event for event in self.recorded_events() if event['command'] == 'server']
            if len(servers) == 2:
                try:
                    for event in servers:
                        with socket.create_connection(('127.0.0.1', event['port']), timeout=0.2):
                            pass
                except OSError:
                    pass
                else:
                    return servers
            if process.poll() is not None:
                output.seek(0)
                self.fail(f"Launcher exited before both servers started: {output.read()}")
            time.sleep(0.05)
        self.fail("Both servers did not start within 10 seconds")

    def assert_processes_stopped(self, servers):
        pids = [event[field] for event in servers for field in ("pid", "child")]
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            live = []
            for pid in pids:
                result = subprocess.run(["ps", "-p", str(pid), "-o", "stat="],
                                        capture_output=True, text=True)
                if result.stdout.strip() and not result.stdout.lstrip().startswith("Z"):
                    live.append(pid)
            if not live:
                for event in servers:
                    with socket.socket() as probe:
                        probe.settimeout(0.2)
                        self.assertNotEqual(probe.connect_ex(('127.0.0.1', event['port'])), 0,
                                            f"Owned port {event['port']} is still listening")
                return
            time.sleep(0.05)
        self.fail(f"Owned processes still running: {live}")

    def test_startup_skips_install_and_sigterm_cleans_owned_descendants(self):
        self.install_fake_servers()
        process, output = self.start_launcher()
        servers = self.wait_for_servers(process, output)
        process.send_signal(signal.SIGTERM)
        process.wait(timeout=10)
        self.assert_processes_stopped(servers)
        self.assertEqual([event['command'] for event in self.recorded_events()], ['server', 'server'])
        output.seek(0)
        log = output.read()
        for event in servers:
            self.assertIn(f"http://127.0.0.1:{event['port']}", log)
        self.assertIn('test server listening', log)

    def run_launcher(self, entrypoint="dev", *arguments):
        return subprocess.run([str(self.root / entrypoint), *arguments],
                              cwd=self.temporary.name, env=self.env,
                              text=True, capture_output=True, timeout=15)

    def recorded_events(self):
        if not self.events.exists():
            return []
        return [json.loads(line) for line in self.events.read_text().splitlines()]

    def test_port_preferences_conflicts_preserve_unrelated_listeners(self):
        self.install_fake_servers()
        for occupied in ((), (3000,), (8000,), (3000, 8000)):
            with self.subTest(occupied=occupied):
                holders = {}
                unavailable = False
                for port in (3000, 8000):
                    holder = socket.socket()
                    holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        holder.bind(('127.0.0.1', port))
                    except OSError:
                        holder.close()
                        unavailable = True
                        break
                    holder.listen()
                    holders[port] = holder
                if unavailable:
                    for holder in holders.values():
                        holder.close()
                    self.skipTest('Preferred ports occupied by existing work; preserving those listeners')
                for port in set(holders) - set(occupied):
                    holders.pop(port).close()
                self.events.unlink(missing_ok=True)
                process = None
                try:
                    process, output = self.start_launcher('dev.sh')
                    servers = self.wait_for_servers(process, output)
                    self.assertEqual(len({event['port'] for event in servers}), 2)
                    for event in servers:
                        backend = event['cwd'] == str(self.root / 'backend')
                        preferred = 8000 if backend else 3000
                        if preferred in occupied:
                            self.assertNotIn(event['port'], occupied)
                        else:
                            self.assertEqual(event['port'], preferred)
                        self.assertIn('127.0.0.1', event['args'])
                        if backend:
                            if '--workers' in event['args']:
                                self.assertEqual(event['args'][event['args'].index('--workers') + 1], '1')
                        else:
                            actual_backend = next(item['port'] for item in servers
                                                  if item['cwd'] == str(self.root / 'backend'))
                            self.assertEqual(event['backend_url'], str(actual_backend))
                    process.send_signal(signal.SIGINT)
                    process.wait(timeout=10)
                    self.assert_processes_stopped(servers)
                    for port, holder in holders.items():
                        self.assertEqual(holder.getsockname()[1], port)
                        with socket.create_connection(('127.0.0.1', port), timeout=1):
                            pass
                finally:
                    if process is not None:
                        self.cleanup_launcher(process)
                    for holder in holders.values():
                        holder.close()

    def test_missing_dependencies_and_unsupported_arguments_give_guidance(self):
        result = self.run_launcher('dev', 'unsupported')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('usage', (result.stdout + result.stderr).lower())
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('install', (result.stdout + result.stderr).lower())
        self.install_fake_servers()
        next_bin = self.root / 'frontend/node_modules/next/dist/bin/next'
        next_bin.unlink()
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('install', (result.stdout + result.stderr).lower())
        next_bin.write_text('installed')
        self.env['LAUNCHER_TEST_MISSING_IMPORT'] = '1'
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('install', (result.stdout + result.stderr).lower())
        self.assertEqual(self.recorded_events(), [])

    def test_either_startup_failure_reports_failure_and_cleans_peer(self):
        self.install_fake_servers()
        for role in ('backend', 'frontend'):
            with self.subTest(role=role):
                self.events.unlink(missing_ok=True)
                self.env['LAUNCHER_TEST_FAIL_START'] = role
                process, output = self.start_launcher()
                process.wait(timeout=10)
                self.assertNotEqual(process.returncode, 0)
                servers = [event for event in self.recorded_events() if event['command'] == 'server']
                self.assert_processes_stopped(servers)
                output.seek(0)
                self.assertIn(f'{role} server exited', output.read().lower())
                self.cleanup_launcher(process)

    def test_either_running_server_failure_cleans_peer_and_descendants(self):
        self.install_fake_servers()
        trigger = Path(self.env['LAUNCHER_TEST_TRIGGER'])
        for role in ('backend', 'frontend'):
            with self.subTest(role=role):
                trigger.unlink(missing_ok=True)
                self.events.unlink(missing_ok=True)
                process, output = self.start_launcher()
                servers = self.wait_for_servers(process, output)
                trigger.write_text(role)
                process.wait(timeout=10)
                self.assertNotEqual(process.returncode, 0)
                self.assert_processes_stopped(servers)
                output.seek(0)
                self.assertIn(f'{role} server exited', output.read().lower())
                self.cleanup_launcher(process)

    def test_bind_race_cleans_partial_app_and_owned_port_holder(self):
        self.install_fake_servers()
        for role in ('backend', 'frontend'):
            with self.subTest(role=role):
                self.events.unlink(missing_ok=True)
                self.env['LAUNCHER_TEST_BIND_RACE'] = role
                process, output = self.start_launcher()
                process.wait(timeout=10)
                self.assertNotEqual(process.returncode, 0)
                servers = [event for event in self.recorded_events() if event['command'] == 'server']
                output.seek(0)
                self.assertTrue(any(event['cwd'] == str(self.root / role) for event in servers), output.read())
                self.assert_processes_stopped(servers)
                output.seek(0)
                self.assertIn(f'{role} server exited', output.read().lower())
                self.cleanup_launcher(process)

    def test_missing_tools_fail_usefully_without_starting_servers(self):
        for tool in ('bash', 'python3', 'dirname'):
            (self.bin / tool).symlink_to(shutil.which(tool))
        self.env['PATH'] = str(self.bin)
        for tool in ('node', 'npm', 'uv', 'python3'):
            with self.subTest(tool=tool):
                executable = self.bin / tool
                hidden = self.bin / (tool + '.hidden')
                executable.rename(hidden)
                try:
                    result = self.run_launcher('dev', 'install')
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(tool.lower().rstrip('3'), (result.stdout + result.stderr).lower())
                    self.assertEqual(self.recorded_events(), [])
                finally:
                    hidden.rename(executable)

    def test_install_failure_returns_nonzero_and_starts_no_servers(self):
        for command in ("uv", "npm"):
            with self.subTest(command=command):
                self.events.unlink(missing_ok=True)
                self.env['LAUNCHER_TEST_INSTALL_FAIL'] = command
                result = self.run_launcher('dev', 'install')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('install', (result.stdout + result.stderr).lower())
                self.assertNotIn('server', [event['command'] for event in self.recorded_events()])
                if command == 'uv':
                    self.assertEqual([event['command'] for event in self.recorded_events()], ['uv'])

    def test_install_uses_locked_dependencies_from_both_entrypoints_outside_checkout(self):
        for entrypoint in ("dev", "dev.sh"):
            with self.subTest(entrypoint=entrypoint):
                if self.events.exists():
                    self.events.unlink()
                result = self.run_launcher(entrypoint, "install")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self.recorded_events(), [
                    {"command": "uv", "args": ["sync", "--frozen"],
                     "cwd": str(self.root / "backend")},
                    {"command": "npm", "args": ["ci", "--ignore-scripts"],
                     "cwd": str(self.root / "frontend")},
                ])


if __name__ == "__main__":
    unittest.main()
