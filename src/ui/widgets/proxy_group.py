# 路径: src/ui/widgets/proxy_group.py
# 作用: 代理设置区域控件
# 校验：勾选某个代理时，至少要同时填入 IP 地址和端口号

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QWidget,
)

from src.core.config_manager import ProxyConfig, ProxyItem


class ProxyToggleGroup(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.http = QCheckBox("HTTP代理")
        self.https = QCheckBox("HTTPS代理")
        self.socks5 = QCheckBox("Socks5代理")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        for checkbox in (self.http, self.https, self.socks5):
            layout.addWidget(checkbox)
        layout.addStretch(1)

    def apply_config(self, enabled: dict[str, bool]) -> None:
        self.http.setChecked(bool(enabled.get("http", False)))
        self.https.setChecked(bool(enabled.get("https", False)))
        self.socks5.setChecked(bool(enabled.get("socks5", False)))

    def collect_config_data(self) -> dict[str, bool]:
        return {
            "http": self.http.isChecked(),
            "https": self.https.isChecked(),
            "socks5": self.socks5.isChecked(),
        }

    def set_ui_enabled(self, enabled: bool) -> None:
        for checkbox in (self.http, self.https, self.socks5):
            checkbox.setEnabled(enabled)

    def validate(self, settings: ProxyConfig) -> tuple[bool, str]:
        checks = (
            (self.http, settings.http, "HTTP代理"),
            (self.https, settings.https, "HTTPS代理"),
            (self.socks5, settings.socks5, "Socks5代理"),
        )
        for checkbox, item, label in checks:
            if not checkbox.isChecked():
                continue
            missing = []
            if not item.host.strip():
                missing.append("IP地址")
            if not item.port.strip():
                missing.append("端口号")
            if missing:
                return (
                    False,
                    f"您已勾选【{label}】，但网络代理设置中未填写"
                    f"{'和'.join(missing)}。\n\n"
                    "请在“鉴权设置 > 网络代理”中补充参数，或取消勾选该代理。",
                )
        return True, ""


class _NetworkProxyRow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.host = QLineEdit()
        self.host.setPlaceholderText("IP地址")
        self.port = QLineEdit()
        self.port.setPlaceholderText("端口")
        self.port.setMaximumWidth(110)
        self.username = QLineEdit()
        self.username.setPlaceholderText("用户名")
        self.password = QLineEdit()
        self.password.setPlaceholderText("密码")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.host, 2)
        layout.addWidget(self.port, 0)
        layout.addWidget(self.username, 1)
        layout.addWidget(self.password, 1)


class NetworkProxyGroup(QWidget):
    def __init__(self, settings: ProxyConfig | None = None) -> None:
        super().__init__()
        self.http = _NetworkProxyRow()
        self.https = _NetworkProxyRow()
        self.socks5 = _NetworkProxyRow()
        form = QFormLayout(self)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.addRow("HTTP代理", self.http)
        form.addRow("HTTPS代理", self.https)
        form.addRow("Socks5代理", self.socks5)
        self.apply_config(settings or ProxyConfig())

    def apply_config(self, settings: ProxyConfig) -> None:
        self._apply_row(self.http, settings.http)
        self._apply_row(self.https, settings.https)
        self._apply_row(self.socks5, settings.socks5)

    def collect_config(self) -> ProxyConfig:
        return ProxyConfig(
            http=self._collect_row(self.http),
            https=self._collect_row(self.https),
            socks5=self._collect_row(self.socks5),
        )

    @staticmethod
    def _apply_row(row: _NetworkProxyRow, item: ProxyItem) -> None:
        row.host.setText(item.host)
        row.port.setText(item.port)
        username, separator, password = (item.auth or "").partition(":")
        row.username.setText(username)
        row.password.setText(password if separator else "")

    @staticmethod
    def _collect_row(row: _NetworkProxyRow) -> ProxyItem:
        username = row.username.text().strip()
        password = row.password.text().strip()
        auth = f"{username}:{password}" if username or password else ""
        return ProxyItem(
            host=row.host.text().strip(),
            port=row.port.text().strip(),
            auth=auth,
        )
