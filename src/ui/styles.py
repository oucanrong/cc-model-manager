# 路径: src/ui/styles.py
# 作用: 全局样式定义

APP_QSS = r'''
QWidget {
    background-color: #ffffff;
    color: #222222;
    font-family: "Microsoft YaHei";
    font-size: 12pt;
}
QMainWindow {
    background-color: #ffffff;
    color: #222222;
}
QGroupBox {
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    margin-top: 12px;
    padding: 10px;
    color: #222222;
    font-weight: 600;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QLineEdit, QComboBox, QPlainTextEdit {
    background-color: #ffffff;
    color: #222222;
    border: 1px solid #cfcfcf;
    border-radius: 6px;
    padding: 3px 6px;
    min-height: 26px;
    selection-background-color: #007acc;
    selection-color: #ffffff;
}
QLineEdit:disabled, QComboBox:disabled {
    color: #888888;
    background-color: #f3f3f3;
}
QPushButton {
    border: none;
    border-radius: 8px;
    padding: 5px 14px;
    min-height: 26px;
    color: white;
}
QPushButton:hover {
    opacity: 0.92;
}
QPushButton:pressed {
    padding-top: 7px;
    padding-bottom: 3px;
}
QPushButton:disabled {
    background-color: #5a5a5a;
    color: #aaaaaa;
}
QLabel {
    color: #222222;
    background-color: transparent;
}
QStatusBar {
    background-color: #ffffff;
    color: #222222;
    border-top: 1px solid #d9d9d9;
}
QPushButton#startButton {
    background-color: #2ea043;
}
QPushButton#stopButton {
    background-color: #d73a49;
}
QPushButton#clearButton {
    background-color: #d29922;
}
QPushButton#copyButton {
    background-color: #6f42c1;
}
QPushButton#pickProjectButton {
    background-color: #2ea043;
}
QPushButton#resetButton {
    background-color: #0e639c;
}
QPushButton#exitButton {
    background-color: #6e7681;
}
QPushButton#authSettingsButton {
    background-color: #2ea043;
}
'''