from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QPushButton, QComboBox, QCheckBox,
                             QDialogButtonBox, QFileDialog)


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 默认下载路径
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self.settings.get("download_path"))
        path_layout.addWidget(self.path_input)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        form.addRow("默认下载路径:", path_layout)

        # 默认浏览器
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["不使用Cookie", "chrome", "firefox", "chromium", "edge"])
        self.browser_combo.setCurrentText(self.settings.get("browser"))
        form.addRow("默认浏览器Cookie:", self.browser_combo)

        # 网速限制
        self.speed_input = QLineEdit(self.settings.get("speed_limit"))
        self.speed_input.setPlaceholderText("留空不限速，如: 5M, 1024K")
        form.addRow("下载速度限制:", self.speed_input)

        # 默认分辨率
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["360", "480", "720", "1080", "1440", "2160"])
        self.resolution_combo.setCurrentText(self.settings.get("default_resolution"))
        form.addRow("默认分辨率:", self.resolution_combo)

        # 自动开始下载
        self.auto_start_check = QCheckBox("获取信息后自动开始下载")
        self.auto_start_check.setChecked(self.settings.get("auto_start_download"))
        form.addRow("", self.auto_start_check)

        layout.addLayout(form)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择默认下载文件夹")
        if folder:
            self.path_input.setText(folder)

    def save_settings(self):
        self.settings.set("download_path", self.path_input.text())
        self.settings.set("browser", self.browser_combo.currentText())
        self.settings.set("speed_limit", self.speed_input.text())
        self.settings.set("default_resolution", self.resolution_combo.currentText())
        self.settings.set("auto_start_download", self.auto_start_check.isChecked())
        self.accept()
