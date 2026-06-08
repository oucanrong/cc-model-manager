from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.services.claude_service import ClaudeService


class ClaudeServiceTests(unittest.TestCase):
    def test_native_process_detection_includes_extension_binary(self) -> None:
        processes = [
            SimpleNamespace(info={"name": "Code.exe"}),
            SimpleNamespace(info={"name": "claude.exe"}),
        ]
        with patch(
            "src.services.claude_service.psutil.process_iter",
            return_value=processes,
        ):
            self.assertTrue(ClaudeService.is_any_native_running())


if __name__ == "__main__":
    unittest.main()
