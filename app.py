import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QListWidget, QListWidgetItem, QProgressBar,
                             QFileDialog, QTextEdit, QSplitter, QGroupBox, QCheckBox,
                             QDialog, QDialogButtonBox, QFormLayout, QMenuBar, QMenu)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon, QAction
import yt_dlp
from urllib.request import urlopen
from settings import Settings
from settings_dialog import SettingsDialog


class VideoInfoWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url, browser):
        super().__init__()
        self.url = url
        self.browser = browser

    def run(self):
        try:
            base = {"quiet": True}
            if self.browser:
                base["cookiesfrombrowser"] = (self.browser,)

            with yt_dlp.YoutubeDL({**base, "extract_flat": True}) as ydl:
                flat = ydl.extract_info(self.url, download=False)

            entries = []
            first_url = self.url
            if flat.get("_type") == "playlist":
                for i, e in enumerate(flat.get("entries") or []):
                    entries.append({"index": i, "title": e.get("title", f"第{i+1}集")})
                if flat.get("entries"):
                    first_url = flat["entries"][0].get("url") or flat["entries"][0].get("webpage_url") or self.url

            with yt_dlp.YoutubeDL(base) as ydl:
                info = ydl.extract_info(first_url, download=False)

            heights = sorted(
                {f["height"] for f in info.get("formats", []) if f.get("height") and f.get("vcodec", "none") != "none"},
                reverse=True,
            )

            self.finished.emit({
                "title": flat.get("title") or info.get("title", ""),
                "thumbnail": info.get("thumbnail", ""),
                "formats": [{"height": h, "label": f"{h}p"} for h in heights],
                "entries": entries,
            })
        except Exception as e:
            self.error.emit(str(e))


class DownloadWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, height, output_dir, browser, entries=None, speed_limit=""):
        super().__init__()
        self.url = url
        self.height = height
        self.output_dir = output_dir
        self.browser = browser
        self.entries = entries
        self.speed_limit = speed_limit

    def run(self):
        def progress_hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes", 0)
                pct = int(done / total * 100) if total else 0
                speed = d.get("_speed_str", "")
                self.progress.emit(pct, speed)
            elif d["status"] == "finished":
                self.progress.emit(99, "合并中...")

        os.makedirs(self.output_dir, exist_ok=True)
        opts = {
            "format": f"bestvideo[height<={self.height}]+bestaudio/best[height<={self.height}]",
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "progress_hooks": [progress_hook],
            "quiet": True,
        }
        if self.browser:
            opts["cookiesfrombrowser"] = (self.browser,)
        if self.speed_limit:
            opts["ratelimit"] = self.parse_speed_limit(self.speed_limit)
        if self.entries is not None:
            opts["playlist_items"] = ",".join(str(i + 1) for i in self.entries)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
            self.finished.emit(self.output_dir)
        except Exception as e:
            self.error.emit(str(e))

    def parse_speed_limit(self, limit_str):
        """解析速度限制字符串，如 '5M' -> 5242880 bytes/s"""
        limit_str = limit_str.strip().upper()
        if not limit_str:
            return None

        multipliers = {'K': 1024, 'M': 1024*1024, 'G': 1024*1024*1024}

        if limit_str[-1] in multipliers:
            try:
                return int(float(limit_str[:-1]) * multipliers[limit_str[-1]])
            except:
                return None
        try:
            return int(limit_str)
        except:
            return None


class BilibiliDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video_data = None
        self.settings = Settings()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle("Bilibili 下载器")
        self.setGeometry(100, 100, 900, 700)

        # 菜单栏
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("设置")

        settings_action = QAction("偏好设置", self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # URL 输入区
        url_group = QGroupBox("视频链接")
        url_layout = QVBoxLayout()

        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入 Bilibili 视频或合集链接...")
        url_row.addWidget(self.url_input)

        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["不使用Cookie", "chrome", "firefox", "chromium", "edge"])
        url_row.addWidget(self.browser_combo)

        self.fetch_btn = QPushButton("获取信息")
        self.fetch_btn.clicked.connect(self.fetch_info)
        url_row.addWidget(self.fetch_btn)

        url_layout.addLayout(url_row)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)

        # 视频信息区
        info_group = QGroupBox("视频信息")
        info_layout = QHBoxLayout()

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(160, 120)
        self.thumbnail_label.setScaledContents(True)
        info_layout.addWidget(self.thumbnail_label)

        info_right = QVBoxLayout()
        self.title_label = QLabel("等待获取...")
        self.title_label.setWordWrap(True)
        info_right.addWidget(self.title_label)

        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("分辨率:"))
        self.resolution_combo = QComboBox()
        res_row.addWidget(self.resolution_combo)
        res_row.addStretch()
        info_right.addLayout(res_row)

        info_layout.addLayout(info_right)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # 剧集列表
        self.episodes_group = QGroupBox("剧集列表")
        episodes_layout = QVBoxLayout()

        ep_btns = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(lambda: self.select_all_episodes(True))
        ep_btns.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("取消全选")
        deselect_all_btn.clicked.connect(lambda: self.select_all_episodes(False))
        ep_btns.addWidget(deselect_all_btn)
        ep_btns.addStretch()
        episodes_layout.addLayout(ep_btns)

        self.episodes_list = QListWidget()
        episodes_layout.addWidget(self.episodes_list)

        self.episodes_group.setLayout(episodes_layout)
        self.episodes_group.hide()
        layout.addWidget(self.episodes_group)

        # 下载设置
        dl_group = QGroupBox("下载设置")
        dl_layout = QVBoxLayout()

        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("保存路径:"))
        self.output_path = QLineEdit(str(Path.home() / "Downloads" / "bilibili"))
        path_row.addWidget(self.output_path)

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_folder)
        path_row.addWidget(browse_btn)
        dl_layout.addLayout(path_row)

        self.download_btn = QPushButton("开始下载")
        self.download_btn.clicked.connect(self.start_download)
        dl_layout.addWidget(self.download_btn)

        dl_group.setLayout(dl_layout)
        layout.addWidget(dl_group)

        # 下载进度
        progress_group = QGroupBox("下载进度")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("等待下载...")
        progress_layout.addWidget(self.status_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

    def fetch_info(self):
        url = self.url_input.text().strip()
        if not url:
            return

        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("获取中...")

        browser = self.browser_combo.currentText()
        if browser == "不使用Cookie":
            browser = None

        self.worker = VideoInfoWorker(url, browser)
        self.worker.finished.connect(self.on_info_received)
        self.worker.error.connect(self.on_info_error)
        self.worker.start()

    def on_info_received(self, data):
        self.video_data = data
        self.title_label.setText(data["title"])

        if data["thumbnail"]:
            try:
                img_data = urlopen(data["thumbnail"]).read()
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                self.thumbnail_label.setPixmap(pixmap)
            except:
                pass

        self.resolution_combo.clear()
        default_res = self.settings.get("default_resolution")
        default_idx = 0
        for idx, fmt in enumerate(data["formats"]):
            self.resolution_combo.addItem(fmt["label"], fmt["height"])
            if str(fmt["height"]) == default_res:
                default_idx = idx
        self.resolution_combo.setCurrentIndex(default_idx)

        if data["entries"]:
            self.episodes_list.clear()
            for ep in data["entries"]:
                item = QListWidgetItem(ep["title"])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                item.setData(Qt.ItemDataRole.UserRole, ep["index"])
                self.episodes_list.addItem(item)
            self.episodes_group.show()
        else:
            self.episodes_group.hide()

        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("获取信息")

        # 自动开始下载
        if self.settings.get("auto_start_download"):
            self.start_download()

    def on_info_error(self, error):
        self.status_label.setText(f"错误: {error}")
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("获取信息")

    def select_all_episodes(self, checked):
        for i in range(self.episodes_list.count()):
            item = self.episodes_list.item(i)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择保存文件夹")
        if folder:
            self.output_path.setText(folder)

    def start_download(self):
        if not self.video_data:
            return

        url = self.url_input.text().strip()
        height = self.resolution_combo.currentData()
        output_dir = self.output_path.text()

        browser = self.browser_combo.currentText()
        if browser == "不使用Cookie":
            browser = None

        entries = None
        if self.episodes_group.isVisible():
            entries = []
            for i in range(self.episodes_list.count()):
                item = self.episodes_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    entries.append(item.data(Qt.ItemDataRole.UserRole))
            if not entries:
                self.status_label.setText("请至少选择一集")
                return

        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("准备下载...")

        speed_limit = self.settings.get("speed_limit", "")
        self.dl_worker = DownloadWorker(url, height, output_dir, browser, entries, speed_limit)
        self.dl_worker.progress.connect(self.on_download_progress)
        self.dl_worker.finished.connect(self.on_download_finished)
        self.dl_worker.error.connect(self.on_download_error)
        self.dl_worker.start()

    def on_download_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"{pct}% {msg}")

    def on_download_finished(self, output_dir):
        self.progress_bar.setValue(100)
        self.status_label.setText(f"下载完成 · 已保存至: {output_dir}")
        self.download_btn.setEnabled(True)

    def on_download_error(self, error):
        self.status_label.setText(f"错误: {error}")
        self.download_btn.setEnabled(True)

    def load_settings(self):
        """加载用户设置到界面"""
        self.output_path.setText(self.settings.get("download_path"))
        self.browser_combo.setCurrentText(self.settings.get("browser"))

    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_settings()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BilibiliDownloader()
    window.show()
    sys.exit(app.exec())
