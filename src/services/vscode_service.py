from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import psutil

from src.core.config_manager import ProxyConfig
from src.services.proxy_service import apply_proxy_env
from src.services.validator_service import validate_project_path


VSCODE_DOWNLOAD_URL = "https://code.visualstudio.com/"


class VSCodeService:
    def resolve_executable(self, saved_path: str = "") -> Path | None:
        candidates: list[Path] = []
        if saved_path.strip():
            candidates.append(Path(saved_path.strip()))
        candidates.extend(self._registry_candidates())

        command = shutil.which("code")
        if command:
            command_path = Path(command)
            candidates.append(command_path)
            if command_path.parent.name.casefold() == "bin":
                candidates.append(command_path.parent.parent / "Code.exe")

        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates.append(
                Path(local_app_data) / "Programs" / "Microsoft VS Code" / "Code.exe"
            )
        for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(env_name)
            if base:
                candidates.append(Path(base) / "Microsoft VS Code" / "Code.exe")

        seen: set[str] = set()
        for candidate in candidates:
            normalized = str(candidate.expanduser().resolve(strict=False)).casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            if candidate.name.casefold() == "code.exe" and candidate.is_file():
                return candidate
        return None

    def _registry_candidates(self) -> list[Path]:
        if os.name != "nt":
            return []
        try:
            import winreg
        except ImportError:
            return []

        candidates: list[Path] = []
        roots = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
        views = (0, winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY)
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
        for root in roots:
            for view in views:
                try:
                    with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ | view) as key:
                        for index in range(winreg.QueryInfoKey(key)[0]):
                            child_name = winreg.EnumKey(key, index)
                            try:
                                with winreg.OpenKey(key, child_name) as child:
                                    display_name = str(
                                        winreg.QueryValueEx(child, "DisplayName")[0]
                                    )
                                    if "Visual Studio Code" not in display_name:
                                        continue
                                    try:
                                        location = str(
                                            winreg.QueryValueEx(child, "InstallLocation")[0]
                                        )
                                    except OSError:
                                        location = ""
                                    if location:
                                        candidates.append(Path(location) / "Code.exe")
                                    try:
                                        icon = str(
                                            winreg.QueryValueEx(child, "DisplayIcon")[0]
                                        ).split(",", 1)[0].strip('"')
                                    except OSError:
                                        icon = ""
                                    if icon:
                                        candidates.append(Path(icon))
                            except OSError:
                                continue
                except OSError:
                    continue
        return candidates

    def is_running(self, executable: Path) -> bool:
        target = str(executable.resolve(strict=False)).casefold()
        for process in psutil.process_iter(["exe"]):
            try:
                value = process.info.get("exe")
                if value and str(Path(value).resolve(strict=False)).casefold() == target:
                    return True
            except (OSError, psutil.Error):
                continue
        return False

    def stop(self, executable: Path) -> None:
        target = str(executable.resolve(strict=False)).casefold()
        for process in psutil.process_iter(["exe"]):
            try:
                value = process.info.get("exe")
                if not value:
                    continue
                if str(Path(value).resolve(strict=False)).casefold() != target:
                    continue
                process.terminate()
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    process.kill()
            except (OSError, psutil.Error):
                continue

    def build_startup_context(
        self,
        executable: Path,
        project_path: str,
        proxy: ProxyConfig,
        env: dict[str, str] | None = None,
        for_codex: bool = False,
    ) -> tuple[Path, dict[str, str], list[str]]:
        cwd = validate_project_path(project_path)
        startup_env = dict(env) if env is not None else os.environ.copy()
        apply_proxy_env(startup_env, proxy, for_codex=for_codex)
        return cwd, startup_env, [str(executable), str(cwd)]

    @staticmethod
    def _run_hidden(command: list[str]) -> subprocess.CompletedProcess[str]:
        if (
            os.name == "nt"
            and command
            and Path(command[0]).suffix.casefold() in {".cmd", ".bat"}
        ):
            command = [
                os.environ.get("COMSPEC", "cmd.exe"),
                "/d",
                "/c",
                *command,
            ]
        kwargs: dict[str, object] = {
            "check": False,
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        return subprocess.run(command, **kwargs)
