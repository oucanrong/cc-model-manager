from __future__ import annotations

import unittest

from src.core.config_manager import ProxyConfig, ProxyItem
from src.services.proxy_service import (
    apply_proxy_env,
    build_codex_proxy_env,
    build_proxy_env,
    codex_has_only_socks5,
)


class ProxyServiceTests(unittest.TestCase):
    def test_https_destination_uses_http_connect_proxy_url(self) -> None:
        proxy = ProxyConfig(
            https=ProxyItem(enabled=True, host="127.0.0.1", port="8090"),
        )

        env = build_proxy_env(proxy)

        self.assertEqual(env["HTTPS_PROXY"], "http://127.0.0.1:8090")
        self.assertEqual(env["https_proxy"], "http://127.0.0.1:8090")

    def test_disabled_proxy_clears_inherited_environment(self) -> None:
        env = {
            "PATH": "test",
            "HTTP_PROXY": "http://old-http",
            "https_proxy": "http://old-https",
            "ALL_PROXY": "socks5://old-socks",
            "WSS_PROXY": "http://old-websocket",
        }

        apply_proxy_env(env, ProxyConfig(), for_codex=True)

        self.assertEqual(env, {"PATH": "test"})

    def test_codex_prefers_http_connect_and_omits_all_proxy(self) -> None:
        proxy = ProxyConfig(
            http=ProxyItem(enabled=True, host="127.0.0.1", port="8080"),
            https=ProxyItem(enabled=True, host="127.0.0.1", port="8443"),
            socks5=ProxyItem(enabled=True, host="127.0.0.1", port="1080"),
        )

        env = build_codex_proxy_env(proxy)

        self.assertEqual(env["HTTP_PROXY"], "http://127.0.0.1:8080")
        self.assertEqual(env["HTTPS_PROXY"], "http://127.0.0.1:8443")
        self.assertEqual(env["WS_PROXY"], "http://127.0.0.1:8080")
        self.assertEqual(env["WSS_PROXY"], "http://127.0.0.1:8443")
        self.assertNotIn("ALL_PROXY", env)

    def test_codex_http_proxy_is_used_as_https_fallback(self) -> None:
        proxy = ProxyConfig(
            http=ProxyItem(enabled=True, host="127.0.0.1", port="8090"),
        )

        env = build_codex_proxy_env(proxy)

        self.assertEqual(env["HTTP_PROXY"], "http://127.0.0.1:8090")
        self.assertEqual(env["HTTPS_PROXY"], "http://127.0.0.1:8090")

    def test_codex_only_socks5_is_rejected(self) -> None:
        proxy = ProxyConfig(
            socks5=ProxyItem(enabled=True, host="127.0.0.1", port="8090"),
        )

        self.assertTrue(codex_has_only_socks5(proxy))
        proxy.http = ProxyItem(enabled=True, host="127.0.0.1", port="8090")
        self.assertFalse(codex_has_only_socks5(proxy))


if __name__ == "__main__":
    unittest.main()
