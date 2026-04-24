"""Daemon mode for persistent MCP service."""

import os
import sys
import signal
import logging
import subprocess
import platform
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


class WikiDaemon:
    """Daemon manager for MCP server."""

    def __init__(self, pid_file: Path, log_file: Path):
        """
        Initialize daemon.

        Args:
            pid_file: Path to PID file
            log_file: Path to log file
        """
        self.pid_file = pid_file
        self.log_file = log_file

    def start(self, target_func=None, *args, **kwargs):
        """
        Start daemon process.

        Args:
            target_func: Function to run in daemon mode (Unix only)
            *args, **kwargs: Arguments for target function
        """
        # Check if already running
        if self.is_running():
            raise RuntimeError(f"Daemon already running (PID: {self.get_pid()})")

        if IS_WINDOWS:
            return self._start_windows()
        else:
            return self._start_unix(target_func, *args, **kwargs)

    def _start_windows(self):
        """Start daemon on Windows using subprocess."""
        # 启动一个新的 Python 进程运行 wiki mcp serve
        cmd = [sys.executable, "-m", "wiki_cli.main", "mcp", "serve"]

        with open(self.log_file, "a") as log:
            proc = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                close_fds=True,
            )

        # Write PID file
        with open(self.pid_file, "w") as f:
            f.write(str(proc.pid))

        return proc.pid

    def _start_unix(self, target_func, *args, **kwargs):
        """Start daemon on Unix using fork."""
        # Fork process
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process
                return pid
        except OSError as e:
            raise RuntimeError(f"Fork failed: {e}")

        # Child process
        os.setsid()
        os.umask(0)

        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            raise RuntimeError(f"Second fork failed: {e}")

        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        with open(self.log_file, "a") as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
            os.dup2(f.fileno(), sys.stderr.fileno())

        # Write PID file
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)

        # Run target function
        try:
            target_func(*args, **kwargs)
        finally:
            self.cleanup()

    def stop(self):
        """Stop daemon process."""
        pid = self.get_pid()
        if not pid:
            raise RuntimeError("Daemon not running")

        try:
            if IS_WINDOWS:
                import subprocess
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True, capture_output=True)
            else:
                import time
                os.kill(pid, signal.SIGTERM)
                for _ in range(10):
                    try:
                        os.kill(pid, 0)
                        time.sleep(0.5)
                    except OSError:
                        break
                else:
                    os.kill(pid, signal.SIGKILL)
        except (OSError, subprocess.CalledProcessError) as e:
            raise RuntimeError(f"Failed to stop daemon: {e}")
        finally:
            self.cleanup()

    def is_running(self) -> bool:
        """Check if daemon is running."""
        pid = self.get_pid()
        if not pid:
            return False

        if IS_WINDOWS:
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True
            )
            return str(pid) in result.stdout
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def get_pid(self) -> Optional[int]:
        """Get daemon PID from file."""
        if not self.pid_file.exists():
            return None

        try:
            with open(self.pid_file, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return None

    def cleanup(self):
        """Clean up PID file."""
        if self.pid_file.exists():
            self.pid_file.unlink()

    def _handle_sigterm(self, signum, frame):
        """Handle SIGTERM signal."""
        logger.info("Received SIGTERM, shutting down...")
        self.cleanup()
        sys.exit(0)
