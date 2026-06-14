from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.core.config_manager import ProxyConfig, ProxyItem
from src.ui.widgets.proxy_group import NetworkProxyGroup, ProxyToggleGroup


class ProxyGroupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_each_proxy_type_requires_ip_and_port(self) -> None:
        group = ProxyToggleGroup()
        for checkbox, protocol in (
            (group.http, "HTTP"),
            (group.https, "HTTPS"),
            (group.socks5, "Socks5"),
        ):
            checkbox.setChecked(True)
            ok, message = group.validate(ProxyConfig())
            self.assertFalse(ok)
            self.assertIn(protocol, message)
            self.assertIn("IP地址和端口号", message)
            checkbox.setChecked(False)

    def test_each_proxy_type_requires_ip(self) -> None:
        group = ProxyToggleGroup()
        settings = ProxyConfig(
            http=ProxyItem(port="8090"),
            https=ProxyItem(port="8090"),
            socks5=ProxyItem(port="8090"),
        )
        for checkbox in (group.http, group.https, group.socks5):
            checkbox.setChecked(True)
            ok, message = group.validate(settings)
            self.assertFalse(ok)
            self.assertIn("IP地址", message)
            checkbox.setChecked(False)

    def test_each_proxy_type_uses_requested_missing_port_message(self) -> None:
        group = ProxyToggleGroup()
        settings = ProxyConfig(
            http=ProxyItem(host="127.0.0.1"),
            https=ProxyItem(host="127.0.0.1"),
            socks5=ProxyItem(host="127.0.0.1"),
        )
        for checkbox in (group.http, group.https, group.socks5):
            checkbox.setChecked(True)
            ok, message = group.validate(settings)
            self.assertFalse(ok)
            self.assertIn("端口号", message)
            checkbox.setChecked(False)

    def test_network_proxy_group_round_trips_values(self) -> None:
        group = NetworkProxyGroup()
        for row in (group.http, group.https, group.socks5):
            row.host.setText("127.0.0.1")
            row.port.setText("8090")
            row.username.setText("user")
            row.password.setText("password")

        settings = group.collect_config()
        for item in (settings.http, settings.https, settings.socks5):
            self.assertEqual(item.host, "127.0.0.1")
            self.assertEqual(item.port, "8090")
            self.assertEqual(item.auth, "user:password")


if __name__ == "__main__":
    unittest.main()
