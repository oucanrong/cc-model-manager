# 路径: src/core/process_manager.py
# 作用: Claude Code 进程管理

from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil


@dataclass
class ProcessHandle:
    process: subprocess.Popen
    started_at: float


class ProcessManager:
    def __init__(self) -> None:
        self._handle: Optional[ProcessHandle] = None

    @property
    def running(self) -> bool:
        return self._handle is not None and self._handle.process.poll() is None

    @property
    def process(self) -> Optional[subprocess.Popen]:
        return self._handle.process if self._handle else None

    def start(self, command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen:
        if self.running:
            raise RuntimeError("Claude Code 已在运行，禁止重复启动。")

        popen_kwargs: dict[str, object] = {
            "cwd": str(cwd),
            "env": env,
            "stdin": None,
            "stdout": None,
            "stderr": None,
        }

        if os.name == "nt":
            popen_kwargs["creationflags"] = (
                subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
            )
        else:
            popen_kwargs["start_new_session"] = True

        proc = subprocess.Popen(command, **popen_kwargs)
        self._handle = ProcessHandle(process=proc, started_at=time.time())
        return proc

    def start_gui(
        self,
        executable: Path,
        cwd: Path,
        env: dict[str, str],
        arguments: list[str] | None = None,
    ) -> subprocess.Popen:
        if self.running:
            raise RuntimeError("Codex 已在运行，禁止重复启动。")
        kwargs: dict[str, object] = {
            "cwd": str(cwd),
            "env": env,
            "stdin": None,
            "stdout": None,
            "stderr": None,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        else:
            kwargs["start_new_session"] = True
        command = [str(executable), *(arguments or [])]
        proc = subprocess.Popen(command, **kwargs)
        self._handle = ProcessHandle(process=proc, started_at=time.time())
        return proc

    def stop_soft(self) -> bool:
        proc = self.process
        if not proc or proc.poll() is not None:
            return True
        try:
            if os.name == "nt":
                proc.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
            else:
                proc.terminate()
            return True
        except Exception:
            return False

    def stop_gui(self) -> bool:
        proc = self.process
        if not proc or proc.poll() is not None:
            return True
        try:
            proc.terminate()
            return True
        except Exception:
            return self.stop_hard()

    def stop_hard(self) -> bool:
        proc = self.process
        if not proc:
            return True
        try:
            if psutil.pid_exists(proc.pid):
                ps_proc = psutil.Process(proc.pid)
                for child in ps_proc.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                ps_proc.kill()
            else:
                proc.kill()
            return True
        except Exception:
            try:
                proc.kill()
                return True
            except Exception:
                return False

    def clear(self) -> None:
        self._handle = None
