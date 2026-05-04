import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QListWidget, QListWidgetItem, QProgressBar,
                             QFileDialog, QSplitter, QCheckBox,
                             QDialog, QDialogButtonBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QIcon, QAction, QColor, QPainter, QBrush
import yt_dlp
from urllib.request import urlopen
from settings import Settings
from settings_dialog import SettingsDialog


BILI_PINK = "#FB7299"

DARK_QSS = f"""
QWidget {{ background: #18181b; color: #fafafa; font-family: 'Segoe UI', sans-serif; font-size: 13px; }}
QFrame#card {{ background: #27272a; border-radius: 8px; }}
QLineEdit, QComboBox {{
    background: #3f3f46; border: 1px solid #52525b; border-radius: 6px;
    padding: 6px 10px; color: #fafafa;
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {BILI_PINK}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QPushButton {{
    background: {BILI_PINK}; color: white; border: none; border-radius: 6px;
    padding: 7px 16px; font-weight: 600;
}}
QPushButton:hover {{ background: #fc8fad; }}
QPushButton:disabled {{ background: #52525b; color: #a1a1aa; }}
QPushButton#ghost {{
    background: transparent; color: #a1a1aa; border: 1px solid #3f3f46;
}}
QPushButton#ghost:hover {{ border-color: {BILI_PINK}; color: {BILI_PINK}; }}
QPushButton#close {{ background: transparent; color: #a1a1aa; border: none; font-size: 16px; padding: 4px 10px; }}
QPushButton#close:hover {{ background: #ef4444; color: white; border-radius: 4px; }}
QPushButton#theme {{ background: transparent; color: #a1a1aa; border: none; font-size: 14px; padding: 4px 8px; }}
QPushButton#theme:hover {{ color: {BILI_PINK}; }}
QProgressBar {{
    background: #3f3f46; border-radius: 4px; height: 6px; text-align: center;
}}
QProgressBar::chunk {{ background: {BILI_PINK}; border-radius: 4px; }}
QListWidget {{
    background: #27272a; border: 1px solid #3f3f46; border-radius: 6px;
}}
QListWidget::item {{ padding: 6px 10px; border-radius: 4px; }}
QListWidget::item:selected {{ background: #3f3f46; color: {BILI_PINK}; }}
QScrollBar:vertical {{ background: #27272a; width: 6px; border-radius: 3px; }}
QScrollBar::handle:vertical {{ background: #52525b; border-radius: 3px; }}
QLabel#title_bar_label {{ color: {BILI_PINK}; font-weight: 700; font-size: 14px; letter-spacing: 1px; }}
QLabel#section {{ color: #a1a1aa; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; }}
"""

LIGHT_QSS = f"""
QWidget {{ background: #f4f4f5; color: #18181b; font-family: 'Segoe UI', sans-serif; font-size: 13px; }}
QFrame#card {{ background: #ffffff; border-radius: 8px; }}
QLineEdit, QComboBox {{
    background: #ffffff; border: 1px solid #d4d4d8; border-radius: 6px;
    padding: 6px 10px; color: #18181b;
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {BILI_PINK}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QPushButton {{
    background: {BILI_PINK}; color: white; border: none; border-radius: 6px;
    padding: 7px 16px; font-weight: 600;
}}
QPushButton:hover {{ background: #fc8fad; }}
QPushButton:disabled {{ background: #d4d4d8; color: #a1a1aa; }}
QPushButton#ghost {{
    background: transparent; color: #71717a; border: 1px solid #d4d4d8;
}}
QPushButton#ghost:hover {{ border-color: {BILI_PINK}; color: {BILI_PINK}; }}
QPushButton#close {{ background: transparent; color: #71717a; border: none; font-size: 16px; padding: 4px 10px; }}
QPushButton#close:hover {{ background: #ef4444; color: white; border-radius: 4px; }}
QPushButton#theme {{ background: transparent; color: #71717a; border: none; font-size: 14px; padding: 4px 8px; }}
QPushButton#theme:hover {{ color: {BILI_PINK}; }}
QProgressBar {{
    background: #e4e4e7; border-radius: 4px; height: 6px; text-align: center;
}}
QProgressBar::chunk {{ background: {BILI_PINK}; border-radius: 4px; }}
QListWidget {{
    background: #ffffff; border: 1px solid #e4e4e7; border-radius: 6px;
}}
QListWidget::item {{ padding: 6px 10px; border-radius: 4px; }}
QListWidget::item:selected {{ background: #fce7ef; color: {BILI_PINK}; }}
QScrollBar:vertical {{ background: #f4f4f5; width: 6px; border-radius: 3px; }}
QScrollBar::handle:vertical {{ background: #d4d4d8; border-radius: 3px; }}
QLabel#title_bar_label {{ color: {BILI_PINK}; font-weight: 700; font-size: 14px; letter-spacing: 1px; }}
QLabel#section {{ color: #71717a; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; }}
"""


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
                self.progress.emit(pct, d.get("_speed_str", ""))
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
            opts["ratelimit"] = self._parse_speed(self.speed_limit)
        if self.entries is not None:
            opts["playlist_items"] = ",".join(str(i + 1) for i in self.entries)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
            self.finished.emit(self.output_dir)
        except Exception as e:
            self.error.emit(str(e))

    def _parse_speed(self, s):
        s = s.strip().upper()
        m = {"K": 1024, "M": 1024**2, "G": 1024**3}
        if s and s[-1] in m:
            try:
                return int(float(s[:-1]) * m[s[-1]])
            except Exception:
                return None
        try:
            return int(s)
        except Exception:
            return None


def _card(layout=None):
    f = QFrame()
    f.setObjectName("card")
    if layout:
        f.setLayout(layout)
    return f


class TitleBar(QWidget):
    def __init__(self, parent, on_theme_toggle, on_close):
        super().__init__(parent)
        self.setFixedHeight(44)
        self._drag_pos = None

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 0, 8, 0)

        lbl = QLabel("BILI-DOWNLOADER")
        lbl.setObjectName("title_bar_label")
        row.addWidget(lbl)
        row.addStretch()

        self.theme_btn = QPushButton("☀")
        self.theme_btn.setObjectName("theme")
        self.theme_btn.setFixedSize(32, 32)
        self.theme_btn.clicked.connect(on_theme_toggle)
        row.addWidget(self.theme_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("close")
        close_btn.setFixedSize(36, 32)
        close_btn.clicked.connect(on_close)
        row.addWidget(close_btn)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.window().move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None


class CompletionToast(QWidget):
    def __init__(self, parent, message):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)

        lbl = QLabel(f"✓  {message}")
        lbl.setStyleSheet(f"color: white; font-weight: 600; background: {BILI_PINK}; border-radius: 8px; padding: 8px 14px;")
        layout.addWidget(lbl)

        self.adjustSize()
        pr = parent.rect()
        self.move(pr.right() - self.width() - 20, pr.bottom() - self.height() - 20)
        self.show()

        QTimer.singleShot(3000, self.close)


class DownloadCenter(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("下载中心")
        self.setMinimumSize(480, 360)
        self._items = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hdr = QLabel("下载中心")
        hdr.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(hdr)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(2)
        layout.addWidget(self.list_widget)

    def add_download(self, key, title):
        item = QListWidgetItem(f"⏳  {title}  —  0%")
        self.list_widget.addItem(item)
        self._items[key] = item

    def update_progress(self, key, pct, speed):
        if key in self._items:
            title = self._items[key].text().split("  —  ")[0].lstrip("⏳✓✗ ")
            self._items[key].setText(f"⏳  {title}  —  {pct}%  {speed}")

    def mark_done(self, key):
        if key in self._items:
            text = self._items[key].text()
            title = text.split("  —  ")[0].lstrip("⏳✓✗ ")
            self._items[key].setText(f"✓  {title}  —  完成")
            self._items[key].setForeground(QColor(BILI_PINK))

    def mark_error(self, key, msg):
        if key in self._items:
            title = self._items[key].text().split("  —  ")[0].lstrip("⏳✓✗ ")
            self._items[key].setText(f"✗  {title}  —  {msg}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.theme = self.settings.get("theme", "dark")
        self._info = None
        self._worker = None
        self._dl_worker = None
        self._dl_key = 0

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(860, 680)

        self.download_center = DownloadCenter(self)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.title_bar = TitleBar(self, self._toggle_theme, self.close)
        root_layout.addWidget(self.title_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root_layout.addWidget(scroll)

        body = QWidget()
        scroll.setWidget(body)
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(20, 16, 20, 16)
        self.body_layout.setSpacing(12)

        self._build_url_card()
        self._build_info_card()
        self._build_episodes_card()
        self._build_download_card()
        self._build_progress_card()
        self.body_layout.addStretch()
        self._build_bottom_bar(root_layout)

        self._apply_theme()
        self._load_settings_to_ui()

    def _build_url_card(self):
        inner = QVBoxLayout()
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(10)

        sec = QLabel("视频链接")
        sec.setObjectName("section")
        inner.addWidget(sec)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴 Bilibili 视频或合集链接...")
        row.addWidget(self.url_input)

        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["不使用Cookie", "chrome", "firefox", "chromium", "edge"])
        self.browser_combo.setFixedWidth(130)
        row.addWidget(self.browser_combo)

        self.fetch_btn = QPushButton("获取信息")
        self.fetch_btn.setFixedWidth(90)
        self.fetch_btn.clicked.connect(self._fetch_info)
        row.addWidget(self.fetch_btn)

        inner.addLayout(row)
        self.body_layout.addWidget(_card(inner))

    def _build_info_card(self):
        inner = QVBoxLayout()
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(10)

        sec = QLabel("视频信息")
        sec.setObjectName("section")
        inner.addWidget(sec)

        row = QHBoxLayout()
        row.setSpacing(14)

        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(160, 100)
        self.thumb_label.setStyleSheet("background: #3f3f46; border-radius: 6px;")
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.thumb_label)

        meta = QVBoxLayout()
        meta.setSpacing(8)
        self.title_label = QLabel("—")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        meta.addWidget(self.title_label)

        res_row = QHBoxLayout()
        res_lbl = QLabel("分辨率:")
        res_lbl.setObjectName("section")
        res_row.addWidget(res_lbl)
        self.res_combo = QComboBox()
        self.res_combo.setFixedWidth(110)
        res_row.addWidget(self.res_combo)
        res_row.addStretch()
        meta.addLayout(res_row)
        meta.addStretch()
        row.addLayout(meta)

        inner.addLayout(row)
        self.body_layout.addWidget(_card(inner))

    def _build_episodes_card(self):
        inner = QVBoxLayout()
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(10)

        sec = QLabel("剧集列表")
        sec.setObjectName("section")
        inner.addWidget(sec)

        self.episode_list = QListWidget()
        self.episode_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.episode_list.setMaximumHeight(160)
        inner.addWidget(self.episode_list)

        btn_row = QHBoxLayout()
        sel_all = QPushButton("全选")
        sel_all.setObjectName("ghost")
        sel_all.clicked.connect(self.episode_list.selectAll)
        desel_all = QPushButton("取消全选")
        desel_all.setObjectName("ghost")
        desel_all.clicked.connect(self.episode_list.clearSelection)
        btn_row.addWidget(sel_all)
        btn_row.addWidget(desel_all)
        btn_row.addStretch()
        inner.addLayout(btn_row)

        self.episodes_card = _card(inner)
        self.episodes_card.setVisible(False)
        self.body_layout.addWidget(self.episodes_card)

    def _build_download_card(self):
        inner = QVBoxLayout()
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(10)

        sec = QLabel("保存位置")
        sec.setObjectName("section")
        inner.addWidget(sec)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.path_input = QLineEdit()
        row.addWidget(self.path_input)
        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("ghost")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse_path)
        row.addWidget(browse_btn)
        self.dl_btn = QPushButton("开始下载")
        self.dl_btn.setFixedWidth(100)
        self.dl_btn.setEnabled(False)
        self.dl_btn.clicked.connect(self._start_download)
        row.addWidget(self.dl_btn)
        inner.addLayout(row)

        self.body_layout.addWidget(_card(inner))

    def _build_progress_card(self):
        inner = QVBoxLayout()
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(8)

        sec = QLabel("下载进度")
        sec.setObjectName("section")
        inner.addWidget(sec)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        inner.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        inner.addWidget(self.status_label)

        self.body_layout.addWidget(_card(inner))

    def _build_bottom_bar(self, root_layout):
        bar = QWidget()
        bar.setFixedHeight(44)
        row = QHBoxLayout(bar)
        row.setContentsMargins(20, 0, 20, 0)

        settings_btn = QPushButton("偏好设置")
        settings_btn.setObjectName("ghost")
        settings_btn.clicked.connect(self._open_settings)
        row.addWidget(settings_btn)
        row.addStretch()

        dc_btn = QPushButton("下载中心")
        dc_btn.setObjectName("ghost")
        dc_btn.clicked.connect(self.download_center.show)
        row.addWidget(dc_btn)

        root_layout.addWidget(bar)

    def _apply_theme(self):
        qss = DARK_QSS if self.theme == "dark" else LIGHT_QSS
        self.setStyleSheet(qss)
        self.download_center.setStyleSheet(qss)
        self.title_bar.theme_btn.setText("☀" if self.theme == "dark" else "🌙")

    def _toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.settings.set("theme", self.theme)
        self._apply_theme()

    def _load_settings_to_ui(self):
        self.path_input.setText(self.settings.get("download_path", ""))
        browser = self.settings.get("browser", "不使用Cookie")
        idx = self.browser_combo.findText(browser)
        if idx >= 0:
            self.browser_combo.setCurrentIndex(idx)

    def _open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            self._load_settings_to_ui()
            self.theme = self.settings.get("theme", self.theme)
            self._apply_theme()

    def _browse_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择下载文件夹")
        if folder:
            self.path_input.setText(folder)

    def _fetch_info(self):
        url = self.url_input.text().strip()
        if not url:
            return
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("获取中...")
        self.dl_btn.setEnabled(False)
        self.status_label.setText("正在获取视频信息...")

        browser = self.browser_combo.currentText()
        if browser == "不使用Cookie":
            browser = None

        self._worker = VideoInfoWorker(url, browser)
        self._worker.finished.connect(self._on_info)
        self._worker.error.connect(self._on_info_error)
        self._worker.start()

    def _on_info(self, data):
        self._info = data
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("获取信息")
        self.title_label.setText(data.get("title", ""))
        self.status_label.setText("就绪")

        self.res_combo.clear()
        for fmt in data.get("formats", []):
            self.res_combo.addItem(fmt["label"], fmt["height"])
        default_res = self.settings.get("default_resolution", "1080")
        for i in range(self.res_combo.count()):
            if str(self.res_combo.itemData(i)) == default_res:
                self.res_combo.setCurrentIndex(i)
                break

        entries = data.get("entries", [])
        self.episode_list.clear()
        if entries:
            for e in entries:
                item = QListWidgetItem(e["title"])
                item.setData(Qt.ItemDataRole.UserRole, e["index"])
                self.episode_list.addItem(item)
            self.episode_list.selectAll()
            self.episodes_card.setVisible(True)
        else:
            self.episodes_card.setVisible(False)

        thumb_url = data.get("thumbnail", "")
        if thumb_url:
            try:
                raw = urlopen(thumb_url, timeout=5).read()
                pix = QPixmap()
                pix.loadFromData(raw)
                self.thumb_label.setPixmap(pix.scaled(160, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation))
            except Exception:
                pass

        self.dl_btn.setEnabled(True)
        if self.settings.get("auto_start_download"):
            self._start_download()

    def _on_info_error(self, msg):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("获取信息")
        self.status_label.setText(f"错误: {msg}")

    def _start_download(self):
        if not self._info:
            return
        url = self.url_input.text().strip()
        height = self.res_combo.currentData() or 1080
        output_dir = self.path_input.text().strip() or self.settings.get("download_path")
        browser = self.browser_combo.currentText()
        if browser == "不使用Cookie":
            browser = None
        speed_limit = self.settings.get("speed_limit", "")

        entries = None
        if self._info.get("entries") and self.episodes_card.isVisible():
            selected = self.episode_list.selectedItems()
            entries = [item.data(Qt.ItemDataRole.UserRole) for item in selected]

        self._dl_key += 1
        key = self._dl_key
        title = self._info.get("title", "未知")
        self.download_center.add_download(key, title)

        self.dl_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("下载中...")

        self._dl_worker = DownloadWorker(url, height, output_dir, browser, entries, speed_limit)
        self._dl_worker.progress.connect(lambda pct, spd: self._on_progress(key, pct, spd))
        self._dl_worker.finished.connect(lambda _: self._on_done(key, title))
        self._dl_worker.error.connect(lambda msg: self._on_error(key, msg))
        self._dl_worker.start()

    def _on_progress(self, key, pct, speed):
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"下载中... {pct}%  {speed}")
        self.download_center.update_progress(key, pct, speed)

    def _on_done(self, key, title):
        self.progress_bar.setValue(100)
        self.status_label.setText("下载完成")
        self.dl_btn.setEnabled(True)
        self.download_center.mark_done(key)
        CompletionToast(self.centralWidget(), f"下载完成 · {title}")

    def _on_error(self, key, msg):
        self.status_label.setText(f"错误: {msg}")
        self.dl_btn.setEnabled(True)
        self.download_center.mark_error(key, msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("BILI-DOWNLOADER")
    win = MainWindow()
    win.resize(900, 700)
    win.show()
    sys.exit(app.exec())
