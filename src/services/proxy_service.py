from __future__ import annotations

from src.core.config_manager import ProxyConfig, ProxyItem

PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "WS_PROXY",
    "WSS_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "ws_proxy",
    "wss_proxy",
)


def _build_proxy_url(item: ProxyItem, scheme: str) -> str | None:
    if not item.enabled:
        return None
    if not item.host.strip() or not item.port.strip():
        return None

    auth = item.auth.strip()
    if auth:
        return f"{scheme}://{auth}@{item.host.strip()}:{item.port.strip()}"
    return f"{scheme}://{item.host.strip()}:{item.port.strip()}"


def build_proxy_env(proxy: ProxyConfig) -> dict[str, str]:
    env: dict[str, str] = {}
    http_url = _build_proxy_url(proxy.http, "http")
    # HTTPS_PROXY describes HTTPS destination traffic. Local proxy clients
    # normally expose an HTTP CONNECT endpoint, so its URL remains http://.
    https_url = _build_proxy_url(proxy.https, "http")
    socks5_url = _build_proxy_url(proxy.socks5, "socks5")

    if http_url:
        env["HTTP_PROXY"] = http_url
        env["http_proxy"] = http_url
    if https_url:
        env["HTTPS_PROXY"] = https_url
        env["https_proxy"] = https_url
    if socks5_url:
        env["ALL_PROXY"] = socks5_url
        env["all_proxy"] = socks5_url

    return env


def build_codex_proxy_env(proxy: ProxyConfig) -> dict[str, str]:
    """Build the HTTP CONNECT proxy environment supported reliably by Codex."""
    http_url = _build_proxy_url(proxy.http, "http")
    https_url = _build_proxy_url(proxy.https, "http")
    if not http_url and not https_url:
        return {}

    http_proxy = http_url or https_url
    https_proxy = https_url or http_url
    return {
        "HTTP_PROXY": http_proxy,
        "http_proxy": http_proxy,
        "HTTPS_PROXY": https_proxy,
        "https_proxy": https_proxy,
        "WS_PROXY": http_proxy,
        "ws_proxy": http_proxy,
        "WSS_PROXY": https_proxy,
        "wss_proxy": https_proxy,
    }


def apply_proxy_env(
    env: dict[str, str],
    proxy: ProxyConfig,
    *,
    for_codex: bool = False,
) -> dict[str, str]:
    """Remove inherited proxy variables and apply only the selected settings."""
    for key in PROXY_ENV_KEYS:
        env.pop(key, None)

    proxy_env = (
        build_codex_proxy_env(proxy)
        if for_codex
        else build_proxy_env(proxy)
    )
    env.update(proxy_env)
    if proxy_env:
        _merge_no_proxy(env, ("127.0.0.1", "localhost"))
    return env


def codex_has_only_socks5(proxy: ProxyConfig) -> bool:
    has_http = _build_proxy_url(proxy.http, "http") is not None
    has_https = _build_proxy_url(proxy.https, "http") is not None
    has_socks5 = _build_proxy_url(proxy.socks5, "socks5") is not None
    return has_socks5 and not has_http and not has_https


def _merge_no_proxy(env: dict[str, str], hosts: tuple[str, ...]) -> None:
    existing = env.get("NO_PROXY") or env.get("no_proxy") or ""
    values = [value.strip() for value in existing.split(",") if value.strip()]
    known = {value.casefold() for value in values}
    for host in hosts:
        if host.casefold() not in known:
            values.append(host)
    merged = ",".join(values)
    env["NO_PROXY"] = merged
    env["no_proxy"] = merged
