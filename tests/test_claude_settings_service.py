from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.services.claude_settings_service import ClaudeSettingsService


class ClaudeSettingsServiceTests(unittest.TestCase):
    def test_crash_recovery_restores_persisted_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings_path = root / "settings.json"
            state_path = root / "restore.json"
            original = b'{"theme":"dark"}'
            settings_path.write_text(
                '{"env":{"ANTHROPIC_AUTH_TOKEN":"temporary"}}',
                encoding="utf-8",
            )
            state_path.write_text(
                json.dumps(
                    {
                        "settings_path": str(settings_path),
                        "owner_pid": 99999999,
                        "original_exists": True,
                        "original_base64": base64.b64encode(original).decode(
                            "ascii"
                        ),
                    }
                ),
                encoding="utf-8",
            )

            recovered = ClaudeSettingsService(settings_path, state_path)
            with patch(
                "src.services.claude_settings_service.psutil.pid_exists",
                return_value=False,
            ):
                self.assertTrue(recovered.recover_if_needed())
            self.assertEqual(settings_path.read_bytes(), original)
            self.assertFalse(state_path.exists())


if __name__ == "__main__":
    unittest.main()
