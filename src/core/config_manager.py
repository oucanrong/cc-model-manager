# 路径: C:\Users\oucan\Documents\vscode\claude_code启动器\src\core\config_manager.py
# 作用: 修复 provider 切换时代理配置互相干扰的问题，确保各 provider 配置完全独立

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

from .constants import (
    CLAUDE_LAUNCH_TARGET_DEFAULT,
    CLAUDE_LAUNCH_TARGET_OPTIONS,
    CODEX_PROVIDER_DEFAULTS,
    CODEX_LAUNCH_TARGET_DEFAULT,
    CODEX_LAUNCH_TARGET_OPTIONS,
    CODEX_PROVIDER_OFFICIAL,
    CODEX_PROVIDER_OPTIONS,
    CONFIG_PATH,
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
    DEFAULT_OPUS_MODEL,
    DEFAULT_SONNET_MODEL,
    DEFAULT_HAIKU_MODEL,
    DEFAULT_SUBAGENT_MODEL,
    DEFAULT_EFFORT_LEVEL,
    DEFAULT_RECENT_PROJECTS,
    PROVIDER_MINIMAX,
    PROVIDER_OPTIONS,
    get_provider_preset,
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
class ProviderSettings:
    base_url: str = ""
    token: str = ""
    anthropic_model: str = ""
    default_opus_model: str = ""
    default_sonnet_model: str = ""
    default_haiku_model: str = ""
    subagent_model: str = ""
    effort_level: str = ""
    # Kimi 专用
    enable_tool_search: str = "false"
    # GLM5 专用
    disable_nonessential_traffic: str = "1"
    api_timeout_ms: str = "3000000"
    # 小米MiMo / 方舟Coding Plan 专用
    has_completed_onboarding: str = "true"
    proxy: ProxyConfig = field(default_factory=ProxyConfig)


@dataclass
class CodexProviderSettings:
    base_url: str = ""
    token: str = ""
    model: str = ""
    reasoning_effort: str = ""
    proxy: ProxyConfig = field(default_factory=ProxyConfig)


@dataclass
class CodexConfig:
    provider: str = CODEX_PROVIDER_OFFICIAL
    launch_target: str = CODEX_LAUNCH_TARGET_DEFAULT
    project_path: str = ""
    recent_projects: list[str] = field(default_factory=list)
    provider_settings: dict[str, CodexProviderSettings] = field(default_factory=dict)


def create_default_codex_config() -> CodexConfig:
    settings = {}
    for provider_name in CODEX_PROVIDER_OPTIONS:
        defaults = CODEX_PROVIDER_DEFAULTS[provider_name]
        settings[provider_name] = CodexProviderSettings(
            base_url=str(defaults["base_url"]),
            model=str(defaults["default_model"]),
            reasoning_effort=str(defaults["default_reasoning_effort"]),
        )
    return CodexConfig(provider_settings=settings)


@dataclass
class AppConfig:
    provider: str = DEFAULT_PROVIDER
    claude_launch_target: str = CLAUDE_LAUNCH_TARGET_DEFAULT
    base_url: str = ""
    token: str = ""
    auth_tokens: dict[str, str] = field(default_factory=dict)
    anthropic_model: str = DEFAULT_MODEL
    default_opus_model: str = DEFAULT_OPUS_MODEL
    default_sonnet_model: str = DEFAULT_SONNET_MODEL
    default_haiku_model: str = DEFAULT_HAIKU_MODEL
    subagent_model: str = DEFAULT_SUBAGENT_MODEL
    effort_level: str = DEFAULT_EFFORT_LEVEL
    # Kimi 专用
    enable_tool_search: str = "false"
    # GLM5 专用
    disable_nonessential_traffic: str = "1"
    api_timeout_ms: str = "3000000"
    # 小米MiMo / 方舟Coding Plan 专用
    has_completed_onboarding: str = "true"
    project_path: str = ""
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    recent_projects: list[str] = field(default_factory=list)
    vscode_path: str = ""
    provider_settings: dict[str, ProviderSettings] = field(default_factory=dict)
    codex: CodexConfig = field(default_factory=create_default_codex_config)


class ConfigManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or CONFIG_PATH

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return AppConfig()
        config = self._from_dict(data)
        provider = config.provider if config.provider in PROVIDER_OPTIONS else DEFAULT_PROVIDER
        config.provider = provider
        self._sync_active_provider(config)
        return config

    def save(self, config: AppConfig) -> None:
        self._flush_active_provider(config)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._to_dict(config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _sync_active_provider(self, config: AppConfig) -> None:
        """将 provider_settings 中当前 provider 的配置同步到 config 顶层字段。"""
        preset = get_provider_preset(config.provider)
        ps = config.provider_settings.get(config.provider)
        if ps is None:
            ps = ProviderSettings(
                base_url="",
                token="",
                anthropic_model="",
                default_opus_model="",
                default_sonnet_model="",
                default_haiku_model="",
                subagent_model="",
                effort_level="",
                proxy=ProxyConfig(),
            )
            config.provider_settings[config.provider] = ps

        # 保证 base_url 使用 provider_settings 中保存的值，否则使用预设
        config.base_url = ps.base_url or preset.base_url
        config.token = ps.token or ""
        config.anthropic_model = ps.anthropic_model or preset.anthropic_model_default
        config.default_opus_model = ps.default_opus_model or preset.default_opus_model_default
        config.default_sonnet_model = ps.default_sonnet_model or preset.default_sonnet_model_default
        config.default_haiku_model = ps.default_haiku_model or preset.default_haiku_model_default
        config.subagent_model = ps.subagent_model or preset.subagent_model_default
        config.effort_level = ps.effort_level or preset.effort_level_default
        # 深拷贝代理配置——关键：确保 config.proxy 与 provider_settings[provider].proxy
        # 是两个完全独立的对象，防止后续 UI 修改 config.proxy 时污染已保存的 provider 配置
        config.proxy = copy.deepcopy(ps.proxy)
        # Kimi 专用参数
        config.enable_tool_search = ps.enable_tool_search or preset.enable_tool_search_default
        # GLM5 专用参数
        config.disable_nonessential_traffic = ps.disable_nonessential_traffic or preset.disable_nonessential_traffic_default
        config.api_timeout_ms = ps.api_timeout_ms or preset.api_timeout_ms_default
        # 小米MiMo / 方舟Coding Plan 专用参数
        config.has_completed_onboarding = ps.has_completed_onboarding or preset.has_completed_onboarding_default

    def _flush_active_provider(self, config: AppConfig) -> None:
        """将 config 顶层字段写回 provider_settings 中当前 provider 的条目。"""
        token = config.token.strip()
        config.auth_tokens[config.provider] = token
        ps = ProviderSettings(
            base_url=config.base_url,
            token=token,
            anthropic_model=config.anthropic_model,
            default_opus_model=config.default_opus_model,
            default_sonnet_model=config.default_sonnet_model,
            default_haiku_model=config.default_haiku_model,
            subagent_model=config.subagent_model,
            effort_level=config.effort_level,
            enable_tool_search=config.enable_tool_search,
            disable_nonessential_traffic=config.disable_nonessential_traffic,
            api_timeout_ms=config.api_timeout_ms,
            has_completed_onboarding=config.has_completed_onboarding,
            # 深拷贝代理配置——关键：确保保存到 provider_settings 的 proxy
            # 与 config.proxy 是完全独立的对象，互不干扰
            proxy=copy.deepcopy(config.proxy),
        )
        config.provider_settings[config.provider] = ps

    def _from_dict(self, data: dict[str, Any]) -> AppConfig:
        self._migrate_minimax_name(data)
        self._migrate_codex_ark_name(data)
        provider = data.get("provider", DEFAULT_PROVIDER)
        if provider not in PROVIDER_OPTIONS:
            provider = DEFAULT_PROVIDER
        auth_tokens = {p: str(data.get("auth_tokens", {}).get(p, "") or "") for p in PROVIDER_OPTIONS}
        provider_settings = {}
        for p, v in (data.get("provider_settings") or {}).items():
            proxy_data = v.get("proxy") or {}
            provider_settings[p] = ProviderSettings(
                base_url=str(v.get("base_url", "") or ""),
                token=str(v.get("token", "") or ""),
                anthropic_model=str(v.get("anthropic_model", "") or ""),
                default_opus_model=str(v.get("default_opus_model", "") or ""),
                default_sonnet_model=str(v.get("default_sonnet_model", "") or ""),
                default_haiku_model=str(v.get("default_haiku_model", "") or ""),
                subagent_model=str(v.get("subagent_model", "") or ""),
                effort_level=str(v.get("effort_level", "") or ""),
                enable_tool_search=str(v.get("enable_tool_search", "") or "false"),
                disable_nonessential_traffic=str(v.get("disable_nonessential_traffic", "") or "1"),
                api_timeout_ms=str(v.get("api_timeout_ms", "") or "3000000"),
                has_completed_onboarding=str(v.get("has_completed_onboarding", "") or "true"),
                proxy=ProxyConfig(
                    http=ProxyItem(**(proxy_data.get("http") or {})),
                    https=ProxyItem(**(proxy_data.get("https") or {})),
                    socks5=ProxyItem(**(proxy_data.get("socks5") or {})),
                ),
            )
        # 为 JSON 中不存在的 provider 初始化默认条目，每个 provider 获得独立的 ProxyConfig
        for p in PROVIDER_OPTIONS:
            if p not in provider_settings:
                preset = get_provider_preset(p)
                provider_settings[p] = ProviderSettings(
                    base_url="",
                    token=auth_tokens.get(p, ""),
                    anthropic_model=preset.anthropic_model_default,
                    default_opus_model=preset.default_opus_model_default,
                    default_sonnet_model=preset.default_sonnet_model_default,
                    default_haiku_model=preset.default_haiku_model_default,
                    subagent_model=preset.subagent_model_default,
                    effort_level=preset.effort_level_default,
                    # proxy 使用 default_factory 自动创建独立实例
                )
        codex_data = data.get("codex") or {}
        claude_launch_targets = {value for value, _ in CLAUDE_LAUNCH_TARGET_OPTIONS}
        claude_launch_target = str(
            data.get("claude_launch_target", CLAUDE_LAUNCH_TARGET_DEFAULT) or ""
        )
        if claude_launch_target not in claude_launch_targets:
            claude_launch_target = CLAUDE_LAUNCH_TARGET_DEFAULT
        codex_launch_targets = {value for value, _ in CODEX_LAUNCH_TARGET_OPTIONS}
        codex_launch_target = str(
            codex_data.get("launch_target", CODEX_LAUNCH_TARGET_DEFAULT) or ""
        )
        if codex_launch_target not in codex_launch_targets:
            codex_launch_target = CODEX_LAUNCH_TARGET_DEFAULT
        codex_provider = str(codex_data.get("provider", CODEX_PROVIDER_OFFICIAL) or "")
        if codex_provider not in CODEX_PROVIDER_OPTIONS:
            codex_provider = CODEX_PROVIDER_OFFICIAL
        codex_settings: dict[str, CodexProviderSettings] = {}
        raw_codex_settings = codex_data.get("provider_settings") or {}
        for provider_name in CODEX_PROVIDER_OPTIONS:
            raw = raw_codex_settings.get(provider_name) or {}
            defaults = CODEX_PROVIDER_DEFAULTS[provider_name]
            proxy_data = raw.get("proxy") or {}
            codex_settings[provider_name] = CodexProviderSettings(
                base_url=str(raw.get("base_url", "") or defaults["base_url"]),
                token=str(raw.get("token", "") or ""),
                model=str(raw.get("model", "") or defaults["default_model"]),
                reasoning_effort=str(
                    raw.get("reasoning_effort", "")
                    or defaults["default_reasoning_effort"]
                ),
                proxy=ProxyConfig(
                    http=ProxyItem(**(proxy_data.get("http") or {})),
                    https=ProxyItem(**(proxy_data.get("https") or {})),
                    socks5=ProxyItem(**(proxy_data.get("socks5") or {})),
                ),
            )

        return AppConfig(
            provider=provider,
            claude_launch_target=claude_launch_target,
            base_url=str(data.get("base_url", "") or ""),
            token=auth_tokens.get(provider, ""),
            auth_tokens=auth_tokens,
            anthropic_model=str(data.get("anthropic_model", "") or ""),
            default_opus_model=str(data.get("default_opus_model", "") or ""),
            default_sonnet_model=str(data.get("default_sonnet_model", "") or ""),
            default_haiku_model=str(data.get("default_haiku_model", "") or ""),
            subagent_model=str(data.get("subagent_model", "") or ""),
            effort_level=str(data.get("effort_level", "") or ""),
            enable_tool_search=str(data.get("enable_tool_search", "") or "false"),
            disable_nonessential_traffic=str(data.get("disable_nonessential_traffic", "") or "1"),
            api_timeout_ms=str(data.get("api_timeout_ms", "") or "3000000"),
            has_completed_onboarding=str(data.get("has_completed_onboarding", "") or "true"),
            project_path=str(data.get("project_path", "") or ""),
            # 顶层 proxy 始终初始化为空——后续由 _sync_active_provider 从
            # provider_settings[provider] 中深拷贝加载当前 provider 的真实代理配置
            proxy=ProxyConfig(),
            recent_projects=data.get("recent_projects", []) or [],
            vscode_path=str(data.get("vscode_path", "") or ""),
            provider_settings=provider_settings,
            codex=CodexConfig(
                provider=codex_provider,
                launch_target=codex_launch_target,
                project_path=str(codex_data.get("project_path", "") or ""),
                recent_projects=codex_data.get("recent_projects", []) or [],
                provider_settings=codex_settings,
            ),
        )

    @staticmethod
    def _migrate_minimax_name(data: dict[str, Any]) -> None:
        legacy = "MINIMAX"
        if data.get("provider") == legacy:
            data["provider"] = PROVIDER_MINIMAX
        auth_tokens = data.get("auth_tokens")
        if isinstance(auth_tokens, dict) and legacy in auth_tokens:
            auth_tokens.setdefault(PROVIDER_MINIMAX, auth_tokens.pop(legacy))
        provider_settings = data.get("provider_settings")
        if isinstance(provider_settings, dict) and legacy in provider_settings:
            provider_settings.setdefault(PROVIDER_MINIMAX, provider_settings.pop(legacy))

    @staticmethod
    def _migrate_codex_ark_name(data: dict[str, Any]) -> None:
        legacy = "方舟 Coding Plan"
        current = "方舟Coding Plan"
        codex = data.get("codex")
        if not isinstance(codex, dict):
            return
        if codex.get("provider") == legacy:
            codex["provider"] = current
        settings = codex.get("provider_settings")
        if isinstance(settings, dict) and legacy in settings:
            settings.setdefault(current, settings.pop(legacy))

    def _to_dict(self, config: AppConfig) -> dict[str, Any]:
        ps_dict = {}
        for p in PROVIDER_OPTIONS:
            ps = config.provider_settings.get(p, ProviderSettings())
            ps_dict[p] = {
                "base_url": ps.base_url,
                "token": ps.token,
                "anthropic_model": ps.anthropic_model,
                "default_opus_model": ps.default_opus_model,
                "default_sonnet_model": ps.default_sonnet_model,
                "default_haiku_model": ps.default_haiku_model,
                "subagent_model": ps.subagent_model,
                "effort_level": ps.effort_level,
                "enable_tool_search": ps.enable_tool_search,
                "disable_nonessential_traffic": ps.disable_nonessential_traffic,
                "api_timeout_ms": ps.api_timeout_ms,
                "has_completed_onboarding": ps.has_completed_onboarding,
                "proxy": {
                    "http": {"enabled": ps.proxy.http.enabled, "host": ps.proxy.http.host, "port": ps.proxy.http.port, "auth": ps.proxy.http.auth},
                    "https": {"enabled": ps.proxy.https.enabled, "host": ps.proxy.https.host, "port": ps.proxy.https.port, "auth": ps.proxy.https.auth},
                    "socks5": {"enabled": ps.proxy.socks5.enabled, "host": ps.proxy.socks5.host, "port": ps.proxy.socks5.port, "auth": ps.proxy.socks5.auth},
                },
            }
        codex_settings = {}
        for provider_name in CODEX_PROVIDER_OPTIONS:
            defaults = CODEX_PROVIDER_DEFAULTS[provider_name]
            setting = config.codex.provider_settings.get(
                provider_name,
                CodexProviderSettings(
                    base_url=str(defaults["base_url"]),
                    model=str(defaults["default_model"]),
                    reasoning_effort=str(defaults["default_reasoning_effort"]),
                ),
            )
            codex_settings[provider_name] = {
                "base_url": setting.base_url,
                "token": setting.token,
                "model": setting.model,
                "reasoning_effort": setting.reasoning_effort,
                "proxy": {
                    "http": asdict(setting.proxy.http),
                    "https": asdict(setting.proxy.https),
                    "socks5": asdict(setting.proxy.socks5),
                },
            }

        return {
            "provider": config.provider,
            "claude_launch_target": config.claude_launch_target,
            "auth_tokens": config.auth_tokens,
            "project_path": config.project_path,
            "recent_projects": config.recent_projects[:DEFAULT_RECENT_PROJECTS],
            "vscode_path": config.vscode_path,
            "provider_settings": ps_dict,
            "codex": {
                "provider": config.codex.provider,
                "launch_target": config.codex.launch_target,
                "project_path": config.codex.project_path,
                "recent_projects": config.codex.recent_projects[:DEFAULT_RECENT_PROJECTS],
                "provider_settings": codex_settings,
            },
        }
