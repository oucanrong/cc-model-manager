from __future__ import annotations

import unittest
from unittest.mock import patch

from src.core.config_manager import AppConfig, CodexProviderSettings
from src.core.constants import CODEX_PROVIDER_OFFICIAL
from src.core.process_manager import ProcessManager
from src.workers.claude_worker import ClaudeWorker
from src.workers.codex_worker import CodexWorker


class UpgradeCheckTests(unittest.TestCase):
    def test_claude_skips_upgrade_when_already_latest(self) -> None:
        worker = ClaudeWorker(AppConfig(), ProcessManager(), upgrade_only=True)
        with (
            patch.object(
                worker.service,
                "get_installed_package_version",
                return_value="2.1.168",
            ),
            patch.object(
                worker.service,
                "get_latest_package_version",
                return_value="2.1.168",
            ),
            patch.object(worker.service, "build_upgrade_command") as build_command,
        ):
            result = worker._try_upgrade_claude()

        self.assertTrue(result)
        self.assertTrue(worker.already_latest)
        build_command.assert_not_called()

    def test_codex_skips_upgrade_when_already_latest(self) -> None:
        worker = CodexWorker(
            provider=CODEX_PROVIDER_OFFICIAL,
            settings=CodexProviderSettings(),
            project_path="",
            process_manager=ProcessManager(),
            upgrade_only=True,
        )
        with (
            patch.object(
                worker.service,
                "get_installed_package_version",
                return_value="0.137.0",
            ),
            patch.object(
                worker.service,
                "get_latest_package_version",
                return_value="0.137.0",
            ),
            patch.object(worker.service, "build_upgrade_command") as build_command,
        ):
            worker._run_upgrade()

        self.assertTrue(worker.already_latest)
        build_command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
