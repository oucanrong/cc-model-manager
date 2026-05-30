from __future__ import annotations

from pathlib import Path


def validate_token(token: str) -> None:
    return


def validate_project_path(project_path: str) -> Path:
    path = Path(project_path).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        raise ValueError("项目目录不存在或不是有效目录。")
    return path