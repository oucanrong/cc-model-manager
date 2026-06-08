from __future__ import annotations

import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel, QListWidget, QTabWidget

from src.ui.main_window import MainWindow
from src.ui.widgets.auth_settings_dialog import AuthSettingsDialog
from src.core.config_manager import CodexProviderSettings, ProviderSettings
from src.core.constants import APP_NAME


class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_has_two_product_tabs(self) -> None:
        window = MainWindow()
        try:
            window.show()
            QApplication.processEvents()
            self.assertEqual(APP_NAME, "cc模型管理器v2.1")
            self.assertEqual(window.windowTitle(), APP_NAME)
            self.assertEqual(window.product_tabs.count(), 2)
            self.assertEqual(window.width(), 760)
            self.assertEqual(window.height(), 900)
            self.assertEqual(window.minimumWidth(), 760)
            self.assertEqual(window.minimumHeight(), 600)
            self.assertEqual(window.product_tabs.tabText(0), "Claude Code")
            self.assertEqual(window.product_tabs.tabText(1), "Codex")
            self.assertFalse(window.product_tabs.tabBar().expanding())
            self.assertEqual(window.product_tabs.tabBar().height(), 36)
            self.assertEqual(window.product_tabs.tabBar().tabRect(0).height(), 36)
            self.assertEqual(window.auth_btn.height(), 36)
            self.assertIs(window.auth_btn.parent(), window.product_tabs)
            self.assertEqual(
                window.product_tabs.tabBar().mapToGlobal(
                    window.product_tabs.tabBar().rect().topLeft()
                ).y(),
                window.auth_btn.mapToGlobal(window.auth_btn.rect().topLeft()).y(),
            )
            auth_right = window.auth_btn.mapTo(
                window.product_tabs,
                window.auth_btn.rect().bottomRight(),
            ).x()
            self.assertEqual(
                window.product_tabs.rect().right() - auth_right,
                12,
            )
            window.resize(1000, 760)
            QApplication.processEvents()
            resized_auth_right = window.auth_btn.mapTo(
                window.product_tabs,
                window.auth_btn.rect().bottomRight(),
            ).x()
            self.assertEqual(
                window.product_tabs.rect().right() - resized_auth_right,
                12,
            )
            self.assertIn("min-width: 92px", window.styleSheet())
            self.assertIn("min-height: 24px", window.styleSheet())
            self.assertIn("background-color: #2ea043", window.styleSheet())
            self.assertEqual(window.parameter_group.provider_label.text(), "API供应商")
            self.assertEqual(
                window.codex_parameter_group.provider_label.text(),
                "API供应商",
            )
            self.assertEqual(
                window.codex_parameter_group.model_label.text(),
                "模型名称",
            )
            self.assertEqual(
                window.codex_parameter_group.context_window_label.text(),
                "输入上下文最大tokens",
            )
            self.assertEqual(
                window.codex_parameter_group.reasoning_label.text(),
                "推理强度",
            )
            self.assertEqual(window.parameter_group._label_model_main.text(), "默认模型")
            self.assertEqual(
                window.parameter_group._label_model_opus.text(),
                "最复杂任务模型",
            )
            self.assertEqual(
                window.parameter_group._label_model_sonnet.text(),
                "日常编码模型",
            )
            self.assertEqual(
                window.parameter_group._label_model_haiku.text(),
                "简单任务模型",
            )
            self.assertEqual(
                window.parameter_group._label_model_subagent.text(),
                "子代理模型",
            )
            self.assertEqual(window.parameter_group._label_effort.text(), "推理强度")
            self.assertEqual(
                window.parameter_group._label_enable_tool_search.text(),
                "启用工具搜索",
            )
            self.assertEqual(
                window.parameter_group._label_api_timeout_ms.text(),
                "API请求超时时间（毫秒）",
            )
            self.assertEqual(
                window.parameter_group._label_disable_nonessential_traffic.text(),
                "禁用非必要网络流量",
            )
            self.assertEqual(
                window.parameter_group._label_has_completed_onboarding.text(),
                "跳过首次引导",
            )
            self.assertEqual(window.parameter_group.launch_target_label.text(), "启动目标")
            self.assertEqual(
                [
                    window.parameter_group.launch_target_combo.itemText(index)
                    for index in range(
                        window.parameter_group.launch_target_combo.count()
                    )
                ],
                [
                    "启动Claude Code cli版",
                    "启动vscode",
                    "升级Claude Code cli版",
                ],
            )
            self.assertEqual(
                window.parameter_group.current_launch_target(),
                window.config.claude_launch_target,
            )
            self.assertEqual(
                [
                    window.codex_parameter_group.launch_target_combo.itemText(index)
                    for index in range(
                        window.codex_parameter_group.launch_target_combo.count()
                    )
                ],
                [
                    "启动codex桌面版",
                    "启动codex cli版",
                    "启动vscode",
                    "升级codex cli版",
                ],
            )
            self.assertEqual(
                window.codex_parameter_group.current_launch_target(),
                window.config.codex.launch_target,
            )
            self.assertEqual(window.start_btn.text(), "启动")
            self.assertEqual(window.codex_start_btn.text(), "启动")
            self.assertEqual(
                window.status_label.text(),
                f"Provider: {window.config.provider} | "
                f"项目目录: {window.config.project_path or '未选择'}",
            )
            self.assertEqual(
                window.codex_status_label.text(),
                f"Provider: {window.config.codex.provider} | "
                f"项目目录: {window.config.codex.project_path or '未选择'}",
            )
            self.assertEqual(
                window.parameter_group.height(),
                window.codex_parameter_group.height(),
            )
            self.assertEqual(
                window.parameter_group.provider_combo.height(),
                window.codex_parameter_group.provider_combo.height(),
            )
            self.assertEqual(
                window.parameter_group.provider_combo.x(),
                window.codex_parameter_group.provider_combo.x(),
            )

            for height in (900, 600):
                window.resize(760, height)
                QApplication.processEvents()
                for button in (window.start_btn, window.codex_start_btn):
                    parent = button.parentWidget()
                    button_bottom = button.mapTo(
                        parent,
                        button.rect().bottomLeft(),
                    ).y()
                    self.assertLessEqual(parent.height() - button_bottom, 20)

            def assert_fixed_row_spacing(group) -> None:
                visible_controls = []
                for row in range(group._layout.rowCount()):
                    item = group._layout.itemAtPosition(row, 1)
                    if item is not None and item.widget().isVisible():
                        visible_controls.append(item.widget())
                gaps = []
                for previous, current in zip(
                    visible_controls,
                    visible_controls[1:],
                ):
                    gaps.append(
                        current.y() - (previous.y() + previous.height())
                    )
                self.assertTrue(gaps)
                self.assertTrue(
                    all(
                        group._layout.verticalSpacing()
                        <= gap
                        <= group._layout.verticalSpacing() + 1
                        for gap in gaps
                    )
                )
                self.assertLessEqual(max(gaps) - min(gaps), 1)

            window.product_tabs.setCurrentIndex(0)
            window.parameter_group.provider_combo.setCurrentText(
                "Claude官方接口"
            )
            QApplication.processEvents()
            assert_fixed_row_spacing(window.parameter_group)

            window.product_tabs.setCurrentIndex(1)
            window.codex_parameter_group.provider_combo.setCurrentText(
                "Codex官方接口"
            )
            QApplication.processEvents()
            assert_fixed_row_spacing(window.codex_parameter_group)
        finally:
            window._loading = True
            window.close()

    def test_codex_status_summary_tracks_provider_project_and_reset(self) -> None:
        window = MainWindow()
        try:
            with patch.object(window.config_manager, "save"):
                window.codex_parameter_group.project_path_edit.clear()
                window.codex_parameter_group.provider_combo.setCurrentText(
                    "DeepSeek"
                )
                window._auto_save()
                QApplication.processEvents()
                self.assertEqual(
                    window.codex_status_label.text(),
                    "Provider: DeepSeek | 项目目录: 未选择",
                )

                window.codex_parameter_group.project_path_edit.setText(
                    r"C:\workspace\codex-project"
                )
                window._auto_save()
                self.assertEqual(
                    window.codex_status_label.text(),
                    r"Provider: DeepSeek | 项目目录: C:\workspace\codex-project",
                )

                window.reset_codex_form()
                self.assertEqual(
                    window.codex_status_label.text(),
                    "Provider: DeepSeek | 项目目录: 未选择",
                )
                window._autosave_timer.stop()
        finally:
            window._loading = True
            window.close()

    def test_auth_dialog_uses_compact_green_tabs(self) -> None:
        window = MainWindow()
        dialog = AuthSettingsDialog(
            window.config.provider_settings,
            window.config.codex.provider_settings,
        )
        try:
            dialog.show()
            QApplication.processEvents()
            self.assertGreaterEqual(dialog.height(), 760)
            nav_lists = dialog.findChildren(QListWidget, "authTabList")
            self.assertEqual(len(nav_lists), 2)
            self.assertTrue(all(nav.width() == 170 for nav in nav_lists))
            self.assertTrue(all(nav.sizeHintForRow(0) == 22 for nav in nav_lists))
            tabs = dialog.findChild(QTabWidget, "authProductTabs")
            self.assertEqual(tabs.tabBar().height(), 36)
            self.assertEqual(tabs.tabBar().tabRect(0).height(), 36)
            claude_nav = next(
                nav
                for nav in nav_lists
                if any(
                    nav.item(row).text() == "Claude中转"
                    for row in range(nav.count())
                )
            )
            codex_nav = next(
                nav
                for nav in nav_lists
                if any(
                    nav.item(row).text() == "GPT中转"
                    for row in range(nav.count())
                )
            )
            tabs.setCurrentIndex(0)
            QApplication.processEvents()
            claude_size = claude_nav.size()
            tabs.setCurrentIndex(1)
            QApplication.processEvents()
            self.assertEqual(claude_size, codex_nav.size())
            self.assertIn("min-width: 92px", dialog.styleSheet())
            self.assertIn("background: #2ea043", dialog.styleSheet())
            label_text = "\n".join(
                label.text() for label in dialog.findChildren(QLabel)
            )
            nav_text = "\n".join(
                nav.item(row).text()
                for nav in nav_lists
                for row in range(nav.count())
            )
            self.assertIn("智谱GLM", nav_text)
            self.assertIn("MiniMax", nav_text)
            self.assertIn("方舟Coding Plan", nav_text)
            self.assertNotIn("方舟 Coding Plan", nav_text)
            self.assertNotIn("MINIMAX", nav_text)
            self.assertEqual(
                dialog._claude_fields["Claude中转"][0].placeholderText(),
                "https://api.example.com",
            )
            self.assertEqual(
                dialog._codex_fields["GPT中转"][0].placeholderText(),
                "https://api.example.com/v1",
            )
            self.assertNotIn(
                "Claude Code 与 Codex 的鉴权信息相互独立",
                label_text,
            )
            self.assertNotIn("Codex 官方接口沿用用户现有的", label_text)
        finally:
            dialog.close()
            window._loading = True
            window.close()

    def test_codex_context_window_tracks_provider_and_model(self) -> None:
        window = MainWindow()
        try:
            group = window.codex_parameter_group
            group.provider_combo.setCurrentText("阿里千问")
            QApplication.processEvents()
            self.assertTrue(group.context_window_edit.isReadOnly())
            group.model_combo.setCurrentText("qwen3.7-max")
            self.assertEqual(group.context_window_edit.text(), "1000000")
            self.assertEqual(
                [group.reasoning_combo.itemText(index) for index in range(
                    group.reasoning_combo.count()
                )],
                ["none", "minimal", "low", "medium", "high"],
            )
            self.assertEqual(group.reasoning_combo.currentText(), "medium")
            group.model_combo.setCurrentText("qwen3.6-flash")
            QApplication.processEvents()
            self.assertEqual(group.context_window_edit.text(), "256000")

            group.provider_combo.setCurrentText("MiniMax")
            QApplication.processEvents()
            self.assertEqual(group.context_window_edit.text(), "512000")
            self.assertFalse(group.reasoning_combo.isVisible())

            group.provider_combo.setCurrentText("GPT中转")
            QApplication.processEvents()
            self.assertEqual(group.model_combo.currentText(), "gpt-5.5")
            self.assertEqual(group.context_window_edit.text(), "")
            self.assertFalse(group.context_window_edit.isVisible())
            self.assertEqual(
                [group.reasoning_combo.itemText(index) for index in range(
                    group.reasoning_combo.count()
                )],
                ["minimal", "low", "medium", "high", "xhigh"],
            )
        finally:
            window._loading = True
            window.close()

    def test_empty_relay_base_urls_remain_empty_and_use_placeholders(self) -> None:
        dialog = AuthSettingsDialog(
            {"Claude中转": ProviderSettings()},
            {"GPT中转": CodexProviderSettings()},
        )
        try:
            dialog.show()
            QApplication.processEvents()
            claude_url = dialog._claude_fields["Claude中转"][0]
            codex_url = dialog._codex_fields["GPT中转"][0]
            self.assertEqual(claude_url.text(), "")
            self.assertEqual(claude_url.placeholderText(), "https://api.example.com")
            self.assertEqual(codex_url.text(), "")
            self.assertEqual(codex_url.placeholderText(), "https://api.example.com/v1")
            self.assertEqual(
                dialog.get_provider_settings()["Claude中转"].base_url,
                "",
            )
            self.assertEqual(
                dialog.get_codex_settings()["GPT中转"].base_url,
                "",
            )
            claude_url.setFocus()
            QApplication.processEvents()
            self.assertEqual(claude_url.placeholderText(), "")
            codex_url.setFocus()
            QApplication.processEvents()
            self.assertEqual(
                claude_url.placeholderText(),
                "https://api.example.com",
            )
        finally:
            dialog.close()

    def test_latest_upgrade_result_shows_no_upgrade_dialog(self) -> None:
        window = MainWindow()
        try:
            with patch("src.ui.main_window._show_info_dialog") as dialog:
                window.worker = SimpleNamespace(
                    upgrade_only=True,
                    already_latest=True,
                )
                window._on_worker_finished(0)
            self.assertEqual(
                window.status_label.text(),
                "Claude Code 已是最新版本，无须升级。",
            )
            dialog.assert_called_once_with(
                window,
                "无需升级",
                "Claude Code 已是最新版本，无须升级。",
            )

            with patch("src.ui.main_window._show_info_dialog") as dialog:
                window.codex_worker = SimpleNamespace(
                    upgrade_only=True,
                    already_latest=True,
                )
                window._on_codex_finished(0)
            self.assertEqual(
                window.codex_status_label.text(),
                "Codex CLI 已是最新版本，无须升级。",
            )
            dialog.assert_called_once_with(
                window,
                "无需升级",
                "Codex CLI 已是最新版本，无须升级。",
            )
        finally:
            window.worker = None
            window.codex_worker = None
            window._loading = True
            window.close()

    def test_codex_provider_switch_preserves_previous_provider_values(self) -> None:
        window = MainWindow()
        try:
            window._loading = True
            window.config.codex.provider = "DeepSeek"
            window.codex_parameter_group.apply_config(window.config.codex)
            window._loading = False
            window.codex_parameter_group.model_combo.setCurrentText("deepseek-v4-flash")
            window.codex_proxy_group.http.enabled.setChecked(True)
            window.codex_proxy_group.http.host.setText("127.0.0.1")
            window.codex_proxy_group.http.port.setText("8090")
            window.codex_parameter_group.provider_combo.setCurrentText("Kimi")
            saved = window.config.codex.provider_settings["DeepSeek"]
            self.assertEqual(saved.model, "deepseek-v4-flash")
            self.assertEqual(saved.proxy.http.host, "127.0.0.1")
            self.assertEqual(saved.proxy.http.port, "8090")
        finally:
            window._loading = True
            window.close()

    def test_claude_vscode_target_only_shows_guidance_and_disables_start(self) -> None:
        window = MainWindow()
        try:
            self.assertNotIn(
                "用户需要自行在vscode中安装claude code插件。",
                window.log_console.toPlainText(),
            )
            with (
                patch.object(window.config_manager, "save"),
                patch("src.ui.main_window._show_info_dialog") as dialog,
            ):
                window.parameter_group.set_launch_target("cli")
                window.parameter_group.set_launch_target("vscode")
                window._autosave_timer.stop()

            dialog.assert_called_once_with(
                window,
                "VS Code使用说明",
                "1. 请在vscode中删除claude code插件。"
                "如果已删除或未安装，继续第2步。\n"
                '2. 然后在启动目标中选择"启动Claude Code cli版"，'
                "用于生成与修改项目代码。\n"
                "3. 手动运行vscode，仅用于查看源代码与确认项目运行结果。",
            )
            self.assertFalse(window.start_btn.isEnabled())
            self.assertNotIn(
                "用户需要自行在vscode中安装claude code插件。",
                window.log_console.toPlainText(),
            )
            with (
                patch.object(window, "start_claude") as start_cli,
                patch.object(window, "upgrade_claude") as upgrade,
            ):
                window.start_selected_claude_target()
            start_cli.assert_not_called()
            upgrade.assert_not_called()

            window.parameter_group.set_launch_target("cli")
            self.assertTrue(window.start_btn.isEnabled())
            window.parameter_group.set_launch_target("upgrade")
            self.assertTrue(window.start_btn.isEnabled())
        finally:
            window._loading = True
            window.close()

    def test_restored_claude_vscode_target_disables_start_without_dialog(self) -> None:
        window = MainWindow()
        try:
            with patch("src.ui.main_window._show_info_dialog") as dialog:
                window._loading = True
                window.parameter_group.set_launch_target("vscode")
                window._loading = False
                window._sync_claude_start_button_state()
            dialog.assert_not_called()
            self.assertFalse(window.start_btn.isEnabled())
        finally:
            window._loading = True
            window.close()

    def test_codex_vscode_target_logs_plugin_reminder(self) -> None:
        window = MainWindow()
        try:
            self.assertNotIn(
                "用户需要自行在vscode中安装codex插件。",
                window.codex_log_console.toPlainText(),
            )
            with patch.object(window.config_manager, "save"):
                window.codex_parameter_group.set_launch_target("cli")
                window.codex_parameter_group.set_launch_target("vscode")
                window._autosave_timer.stop()

            self.assertIn(
                "用户需要自行在vscode中安装codex插件。",
                window.codex_log_console.toPlainText(),
            )
        finally:
            window._loading = True
            window.close()

    def test_official_proxy_confirmation_messages_are_exact(self) -> None:
        window = MainWindow()
        try:
            with patch(
                "src.ui.main_window._show_confirm_dialog",
                return_value=False,
            ) as confirm:
                self.assertFalse(window._check_proxy_for_official())
            confirm.assert_called_once_with(
                window,
                "代理提示",
                "如果不勾选http和https代理，有可能导致claude code运行异常或闪退。\n"
                "点击确认继续，无代理启动claude code。",
            )

            window.codex_parameter_group.provider_combo.setCurrentText(
                "Codex官方接口"
            )
            window.codex_parameter_group.project_path_edit.setText(".")
            window.codex_proxy_group.http.enabled.setChecked(False)
            window.codex_proxy_group.https.enabled.setChecked(False)
            window.codex_proxy_group.socks5.enabled.setChecked(False)
            with (
                patch.object(window.config_manager, "save"),
                patch.object(
                    window.codex_service,
                    "is_vscode_extension_running",
                    return_value=False,
                ),
                patch.object(
                    window.codex_service,
                    "resolve_desktop_executable",
                    return_value=None,
                ),
                patch.object(
                    window.codex_service,
                    "is_any_desktop_running",
                    return_value=False,
                ),
                patch.object(
                    window.codex_service,
                    "is_desktop_running",
                    return_value=False,
                ),
                patch(
                    "src.ui.main_window._show_confirm_dialog",
                    return_value=False,
                ) as confirm,
            ):
                window.start_codex()
                window._autosave_timer.stop()
            confirm.assert_called_once_with(
                window,
                "代理提示",
                "如果不勾选http和https代理，有可能导致codex运行异常或闪退。\n"
                "点击确认继续，无代理启动codex。",
            )
            self.assertIsNone(window.codex_worker)
        finally:
            window._loading = True
            window.close()

    def test_running_codex_vscode_extension_blocks_desktop_and_cli_only(self) -> None:
        window = MainWindow()
        try:
            with (
                patch.object(window.config_manager, "save"),
                patch.object(
                    window.codex_service,
                    "is_vscode_extension_running",
                    return_value=True,
                ) as extension_running,
                patch("src.ui.main_window.QMessageBox.information") as info,
            ):
                window.start_codex()
                window.start_codex_desktop()
                window._autosave_timer.stop()
            self.assertEqual(extension_running.call_count, 2)
            self.assertEqual(info.call_count, 2)
            self.assertTrue(
                all("Codex 插件正在运行" in call.args[2] for call in info.call_args_list)
            )
            self.assertIsNone(window.codex_worker)

            with (
                patch.object(window.config_manager, "save"),
                patch.object(
                    window.codex_service,
                    "is_vscode_extension_running",
                    return_value=True,
                ) as extension_running,
                patch.object(
                    window.codex_service,
                    "resolve_desktop_executable",
                    return_value=None,
                ),
                patch.object(
                    window.codex_service,
                    "is_any_desktop_running",
                    return_value=False,
                ),
                patch.object(
                    window.codex_service,
                    "is_desktop_running",
                    return_value=False,
                ),
                patch.object(
                    window,
                    "_resolve_vscode_for_launch",
                    return_value=None,
                ),
            ):
                window.start_codex_vscode()
                window._autosave_timer.stop()
            extension_running.assert_not_called()
        finally:
            window._loading = True
            window.close()

    def test_codex_only_socks5_proxy_is_blocked_before_launch(self) -> None:
        window = MainWindow()
        try:
            window.codex_parameter_group.provider_combo.setCurrentText(
                "Codex官方接口"
            )
            window.codex_parameter_group.project_path_edit.setText(".")
            window.codex_proxy_group.http.enabled.setChecked(False)
            window.codex_proxy_group.https.enabled.setChecked(False)
            window.codex_proxy_group.socks5.enabled.setChecked(True)
            window.codex_proxy_group.socks5.host.setText("127.0.0.1")
            window.codex_proxy_group.socks5.port.setText("8090")

            with (
                patch.object(window.config_manager, "save"),
                patch.object(
                    window.codex_service,
                    "is_vscode_extension_running",
                    return_value=False,
                ),
                patch.object(
                    window.codex_service,
                    "resolve_desktop_executable",
                    return_value=None,
                ),
                patch.object(
                    window.codex_service,
                    "is_any_desktop_running",
                    return_value=False,
                ),
                patch.object(
                    window.codex_service,
                    "is_desktop_running",
                    return_value=False,
                ),
                patch("src.ui.main_window._show_info_dialog") as dialog,
            ):
                window.start_codex()
                window._autosave_timer.stop()

            dialog.assert_called_once()
            self.assertEqual(dialog.call_args.args[1], "Codex代理不兼容")
            self.assertIn("HTTP或HTTPS代理", dialog.call_args.args[2])
            self.assertIsNone(window.codex_worker)
        finally:
            window._loading = True
            window.close()

    def test_codex_install_success_updates_ui_and_quits(self) -> None:
        window = MainWindow()
        try:
            app = QApplication.instance()
            with (
                patch("src.ui.main_window._show_info_dialog") as dialog,
                patch.object(app, "quit") as quit_app,
            ):
                window._on_codex_install_success()
            self.assertEqual(
                window.codex_status_label.text(),
                "Codex CLI 已成功安装。",
            )
            self.assertIn(
                "Codex CLI 已成功安装。",
                window.codex_log_console.toPlainText(),
            )
            dialog.assert_called_once()
            self.assertIn("重启本软件", dialog.call_args.args[2])
            quit_app.assert_called_once()
        finally:
            window._loading = True
            window.close()

    def test_codex_launch_buttons_are_mutually_locked(self) -> None:
        window = MainWindow()
        try:
            window._lock_codex_ui()
            self.assertFalse(window.codex_start_btn.isEnabled())
            self.assertFalse(
                window.codex_parameter_group.launch_target_combo.isEnabled()
            )
            self.assertTrue(window.codex_stop_btn.isEnabled())
            window._unlock_codex_ui()
            self.assertTrue(window.codex_start_btn.isEnabled())
            self.assertTrue(
                window.codex_parameter_group.launch_target_combo.isEnabled()
            )
            self.assertFalse(window.codex_stop_btn.isEnabled())
        finally:
            window._loading = True
            window.close()

    def test_claude_launch_buttons_are_mutually_locked(self) -> None:
        window = MainWindow()
        try:
            window.parameter_group.set_launch_target("cli")
            window._lock_claude_ui()
            self.assertFalse(window.start_btn.isEnabled())
            self.assertFalse(window.parameter_group.launch_target_combo.isEnabled())
            self.assertTrue(window.stop_btn.isEnabled())
            window._unlock_ui()
            self.assertTrue(window.start_btn.isEnabled())
            self.assertTrue(window.parameter_group.launch_target_combo.isEnabled())
            self.assertFalse(window.stop_btn.isEnabled())
        finally:
            window._loading = True
            window.close()

    def test_unified_start_buttons_dispatch_selected_targets(self) -> None:
        window = MainWindow()
        try:
            claude_targets = {
                "cli": "start_claude",
                "upgrade": "upgrade_claude",
            }
            for target, method_name in claude_targets.items():
                window.parameter_group.set_launch_target(target)
                with patch.object(window, method_name) as method:
                    window.start_selected_claude_target()
                method.assert_called_once()

            codex_targets = {
                "desktop": "start_codex_desktop",
                "cli": "start_codex",
                "vscode": "start_codex_vscode",
                "upgrade": "upgrade_codex",
            }
            for target, method_name in codex_targets.items():
                window.codex_parameter_group.set_launch_target(target)
                with patch.object(window, method_name) as method:
                    window.start_selected_codex_target()
                method.assert_called_once()
        finally:
            window._loading = True
            window.close()

    def test_missing_desktop_opens_store_search_after_confirmation(self) -> None:
        window = MainWindow()
        try:
            with (
                patch.object(
                    window.codex_service,
                    "resolve_desktop_executable",
                    return_value=None,
                ),
                patch.object(
                    window.codex_service,
                    "is_vscode_extension_running",
                    return_value=False,
                ),
                patch.object(
                    window.codex_service,
                    "is_desktop_running",
                    return_value=False,
                ),
                patch.object(
                    window.codex_service,
                    "is_any_desktop_running",
                    return_value=False,
                ),
                patch("src.ui.main_window._show_confirm_dialog", return_value=True),
                patch("src.ui.main_window.QDesktopServices.openUrl") as open_store,
            ):
                window.start_codex_desktop()
            open_store.assert_called_once()
            self.assertEqual(
                open_store.call_args.args[0].toString(),
                "ms-windows-store://search/?query=Codex",
            )
            self.assertIsNone(window.codex_worker)
        finally:
            window._loading = True
            window.close()

    def test_external_desktop_blocks_cli_and_desktop_launch(self) -> None:
        window = MainWindow()
        try:
            executable = Path(r"C:\Apps\Codex.exe")
            with (
                patch.object(
                    window.codex_service,
                    "resolve_desktop_executable",
                    return_value=executable,
                ),
                patch.object(
                    window.codex_service,
                    "is_vscode_extension_running",
                    return_value=False,
                ),
                patch.object(
                    window.codex_service,
                    "is_desktop_running",
                    return_value=True,
                ),
                patch.object(
                    window.codex_service,
                    "is_any_desktop_running",
                    return_value=False,
                ),
                patch("src.ui.main_window.QMessageBox.information") as info,
            ):
                window.start_codex()
                window.start_codex_desktop()
            self.assertEqual(info.call_count, 2)
            self.assertTrue(
                all(
                    "已在运行" in call.args[2]
                    for call in info.call_args_list
                )
            )
            self.assertIsNone(window.codex_worker)
        finally:
            window._loading = True
            window.close()


if __name__ == "__main__":
    unittest.main()
