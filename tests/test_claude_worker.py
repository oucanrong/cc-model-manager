from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.config_manager import AppConfig
from src.core.constants import PROVIDER_DEEPSEEK
from src.services.env_builder_service import build_env
from src.workers.claude_worker import ClaudeWorker


class ClaudeWorkerTests(unittest.TestCase):
    def _config(self) -> AppConfig:
        config = AppConfig(
            provider=PROVIDER_DEEPSEEK,
            token="test-key",
            project_path=".",
            anthropic_model="deepseek-v4-pro[1m]",
        )
        config.auth_tokens[PROVIDER_DEEPSEEK] = "test-key"
        return config

    def test_cli_uses_environment_without_writing_settings(self) -> None:
        process_manager = MagicMock()
        process_manager.start.return_value.wait.return_value = 0
        worker = ClaudeWorker(self._config(), process_manager)
        worker._ensure_claude_ready = MagicMock(return_value=True)
        worker.service = MagicMock()
        worker.service.build_startup_context.return_value = (
            Path("."),
            {"ANTHROPIC_AUTH_TOKEN": "test-key"},
            ["claude"],
        )

        worker._run_launch()

        process_manager.start.assert_called_once()
        process_manager.start_gui.assert_not_called()

    def test_settings_environment_excludes_stale_provider_parameters(self) -> None:
        config = self._config()
        with patch.dict(
            "src.services.env_builder_service.os.environ",
            {
                "ENABLE_TOOL_SEARCH": "stale",
                "API_TIMEOUT_MS": "stale",
                "HAS_COMPLETED_ONBOARDING": "stale",
            },
            clear=True,
        ):
            env = build_env(config)
        self.assertNotIn("ENABLE_TOOL_SEARCH", env)
        self.assertNotIn("API_TIMEOUT_MS", env)
        self.assertNotIn("HAS_COMPLETED_ONBOARDING", env)


if __name__ == "__main__":
    unittest.main()
