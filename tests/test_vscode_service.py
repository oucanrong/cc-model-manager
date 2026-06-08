from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.core.config_manager import AppConfig, ConfigManager
from src.services.vscode_service import VSCodeService


class VSCodeServiceTests(unittest.TestCase):
    def test_saved_path_has_priority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "Code.exe"
            executable.touch()
            service = VSCodeService()
            with patch.object(service, "_registry_candidates", return_value=[]):
                self.assertEqual(
                    service.resolve_executable(str(executable)),
                    executable,
                )

    def test_code_command_infers_installation_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            install = Path(directory) / "Microsoft VS Code"
            executable = install / "Code.exe"
            command = install / "bin" / "code.cmd"
            command.parent.mkdir(parents=True)
            executable.touch()
            command.touch()
            service = VSCodeService()
            with (
                patch.object(service, "_registry_candidates", return_value=[]),
                patch(
                    "src.services.vscode_service.shutil.which",
                    return_value=str(command),
                ),
                patch.dict("src.services.vscode_service.os.environ", {}, clear=True),
            ):
                self.assertEqual(service.resolve_executable(), executable)

    def test_running_detection_matches_any_process_with_same_path(self) -> None:
        executable = Path(r"C:\Apps\Microsoft VS Code\Code.exe")
        processes = [
            SimpleNamespace(info={"exe": r"C:\Windows\notepad.exe"}),
            SimpleNamespace(info={"exe": str(executable)}),
            SimpleNamespace(info={"exe": str(executable)}),
        ]
        service = VSCodeService()
        with patch(
            "src.services.vscode_service.psutil.process_iter",
            return_value=processes,
        ):
            self.assertTrue(service.is_running(executable))

    def test_vscode_path_is_saved_and_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            manager = ConfigManager(path)
            config = AppConfig(vscode_path=r"D:\Tools\VS Code\Code.exe")
            manager.save(config)
            self.assertEqual(
                manager.load().vscode_path,
                r"D:\Tools\VS Code\Code.exe",
            )

    def test_launch_targets_are_saved_and_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            manager = ConfigManager(path)
            config = AppConfig(claude_launch_target="vscode")
            config.codex.launch_target = "upgrade"
            manager.save(config)
            loaded = manager.load()
            self.assertEqual(loaded.claude_launch_target, "vscode")
            self.assertEqual(loaded.codex.launch_target, "upgrade")

    def test_missing_launch_targets_use_requested_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text("{}", encoding="utf-8")
            loaded = ConfigManager(path).load()
            self.assertEqual(loaded.claude_launch_target, "cli")
            self.assertEqual(loaded.codex.launch_target, "desktop")

    def test_removed_claude_desktop_target_falls_back_to_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                '{"claude_launch_target": "desktop"}',
                encoding="utf-8",
            )
            self.assertEqual(
                ConfigManager(path).load().claude_launch_target,
                "cli",
            )


if __name__ == "__main__":
    unittest.main()
