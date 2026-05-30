# 路径: src/workers/claude_worker.py
# 作用: Claude Code 启动异步线程

from __future__ import annotations

import webbrowser

from PyQt6.QtCore import QThread, pyqtSignal

from src.core.config_manager import AppConfig
from src.core.logger import setup_logger
from src.core.process_manager import ProcessManager
from src.services.claude_service import ClaudeService


class ClaudeWorker(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)

    def __init__(self, config: AppConfig, process_manager: ProcessManager) -> None:
        super().__init__()
        self.config = config
        self.process_manager = process_manager
        self.service = ClaudeService()
        self.logger = setup_logger()
        self._stop_requested = False

    def _emit_process_output(self, prefix: str, text: str) -> None:
        if not text:
            return
        for line in text.splitlines():
            line = line.rstrip()
            if line:
                self.log_signal.emit(f"[{prefix}] {line}")

    def _ensure_claude_ready(self) -> None:
        if self.service.check_claude_installed():
            return

        self.status_signal.emit("未检测到 claude，开始检查 npm ...")
        self.log_signal.emit("[SYSTEM] 未检测到 claude，开始检查 npm ...")

        if not self.service.check_npm_installed():
            self.status_signal.emit("未检测到 npm，已打开 Node.js 下载页面。")
            self.log_signal.emit("[SYSTEM] 未检测到 npm，已自动打开 Node.js 下载页面。")
            webbrowser.open(self.service.node_download_url, new=2)
            raise RuntimeError("未检测到 npm，请先安装 Node.js。已为你打开下载页面。")

        self.status_signal.emit("检测到 npm，正在自动安装 Claude Code ...")
        self.log_signal.emit("[SYSTEM] 检测到 npm，正在自动安装 Claude Code ...")

        result = self.service.install_claude_code()
        if result.stdout:
            self._emit_process_output("INSTALL", result.stdout)
        if result.stderr:
            self._emit_process_output("INSTALL-ERR", result.stderr)

        if result.returncode != 0:
            raise RuntimeError(
                "Claude Code 自动安装失败，请检查 npm / 网络 / 权限后重试。"
            )

        if not self.service.check_claude_installed():
            raise RuntimeError(
                "Claude Code 安装完成，但当前环境仍未检测到 claude 命令。请确认 npm 全局路径已加入 PATH。"
            )

        self.status_signal.emit("Claude Code 安装完成。")
        self.log_signal.emit("[SYSTEM] Claude Code 安装完成。")

    def run(self) -> None:
        try:
            self._ensure_claude_ready()

            cwd, env, command = self.service.build_startup_context(self.config)
            self.status_signal.emit(f"正在启动 Claude Code：{cwd}")
            self.log_signal.emit(f"[SYSTEM] 工作目录：{cwd}")
            self.log_signal.emit(f"[SYSTEM] 启动命令：{' '.join(command)}")

            proc = self.process_manager.start(command=command, cwd=cwd, env=env)
            self.status_signal.emit("Claude Code 已在独立终端中启动。")
            self.log_signal.emit("[SYSTEM] Claude Code 已在独立终端中启动。")

            return_code = proc.wait()
            self.status_signal.emit(f"Claude Code 已退出，返回码：{return_code}")
            self.finished_signal.emit(return_code)
        except Exception as exc:
            self.logger.exception("启动 Claude Code 失败")
            self.error_signal.emit(str(exc))

    def request_soft_stop(self) -> None:
        self._stop_requested = True
        if not self.process_manager.stop_soft():
            self.process_manager.stop_hard()

    def request_hard_stop(self) -> None:
        self._stop_requested = True
        self.process_manager.stop_hard()