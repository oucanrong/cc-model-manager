from __future__ import annotations

from src.core.config_manager import ProxyConfig, ProxyItem


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
    https_url = _build_proxy_url(proxy.https, "https")
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