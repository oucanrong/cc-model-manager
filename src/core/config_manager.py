from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

from .constants import (
    CONFIG_PATH,
    DEFAULT_BASE_URL,
    DEFAULT_EFFORT_LEVEL,
    DEFAULT_HAIKU_MODEL,
    DEFAULT_MODEL,
    DEFAULT_OPUS_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_RECENT_PROJECTS,
    DEFAULT_SONNET_MODEL,
    DEFAULT_SUBAGENT_MODEL,
    PROVIDER_CLAUDE_DEFAULT,
    PROVIDER_DEEPSEEK,
    PROVIDER_KIMI,
    PROVIDER_OPTIONS,
    PROVIDER_ZHIPU,
)


@dataclass
class ProxyItem:
    enabled: bool = False
    host: str = ""
    port: str = ""
    auth: str = ""


@dataclass
class ProxyConfig:
    http: ProxyItem = field(default_factory=ProxyItem)
    https: ProxyItem = field(default_factory=ProxyItem)
    socks5: ProxyItem = field(default_factory=ProxyItem)


@dataclass
class AppConfig:
    provider: str = DEFAULT_PROVIDER
    base_url: str = DEFAULT_BASE_URL
    token: str = ""
    auth_tokens: dict[str, str] = field(default_factory=dict)
    anthropic_model: str = DEFAULT_MODEL
    default_opus_model: str = DEFAULT_OPUS_MODEL
    default_sonnet_model: str = DEFAULT_SONNET_MODEL
    default_haiku_model: str = DEFAULT_HAIKU_MODEL
    subagent_model: str = DEFAULT_SUBAGENT_MODEL
    effort_level: str = DEFAULT_EFFORT_LEVEL
    project_path: str = ""
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    recent_projects: list[str] = field(default_factory=list)


class ConfigManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CONFIG_PATH

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()

        data = json.loads(self.path.read_text(encoding="utf-8"))
        config = self._from_dict(data)

        provider = config.provider if config.provider in PROVIDER_OPTIONS else DEFAULT_PROVIDER
        config.provider = provider
        config.token = config.auth_tokens.get(provider, config.token).strip()
        return config

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._to_dict(config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _normalize_auth_tokens(self, data: Any) -> dict[str, str]:
        if not isinstance(data, dict):
            return {}
        result: dict[str, str] = {}
        for key, value in data.items():
            if value is None:
                result[str(key)] = ""
            else:
                result[str(key)] = str(value)
        return result

    def _from_dict(self, data: dict[str, Any]) -> AppConfig:
        provider = data.get("provider", DEFAULT_PROVIDER)
        if provider not in PROVIDER_OPTIONS:
            provider = DEFAULT_PROVIDER

        proxy_data = data.get("proxy", {})
        auth_tokens = self._normalize_auth_tokens(data.get("auth_tokens", {}))
        legacy_token = str(data.get("token", "") or "").strip()

        if not auth_tokens and legacy_token:
            auth_tokens = {provider: legacy_token}
        elif legacy_token and not auth_tokens.get(provider, "").strip():
            auth_tokens[provider] = legacy_token

        return AppConfig(
            provider=provider,
            base_url=str(data.get("base_url", DEFAULT_BASE_URL) or ""),
            token=auth_tokens.get(provider, legacy_token),
            auth_tokens=auth_tokens,
            anthropic_model=str(data.get("anthropic_model", DEFAULT_MODEL) or ""),
            default_opus_model=str(data.get("default_opus_model", DEFAULT_OPUS_MODEL) or ""),
            default_sonnet_model=str(data.get("default_sonnet_model", DEFAULT_SONNET_MODEL) or ""),
            default_haiku_model=str(data.get("default_haiku_model", DEFAULT_HAIKU_MODEL) or ""),
            subagent_model=str(data.get("subagent_model", DEFAULT_SUBAGENT_MODEL) or ""),
            effort_level=str(data.get("effort_level", DEFAULT_EFFORT_LEVEL) or ""),
            project_path=str(data.get("project_path", "") or ""),
            proxy=ProxyConfig(
                http=ProxyItem(**proxy_data.get("http", {})),
                https=ProxyItem(**proxy_data.get("https", {})),
                socks5=ProxyItem(**proxy_data.get("socks5", {})),
            ),
            recent_projects=data.get("recent_projects", []),
        )

    def _to_dict(self, config: AppConfig) -> dict[str, Any]:
        ordered_auth_tokens = {
            PROVIDER_CLAUDE_DEFAULT: config.auth_tokens.get(PROVIDER_CLAUDE_DEFAULT, ""),
            PROVIDER_DEEPSEEK: config.auth_tokens.get(PROVIDER_DEEPSEEK, ""),
            PROVIDER_KIMI: config.auth_tokens.get(PROVIDER_KIMI, ""),
            PROVIDER_ZHIPU: config.auth_tokens.get(PROVIDER_ZHIPU, ""),
        }

        return {
            "provider": config.provider,
            "base_url": config.base_url,
            "token": config.token,
            "auth_tokens": ordered_auth_tokens,
            "anthropic_model": config.anthropic_model,
            "default_opus_model": config.default_opus_model,
            "default_sonnet_model": config.default_sonnet_model,
            "default_haiku_model": config.default_haiku_model,
            "subagent_model": config.subagent_model,
            "effort_level": config.effort_level,
            "project_path": config.project_path,
            "proxy": {
                "http": asdict(config.proxy.http),
                "https": asdict(config.proxy.https),
                "socks5": asdict(config.proxy.socks5),
            },
            "recent_projects": config.recent_projects[:DEFAULT_RECENT_PROJECTS],
        }