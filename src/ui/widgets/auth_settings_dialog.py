# 路径: src/ui/widgets/auth_settings_dialog.py
# 作用: 鉴权设置弹窗

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.constants import (
    PROVIDER_CLAUDE_DEFAULT,
    PROVIDER_DEEPSEEK,
    PROVIDER_KIMI,
    PROVIDER_ZHIPU,
)


class AuthSettingsDialog(QDialog):
    def __init__(self, auth_tokens: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("鉴权设置")
        self.setModal(True)
        self.resize(700, 400)
        self.setMinimumSize(700, 400)

        font = QFont("Microsoft YaHei")
        font.setPointSize(12)
        self.setFont(font)

        self._token_edits: dict[str, QLineEdit] = {}

        self._build_ui(auth_tokens)
        self._apply_styles()

    def _build_ui(self, auth_tokens: dict[str, str]) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("为不同 Provider 单独保存鉴权值，留空表示不设置。")
        title.setWordWrap(True)
        root.addWidget(title)

        content_row = QHBoxLayout()
        content_row.setSpacing(12)

        self.tab_list = QListWidget()
        self.tab_list.setObjectName("authTabList")
        self.tab_list.setFixedWidth(160)
        self.tab_list.setSpacing(4)
        self.tab_list.setAlternatingRowColors(False)
        self.tab_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        self.stack = QStackedWidget()
        self.stack.setObjectName("authPageStack")

        tabs: list[tuple[str, str]] = [
            ("Claude", PROVIDER_CLAUDE_DEFAULT),
            ("DeepSeek", PROVIDER_DEEPSEEK),
            ("Kimi", PROVIDER_KIMI),
            ("GML", PROVIDER_ZHIPU),
        ]

        for title_text, provider_key in tabs:
            item = QListWidgetItem(title_text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setSizeHint(item.sizeHint().expandedTo(self._tab_item_size_hint()))
            self.tab_list.addItem(item)
            self.stack.addWidget(self._make_page(title_text, provider_key, auth_tokens))

        self.tab_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.tab_list.setCurrentRow(0)

        content_row.addWidget(self.tab_list)
        content_row.addWidget(self.stack, 1)
        root.addLayout(content_row, 1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("authDialogCancelButton")
        self.cancel_btn.clicked.connect(self.reject)

        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.setObjectName("authDialogConfirmButton")
        self.confirm_btn.clicked.connect(self.accept)

        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        button_row.addWidget(self.cancel_btn)
        button_row.addWidget(self.confirm_btn)
        root.addLayout(button_row)

    @staticmethod
    def _tab_item_size_hint():
        from PyQt6.QtCore import QSize

        return QSize(120, 44)

    def _make_page(self, title: str, provider_key: str, auth_tokens: dict[str, str]) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hint = QLabel(f"{title} API Token 鉴权")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.EchoMode.Password)
        edit.setPlaceholderText("可留空")
        edit.setText(auth_tokens.get(provider_key, ""))
        layout.addWidget(edit)

        self._token_edits[provider_key] = edit
        layout.addStretch(1)
        return page

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background-color: #ffffff;
            }
            QListWidget#authTabList {
                background-color: #f7f7f7;
                border: 1px solid #d9d9d9;
                border-radius: 8px;
                outline: none;
            }
            QListWidget#authTabList::item {
                color: #222222;
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 10px 12px;
                margin: 4px;
            }
            QListWidget#authTabList::item:selected {
                background-color: #2ea043;
                color: white;
            }
            QListWidget#authTabList::item:hover:!selected {
                background-color: #e9f5ec;
            }
            QWidget#authPageStack {
                background-color: #ffffff;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 6px 16px;
                min-height: 28px;
                color: white;
            }
            QPushButton#authDialogCancelButton {
                background-color: #6e7681;
            }
            QPushButton#authDialogConfirmButton {
                background-color: #2ea043;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #222222;
                border: 1px solid #cfcfcf;
                border-radius: 6px;
                padding: 3px 6px;
                min-height: 26px;
            }
            QLabel {
                color: #222222;
            }
            """
        )

    def get_auth_tokens(self) -> dict[str, str]:
        return {
            PROVIDER_CLAUDE_DEFAULT: self._token_edits[PROVIDER_CLAUDE_DEFAULT].text().strip(),
            PROVIDER_DEEPSEEK: self._token_edits[PROVIDER_DEEPSEEK].text().strip(),
            PROVIDER_KIMI: self._token_edits[PROVIDER_KIMI].text().strip(),
            PROVIDER_ZHIPU: self._token_edits[PROVIDER_ZHIPU].text().strip(),
        }