# 路径: src/ui/widgets/codex_parameter_group.py
# 作用: Codex 标签的 Provider、单模型、推理强度和工作目录控件

from __future__ import annotations

from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
)

from src.core.config_manager import CodexConfig
from src.core.constants import (
    CODEX_LAUNCH_TARGET_DEFAULT,
    CODEX_LAUNCH_TARGET_OPTIONS,
    CODEX_PROVIDER_DEFAULTS,
    CODEX_PROVIDER_OFFICIAL,
    CODEX_PROVIDER_OPTIONS,
    get_codex_context_window,
)


class CodexParameterGroup(QGroupBox):
    def __init__(self, on_pick_project) -> None:
        super().__init__("启动参数")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(CODEX_PROVIDER_OPTIONS)
        self.model_combo = QComboBox()
        self.reasoning_combo = QComboBox()
        self.context_window_edit = QLineEdit()
        self.context_window_edit.setReadOnly(True)
        self.launch_target_combo = QComboBox()
        for value, label in CODEX_LAUNCH_TARGET_OPTIONS:
            self.launch_target_combo.addItem(label, value)
        self.project_path_edit = QLineEdit()
        self.pick_btn = QPushButton("选择工作目录")
        self.pick_btn.setObjectName("pickProjectButton")
        self.pick_btn.clicked.connect(on_pick_project)

        for widget in (
            self.provider_combo,
            self.model_combo,
            self.reasoning_combo,
            self.context_window_edit,
            self.launch_target_combo,
            self.project_path_edit,
        ):
            widget.setMinimumHeight(26)
            widget.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
        self.pick_btn.setMinimumHeight(26)
        self.pick_btn.setMinimumWidth(120)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        self._layout = QGridLayout(self)
        self._layout.setColumnStretch(1, 1)
        self._layout.setHorizontalSpacing(10)
        self._layout.setVerticalSpacing(10)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setRowStretch(6, 1)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.provider_label = QLabel("API供应商")
        self._layout.addWidget(self.provider_label, 0, 0)
        self._layout.addWidget(self.provider_combo, 0, 1)
        self.model_label = QLabel("模型名称")
        self._layout.addWidget(self.model_label, 1, 0)
        self._layout.addWidget(self.model_combo, 1, 1)
        self.context_window_label = QLabel("输入上下文最大tokens")
        self._layout.addWidget(self.context_window_label, 2, 0)
        self._layout.addWidget(self.context_window_edit, 2, 1)
        self.reasoning_label = QLabel("推理强度")
        self._layout.addWidget(self.reasoning_label, 3, 0)
        self._layout.addWidget(self.reasoning_combo, 3, 1)
        self.launch_target_label = QLabel("启动目标")
        self._layout.addWidget(self.launch_target_label, 4, 0)
        self._layout.addWidget(self.launch_target_combo, 4, 1)
        self._layout.addWidget(self.pick_btn, 5, 0)
        self._layout.addWidget(self.project_path_edit, 5, 1)
        self.model_combo.currentTextChanged.connect(self._refresh_context_window)
        self.set_provider(self.provider_combo.currentText())

    def set_provider(self, provider: str) -> None:
        defaults = CODEX_PROVIDER_DEFAULTS[provider]
        blocker = QSignalBlocker(self.model_combo)
        self.model_combo.clear()
        self.model_combo.addItems(list(defaults["models"]))
        if defaults["default_model"]:
            self.model_combo.setCurrentText(str(defaults["default_model"]))
        reasoning_blocker = QSignalBlocker(self.reasoning_combo)
        self.reasoning_combo.clear()
        self.reasoning_combo.addItems(list(defaults["reasoning_options"]))
        if defaults["default_reasoning_effort"]:
            self.reasoning_combo.setCurrentText(
                str(defaults["default_reasoning_effort"])
            )
        del reasoning_blocker
        del blocker
        visible = provider != CODEX_PROVIDER_OFFICIAL
        context_visible = visible and self.current_context_window() is not None
        reasoning_visible = visible and bool(defaults["reasoning_options"])
        self.model_label.setVisible(visible)
        self.model_combo.setVisible(visible)
        self.context_window_label.setVisible(context_visible)
        self.context_window_edit.setVisible(context_visible)
        self.reasoning_label.setVisible(reasoning_visible)
        self.reasoning_combo.setVisible(reasoning_visible)
        self._refresh_context_window()

    def current_context_window(self) -> int | None:
        return get_codex_context_window(
            self.provider_combo.currentText(),
            self.model_combo.currentText(),
        )

    def _refresh_context_window(self) -> None:
        context_window = self.current_context_window()
        self.context_window_edit.setText(
            str(context_window) if context_window is not None else ""
        )
        visible = (
            self.provider_combo.currentText() != CODEX_PROVIDER_OFFICIAL
            and context_window is not None
        )
        self.context_window_label.setVisible(visible)
        self.context_window_edit.setVisible(visible)

    def apply_config(self, config: CodexConfig) -> None:
        blocker = QSignalBlocker(self.provider_combo)
        self.provider_combo.setCurrentText(config.provider)
        del blocker
        self.set_provider(config.provider)
        setting = config.provider_settings[config.provider]
        if self.model_combo.findText(setting.model) >= 0:
            self.model_combo.setCurrentText(setting.model)
        if self.reasoning_combo.findText(setting.reasoning_effort) >= 0:
            self.reasoning_combo.setCurrentText(setting.reasoning_effort)
        self.set_launch_target(config.launch_target)
        self.project_path_edit.setText(config.project_path)

    def set_ui_enabled(self, enabled: bool) -> None:
        for widget in (
            self.provider_combo,
            self.model_combo,
            self.context_window_edit,
            self.reasoning_combo,
            self.launch_target_combo,
            self.project_path_edit,
            self.pick_btn,
        ):
            widget.setEnabled(enabled)

    def current_launch_target(self) -> str:
        value = self.launch_target_combo.currentData()
        return str(value or CODEX_LAUNCH_TARGET_DEFAULT)

    def set_launch_target(self, value: str) -> None:
        index = self.launch_target_combo.findData(value)
        if index < 0:
            index = self.launch_target_combo.findData(CODEX_LAUNCH_TARGET_DEFAULT)
        self.launch_target_combo.setCurrentIndex(index)
