from __future__ import annotations

import base64
import json
from pathlib import Path

import psutil


_STATE_FILE_NAME = "cc-model-manager-settings-restore.json"


class ClaudeSettingsService:
    def __init__(
        self,
        settings_path: Path | None = None,
        state_path: Path | None = None,
    ) -> None:
        claude_dir = Path.home() / ".claude"
        self.settings_path = settings_path or claude_dir / "settings.json"
        self.state_path = state_path or claude_dir / _STATE_FILE_NAME

    def recover_if_needed(self) -> bool:
        if not self.state_path.exists():
            return False
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        owner_pid = state.get("owner_pid")
        if isinstance(owner_pid, int) and psutil.pid_exists(owner_pid):
            return False
        self._restore_from_state()
        return True

    def _restore_from_state(self) -> None:
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        target = Path(state.get("settings_path") or self.settings_path)
        original = base64.b64decode(state.get("original_base64", ""))
        if state.get("original_exists", False):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original)
        elif target.exists():
            target.unlink()
        self.state_path.unlink(missing_ok=True)
