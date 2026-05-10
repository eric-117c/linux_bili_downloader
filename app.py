import sys
import os
import json
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QListWidget, QListWidgetItem, QProgressBar,
                             QFileDialog, QFrame, QScrollArea, QStackedWidget,
                             QListView, QStyledItemDelegate, QAbstractItemView)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QTimer, QPoint, QObject,
                          QSize, QRectF, QModelIndex, QPointF)
from PyQt6.QtGui import (QPixmap, QColor, QPainter, QPen, QBrush, QFont,
                         QStandardItemModel, QStandardItem, QCursor)
import yt_dlp
from urllib.request import urlopen
from settings import Settings
from settings_dialog import SettingsDialog


BILI_PINK = "#FB7299"

_NAV_STYLES = f"""
QWidget#nav_bar {{ border-right: 1px solid; }}
QPushButton#nav, QPushButton#nav_active {{
    background: transparent; border: none; border-radius: 0;
    padding: 12px 0; font-size: 11px; font-weight: 600;
    text-align: center; width: 72px;
}}
QPushButton#nav_active {{ color: {BILI_PINK}; border-left: 3px solid {BILI_PINK}; }}
"""

DARK_QSS = f"""
QWidget {{ background: transparent; color: #fafafa; font-family: 'Segoe UI', sans-serif; font-size: 13px; }}
QDialog {{ background: #18181b; }}
QWidget#nav_bar {{ border-right-color: #3f3f46; background: rgba(24, 24, 27, 220); }}
QPushButton#nav {{ color: #71717a; }}
QPushButton#nav:hover {{ color: #a1a1aa; background: rgba(39, 39, 42, 180); }}
QFrame#card {{ background: rgba(39, 39, 42, 240); border-radius: 8px; }}
QLineEdit, QComboBox {{
    background: #3f3f46; border: 1px solid #52525b; border-radius: 6px;
    padding: 6px 10px; color: #fafafa;
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {BILI_PINK}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: #27272a; color: #fafafa; border: 1px solid #52525b;
    selection-background-color: #3f3f46; selection-color: {BILI_PINK};
}}
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
""" + _NAV_STYLES

LIGHT_QSS = f"""
QWidget {{ background: transparent; color: #18181b; font-family: 'Segoe UI', sans-serif; font-size: 13px; }}
QDialog {{ background: #f4f4f5; }}
QWidget#nav_bar {{ border-right-color: #e4e4e7; background: rgba(244, 244, 245, 220); }}
QPushButton#nav {{ color: #52525b; }}
QPushButton#nav:hover {{ color: #18181b; background: rgba(228, 228, 231, 180); }}
QFrame#card {{ background: rgba(255, 255, 255, 240); border-radius: 8px; }}
QLineEdit, QComboBox {{
    background: #ffffff; border: 1px solid #d4d4d8; border-radius: 6px;
    padding: 6px 10px; color: #18181b;
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {BILI_PINK}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: #ffffff; color: #18181b; border: 1px solid #d4d4d8;
    selection-background-color: #fce7ef; selection-color: {BILI_PINK};
}}
QPushButton {{
    background: {BILI_PINK}; color: white; border: none; border-radius: 6px;
    padding: 7px 16px; font-weight: 600;
}}
QPushButton:hover {{ background: #e85c85; }}
QPushButton:disabled {{ background: #d4d4d8; color: #71717a; }}
QPushButton#ghost {{
    background: transparent; color: #52525b; border: 1px solid #d4d4d8;
}}
QPushButton#ghost:hover {{ border-color: {BILI_PINK}; color: {BILI_PINK}; background: #fce7ef; }}
QPushButton#close {{ background: transparent; color: #52525b; border: none; font-size: 16px; padding: 4px 10px; }}
QPushButton#close:hover {{ background: #ef4444; color: white; border-radius: 4px; }}
QPushButton#theme {{ background: transparent; color: #52525b; border: none; font-size: 14px; padding: 4px 8px; }}
QPushButton#theme:hover {{ color: {BILI_PINK}; }}
QProgressBar {{
    background: #e4e4e7; border-radius: 4px; height: 6px; text-align: center;
}}
QProgressBar::chunk {{ background: {BILI_PINK}; border-radius: 4px; }}
QListWidget {{
    background: #ffffff; border: 1px solid #e4e4e7; border-radius: 6px; color: #18181b;
}}
QListWidget::item {{ padding: 6px 10px; border-radius: 4px; color: #18181b; }}
QListWidget::item:selected {{ background: #fce7ef; color: {BILI_PINK}; }}
QListWidget::item:hover {{ background: #f4f4f5; }}
QScrollBar:vertical {{ background: #f4f4f5; width: 6px; border-radius: 3px; }}
QScrollBar::handle:vertical {{ background: #d4d4d8; border-radius: 3px; }}
QLabel {{ color: #18181b; }}
QLabel#title_bar_label {{ color: {BILI_PINK}; font-weight: 700; font-size: 14px; letter-spacing: 1px; }}
QLabel#section {{ color: #52525b; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; }}
QCheckBox {{ color: #18181b; }}
QCheckBox::indicator {{ border: 1px solid #d4d4d8; border-radius: 3px; background: #fff; }}
QCheckBox::indicator:checked {{ background: {BILI_PINK}; border-color: {BILI_PINK}; }}
QDialogButtonBox QPushButton {{ min-width: 72px; }}
""" + _NAV_STYLES


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
    cancelled = pyqtSignal()

    def __init__(self, url, height, output_dir, browser, entries=None, speed_limit=""):
        super().__init__()
        self.url = url
        self.height = height
        self.output_dir = output_dir
        self.browser = browser
        self.entries = entries
        self.speed_limit = speed_limit
        self._cancel = False
        self._paused = False
        self._temp_files: set[str] = set()

    def cancel(self):
        self._cancel = True

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def _cleanup_temp(self):
        for path in list(self._temp_files):
            for candidate in (path, path + ".part"):
                try:
                    if os.path.exists(candidate):
                        os.remove(candidate)
                except OSError:
                    pass

    def run(self):
        def progress_hook(d):
            while self._paused:
                QThread.msleep(100)
            if self._cancel:
                raise Exception("__cancelled__")
            filename = d.get("filename") or d.get("tmpfilename") or ""
            if filename:
                self._temp_files.add(filename)
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
            if self._cancel:
                self._cleanup_temp()
                self.cancelled.emit()
            else:
                self.finished.emit(self.output_dir)
        except Exception as e:
            if "__cancelled__" in str(e) or self._cancel:
                self._cleanup_temp()
                self.cancelled.emit()
            else:
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


class NavBar(QWidget):
    page_changed = pyqtSignal(int)

    _PAGES = [("🏠\n主页", 0), ("📥\n下载中心", 1), ("👤\n个人", 2)]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("nav_bar")
        self.setFixedWidth(72)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(4)

        self._btns = []
        for label, idx in self._PAGES:
            btn = QPushButton(label)
            btn.setObjectName("nav")
            btn.setFixedHeight(64)
            btn.clicked.connect(lambda _, i=idx: self._select(i))
            layout.addWidget(btn)
            self._btns.append(btn)

        layout.addStretch()
        self._select(0)

    def _select(self, idx):
        for i, btn in enumerate(self._btns):
            btn.setObjectName("nav_active" if i == idx else "nav")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.page_changed.emit(idx)


_DL_MARGIN_H = 14
_DL_MARGIN_V = 10
_DL_BTN_W = 26
_DL_BTN_H = 26
_DL_BTN_GAP = 6
_DL_BAR_H = 5
_DL_BAR_BOTTOM = 12


class DownloadDelegate(QStyledItemDelegate):
    pause_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)

    def __init__(self, parent=None, is_dark=True):
        super().__init__(parent)
        self._dark = is_dark

    def set_dark(self, is_dark: bool):
        self._dark = is_dark

    def _colors(self):
        if self._dark:
            return {
                "bg": QColor("#27272a"),
                "text": QColor("#fafafa"),
                "muted": QColor("#a1a1aa"),
                "track": QColor("#3f3f46"),
                "btn_bg": QColor("#3f3f46"),
                "btn_text": QColor("#a1a1aa"),
                "group_bg": QColor("#18181b"),
                "group_text": QColor("#a1a1aa"),
            }
        return {
            "bg": QColor("#ffffff"),
            "text": QColor("#18181b"),
            "muted": QColor("#71717a"),
            "track": QColor("#e4e4e7"),
            "btn_bg": QColor("#f4f4f5"),
            "btn_text": QColor("#52525b"),
            "group_bg": QColor("#f4f4f5"),
            "group_text": QColor("#71717a"),
        }

    def _bar_fill_color(self, state: str) -> QColor:
        if state == "completed":
            return QColor("#4ade80")
        if state in ("error", "cancelled"):
            return QColor("#ef4444")
        return QColor(BILI_PINK)

    def _btn_rects(self, rect):
        cx = rect.right() - _DL_MARGIN_H
        cy = rect.top() + _DL_MARGIN_V + _DL_BTN_H // 2
        cancel = QRectF(cx - _DL_BTN_W, cy - _DL_BTN_H // 2, _DL_BTN_W, _DL_BTN_H)
        pause = QRectF(cx - _DL_BTN_W * 2 - _DL_BTN_GAP, cy - _DL_BTN_H // 2, _DL_BTN_W, _DL_BTN_H)
        return pause, cancel

    def _delete_rect(self, rect):
        cx = rect.right() - _DL_MARGIN_H
        cy = rect.top() + _DL_MARGIN_V + _DL_BTN_H // 2
        return QRectF(cx - _DL_BTN_W, cy - _DL_BTN_H // 2, _DL_BTN_W, _DL_BTN_H)

    def sizeHint(self, option, index):
        data = index.data(Qt.ItemDataRole.UserRole)
        if data and data.get("is_group"):
            return QSize(0, 40)
        return QSize(0, 72)

    def paint(self, painter, option, index):
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect
        c = self._colors()

        # ── group header ──────────────────────────────────────────────────────
        if data.get("is_group"):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(c["group_bg"]))
            painter.drawRoundedRect(QRectF(rect).adjusted(2, 2, -2, -2), 6, 6)

            arrow = "▾" if data.get("expanded", True) else "▸"
            label = f"{arrow}  {data.get('title', '')}"
            fnt = QFont(painter.font())
            fnt.setBold(True)
            fnt.setPointSize(9)
            painter.setFont(fnt)
            painter.setPen(QPen(c["group_text"]))
            painter.drawText(
                QRectF(rect.left() + _DL_MARGIN_H, rect.top(), rect.width() - _DL_MARGIN_H * 2, rect.height()),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                label,
            )
            painter.restore()
            return

        # ── episode / single item ─────────────────────────────────────────────
        state = data.get("state", "downloading")
        title = data.get("title", "")
        status_text = data.get("status_text", "")
        progress = data.get("progress", 0)
        is_ep = data.get("is_episode", False)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(c["bg"]))
        left_margin = _DL_MARGIN_H * 2 if is_ep else _DL_MARGIN_H
        painter.drawRoundedRect(QRectF(rect).adjusted(left_margin - 6, 2, -2, -2), 6, 6)

        active = state in ("downloading", "paused")
        is_error = state == "error"

        pause_rect, cancel_rect = self._btn_rects(rect)
        del_rect = self._delete_rect(rect)

        # title
        title_font = QFont(painter.font())
        title_font.setBold(True)
        title_font.setPointSize(10)
        painter.setFont(title_font)
        painter.setPen(QPen(c["text"]))
        if active:
            title_right = int(pause_rect.left()) - 8
        elif is_error:
            title_right = int(del_rect.left()) - 8
        else:
            title_right = rect.right() - _DL_MARGIN_H
        title_rect = QRectF(rect.left() + left_margin, rect.top() + _DL_MARGIN_V,
                            title_right - rect.left() - left_margin, _DL_BTN_H)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)

        # status text
        if status_text:
            sf = QFont(painter.font())
            sf.setBold(False)
            sf.setPointSize(9)
            painter.setFont(sf)
            if state == "completed":
                painter.setPen(QPen(QColor("#4ade80")))
            elif is_error:
                painter.setPen(QPen(QColor("#ef4444")))
            else:
                painter.setPen(QPen(c["muted"]))
            if active:
                status_right = int(pause_rect.left()) - 4
            elif is_error:
                status_right = int(del_rect.left()) - 4
            else:
                status_right = rect.right() - _DL_MARGIN_H
            status_rect = QRectF(rect.left() + left_margin, rect.top() + _DL_MARGIN_V,
                                 status_right - rect.left() - left_margin, _DL_BTN_H)
            painter.drawText(status_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, status_text)

        # progress bar
        bar_y = rect.bottom() - _DL_BAR_BOTTOM - _DL_BAR_H
        bar_rect = QRectF(rect.left() + left_margin, bar_y,
                          rect.width() - left_margin - _DL_MARGIN_H, _DL_BAR_H)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(c["track"]))
        painter.drawRoundedRect(bar_rect, 2, 2)
        if progress > 0:
            fill_w = bar_rect.width() * progress / 100
            painter.setBrush(QBrush(self._bar_fill_color(state)))
            painter.drawRoundedRect(QRectF(bar_rect.left(), bar_rect.top(), fill_w, _DL_BAR_H), 2, 2)

        # active buttons: pause + cancel
        if active:
            for brect, icon in ((pause_rect, "⏸" if state != "paused" else "▶"), (cancel_rect, "✕")):
                painter.setBrush(QBrush(c["btn_bg"]))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(brect, 4, 4)
                bf = QFont(painter.font())
                bf.setPointSize(9)
                painter.setFont(bf)
                painter.setPen(QPen(c["btn_text"]))
                painter.drawText(brect, Qt.AlignmentFlag.AlignCenter, icon)

        # error: delete button
        if is_error:
            painter.setBrush(QBrush(QColor("#3f1a1a") if self._dark else QColor("#fee2e2")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(del_rect, 4, 4)
            bf = QFont(painter.font())
            bf.setPointSize(9)
            painter.setFont(bf)
            painter.setPen(QPen(QColor("#ef4444")))
            painter.drawText(del_rect, Qt.AlignmentFlag.AlignCenter, "✕")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        from PyQt6.QtCore import QEvent
        if event.type() != QEvent.Type.MouseButtonRelease:
            return False
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data:
            return False

        pos = event.position() if hasattr(event, "position") else event.pos()

        # group header: toggle expand
        if data.get("is_group"):
            self.group_toggle_requested = getattr(self, "group_toggle_requested", None)
            if self.group_toggle_requested:
                self.group_toggle_requested.emit(data["key"])
            return True

        state = data.get("state", "downloading")
        key = data["key"]

        if state in ("downloading", "paused"):
            _, cancel_rect = self._btn_rects(option.rect)
            pause_rect, _ = self._btn_rects(option.rect)
            if cancel_rect.contains(pos.x(), pos.y()):
                self.cancel_clicked.emit(key)
                return True
            if pause_rect.contains(pos.x(), pos.y()):
                self.pause_clicked.emit(key)
                return True

        if state == "error":
            if self._delete_rect(option.rect).contains(pos.x(), pos.y()):
                self.delete_clicked.emit(key)
                return True

        return False


class DragListView(QListView):
    """QListView that swaps UserRole dicts directly on drag-drop, avoiding Qt mime serialization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_source_row: int | None = None
        self.setDragEnabled(False)          # we handle it ourselves
        self.setAcceptDrops(False)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self.indexAt(event.pos())
            if idx.isValid():
                d = idx.data(Qt.ItemDataRole.UserRole)
                # only drag non-group rows
                if d and not d.get("is_group"):
                    self._drag_source_row = idx.row()
                    self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_source_row is not None:
            idx = self.indexAt(event.pos())
            if idx.isValid() and idx.row() != self._drag_source_row:
                target_d = idx.data(Qt.ItemDataRole.UserRole)
                # don't drop onto group headers
                if target_d and not target_d.get("is_group"):
                    self._swap_rows(self._drag_source_row, idx.row())
                    self._drag_source_row = idx.row()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_source_row = None
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().mouseReleaseEvent(event)

    def _swap_rows(self, src: int, dst: int):
        model = self.model()
        src_item = model.item(src)
        dst_item = model.item(dst)
        if src_item is None or dst_item is None:
            return
        src_data = src_item.data(Qt.ItemDataRole.UserRole)
        dst_data = dst_item.data(Qt.ItemDataRole.UserRole)
        src_item.setData(dst_data, Qt.ItemDataRole.UserRole)
        dst_item.setData(src_data, Qt.ItemDataRole.UserRole)
        model.dataChanged.emit(model.index(src, 0), model.index(src, 0))
        model.dataChanged.emit(model.index(dst, 0), model.index(dst, 0))


class DownloadCenter(QWidget):
    pause_requested = pyqtSignal(int)
    cancel_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        hdr = QLabel("下载中心")
        hdr.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(hdr)

        sub = QLabel("拖动行可调整顺序")
        sub.setObjectName("section")
        layout.addWidget(sub)

        self._model = QStandardItemModel(self)
        self._model.setItemPrototype(QStandardItem())

        self._delegate = DownloadDelegate(is_dark=True)
        self._delegate.pause_clicked.connect(self.pause_requested)
        self._delegate.cancel_clicked.connect(self.cancel_requested)
        self._delegate.delete_clicked.connect(self.delete_requested)
        self._delegate.group_toggle_requested = pyqtSignal(int)

        self._view = DragListView()
        self._view.setModel(self._model)
        self._view.setItemDelegate(self._delegate)
        self._view.setSpacing(4)
        self._view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._view.setFrameShape(QFrame.Shape.NoFrame)
        self._view.clicked.connect(self._on_view_clicked)
        layout.addWidget(self._view)

        # group_key -> list of ep keys
        self._groups: dict[int, list[int]] = {}
        # group_key -> expanded
        self._group_expanded: dict[int, bool] = {}

    def set_dark(self, is_dark: bool):
        self._delegate.set_dark(is_dark)
        self._view.viewport().update()

    def _find_row(self, key: int) -> int | None:
        for row in range(self._model.rowCount()):
            item = self._model.item(row)
            d = item.data(Qt.ItemDataRole.UserRole)
            if d and d.get("key") == key:
                return row
        return None

    def _update_item(self, row: int, updates: dict):
        item = self._model.item(row)
        d = dict(item.data(Qt.ItemDataRole.UserRole))
        d.update(updates)
        item.setData(d, Qt.ItemDataRole.UserRole)
        idx = self._model.index(row, 0)
        self._model.dataChanged.emit(idx, idx)

    def _make_item(self, data: dict, draggable=True) -> QStandardItem:
        item = QStandardItem()
        item.setData(data, Qt.ItemDataRole.UserRole)
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if draggable:
            flags |= Qt.ItemFlag.ItemIsDragEnabled
        item.setFlags(flags)
        return item

    def add_download(self, key: int, title: str):
        item = self._make_item({
            "key": key, "title": title, "progress": 0,
            "speed": "", "state": "downloading", "status_text": "准备中...",
            "is_episode": False,
        })
        self._model.insertRow(0, item)

    def add_episode(self, group_key: int, series_title: str, ep_key: int, ep_title: str):
        """Add an episode under a collapsible group. Creates group header if needed."""
        if group_key not in self._groups:
            # insert group header at top
            group_item = self._make_item({
                "key": group_key, "title": series_title,
                "is_group": True, "expanded": True,
            }, draggable=False)
            self._model.insertRow(0, group_item)
            self._groups[group_key] = []
            self._group_expanded[group_key] = True

        self._groups[group_key].append(ep_key)

        # find group row, insert episode right after it (and after existing episodes)
        group_row = self._find_row(group_key)
        insert_at = group_row + len(self._groups[group_key])  # after all existing eps

        ep_item = self._make_item({
            "key": ep_key, "title": ep_title, "progress": 0,
            "speed": "", "state": "downloading", "status_text": "准备中...",
            "is_episode": True, "group_key": group_key,
        })
        self._model.insertRow(insert_at, ep_item)

    def remove_item(self, key: int):
        row = self._find_row(key)
        if row is None:
            return
        d = self._model.item(row).data(Qt.ItemDataRole.UserRole)
        group_key = d.get("group_key")
        self._model.removeRow(row)

        if group_key is not None and group_key in self._groups:
            self._groups[group_key] = [k for k in self._groups[group_key] if k != key]
            # remove group header if no episodes left
            if not self._groups[group_key]:
                g_row = self._find_row(group_key)
                if g_row is not None:
                    self._model.removeRow(g_row)
                del self._groups[group_key]
                del self._group_expanded[group_key]

    def _on_view_clicked(self, index: QModelIndex):
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data or not data.get("is_group"):
            return
        key = data["key"]
        expanded = not self._group_expanded.get(key, True)
        self._group_expanded[key] = expanded
        g_row = self._find_row(key)
        if g_row is not None:
            self._update_item(g_row, {"expanded": expanded})
        # show/hide episode rows
        for ep_key in self._groups.get(key, []):
            ep_row = self._find_row(ep_key)
            if ep_row is not None:
                self._view.setRowHidden(ep_row, not expanded)

    def update_progress(self, key: int, pct: int, speed: str):
        row = self._find_row(key)
        if row is None:
            return
        status = f"{pct}%  {speed}" if speed else f"{pct}%"
        self._update_item(row, {"progress": pct, "speed": speed,
                                "state": "downloading", "status_text": status})

    def mark_done(self, key: int):
        row = self._find_row(key)
        if row is None:
            return
        self._update_item(row, {"progress": 100, "state": "completed", "status_text": "完成"})

    def mark_error(self, key: int, msg: str):
        row = self._find_row(key)
        if row is None:
            return
        self._update_item(row, {"state": "error", "status_text": msg})


class PersonalPage(QWidget):
    def __init__(self, settings, on_open_settings, on_wallpaper_change, on_clear_cache, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.on_wallpaper_change = on_wallpaper_change

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        hdr = QLabel("个人")
        hdr.setStyleSheet("font-size: 18px; font-weight: bold;")
        outer.addWidget(hdr)

        # App info card
        info_inner = QVBoxLayout()
        info_inner.setContentsMargins(20, 18, 20, 18)
        info_inner.setSpacing(8)

        app_name = QLabel("BILI-DOWNLOADER")
        app_name.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {BILI_PINK}; letter-spacing: 2px;")
        info_inner.addWidget(app_name)

        version = QLabel("版本 1.0.0")
        version.setObjectName("section")
        info_inner.addWidget(version)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #3f3f46;")
        info_inner.addWidget(sep)

        github_lbl = QLabel("GitHub: github.com/Fem-boy_sc")
        github_lbl.setStyleSheet(f"color: {BILI_PINK};")
        info_inner.addWidget(github_lbl)

        copyright_lbl = QLabel("© 2025 Fem-boy_sc  保留所有权利")
        copyright_lbl.setObjectName("section")
        info_inner.addWidget(copyright_lbl)

        outer.addWidget(_card(info_inner))

        # Wallpaper card
        wp_inner = QVBoxLayout()
        wp_inner.setContentsMargins(20, 18, 20, 18)
        wp_inner.setSpacing(10)

        wp_sec = QLabel("背景壁纸")
        wp_sec.setObjectName("section")
        wp_inner.addWidget(wp_sec)

        self.wp_path_label = QLabel(settings.get("wallpaper") or "未设置")
        self.wp_path_label.setWordWrap(True)
        self.wp_path_label.setStyleSheet("font-size: 12px;")
        wp_inner.addWidget(self.wp_path_label)

        wp_btn_row = QHBoxLayout()
        wp_btn_row.setSpacing(8)
        pick_btn = QPushButton("选择壁纸")
        pick_btn.clicked.connect(self._pick_wallpaper)
        wp_btn_row.addWidget(pick_btn)
        clear_wp_btn = QPushButton("清除壁纸")
        clear_wp_btn.setObjectName("ghost")
        clear_wp_btn.clicked.connect(self._clear_wallpaper)
        wp_btn_row.addWidget(clear_wp_btn)
        wp_btn_row.addStretch()
        wp_inner.addLayout(wp_btn_row)

        outer.addWidget(_card(wp_inner))

        # Cache card
        cache_inner = QVBoxLayout()
        cache_inner.setContentsMargins(20, 18, 20, 18)
        cache_inner.setSpacing(10)

        cache_sec = QLabel("缓存管理")
        cache_sec.setObjectName("section")
        cache_inner.addWidget(cache_sec)

        cache_desc = QLabel("仅清除下载中断留下的 .part 临时文件，不影响已下载的视频")
        cache_desc.setStyleSheet("font-size: 12px;")
        cache_desc.setWordWrap(True)
        cache_inner.addWidget(cache_desc)

        cache_btn_row = QHBoxLayout()
        cache_btn_row.setSpacing(8)
        self._cache_btn = QPushButton("一键清缓存")
        self._cache_btn.clicked.connect(lambda: self._do_clear_cache(on_clear_cache))
        cache_btn_row.addWidget(self._cache_btn)
        self._cache_result = QLabel("")
        self._cache_result.setObjectName("section")
        cache_btn_row.addWidget(self._cache_result)
        cache_btn_row.addStretch()
        cache_inner.addLayout(cache_btn_row)

        outer.addWidget(_card(cache_inner))

        # Settings shortcut card
        cfg_inner = QVBoxLayout()
        cfg_inner.setContentsMargins(20, 18, 20, 18)
        cfg_inner.setSpacing(10)

        cfg_sec = QLabel("应用设置")
        cfg_sec.setObjectName("section")
        cfg_inner.addWidget(cfg_sec)

        cfg_btn = QPushButton("偏好设置")
        cfg_btn.setObjectName("ghost")
        cfg_btn.clicked.connect(on_open_settings)
        cfg_inner.addWidget(cfg_btn)

        outer.addWidget(_card(cfg_inner))
        outer.addStretch()

    def _do_clear_cache(self, callback):
        count = callback()
        self._cache_result.setText(f"已清除 {count} 个文件" if count else "无残留缓存")
        QTimer.singleShot(3000, lambda: self._cache_result.setText(""))

    def _pick_wallpaper(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择壁纸", "", "图片文件 (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path:
            self.settings.set("wallpaper", path)
            self.wp_path_label.setText(path)
            self.on_wallpaper_change(path)

    def _clear_wallpaper(self):
        self.settings.set("wallpaper", "")
        self.wp_path_label.setText("未设置")
        self.on_wallpaper_change("")


class RootWidget(QWidget):
    """Central widget that paints the wallpaper behind all content."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._wallpaper: QPixmap | None = None

    def set_wallpaper(self, path: str):
        if path and os.path.isfile(path):
            pix = QPixmap(path)
            self._wallpaper = pix if not pix.isNull() else None
        else:
            self._wallpaper = None
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._wallpaper:
            p = QPainter(self)
            p.drawPixmap(
                self.rect(),
                self._wallpaper.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                ),
            )
            p.fillRect(self.rect(), QColor(0, 0, 0, 80))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.theme = self.settings.get("theme", "dark")
        self._info = None
        self._worker = None
        self._dl_worker = None
        self._dl_key = 0
        self._dl_workers = {}  # key -> worker mapping
        self._output_dirs: set[str] = set()  # all dirs ever downloaded to

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(860, 680)

        self._root = RootWidget()
        self._root.setObjectName("root")
        self.setCentralWidget(self._root)

        root_layout = QVBoxLayout(self._root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.title_bar = TitleBar(self, self._toggle_theme, self.close)
        root_layout.addWidget(self.title_bar)

        body_row = QHBoxLayout()
        body_row.setContentsMargins(0, 0, 0, 0)
        body_row.setSpacing(0)
        root_layout.addLayout(body_row)

        self.nav = NavBar()
        self.nav.page_changed.connect(self._switch_page)
        body_row.addWidget(self.nav)

        self.stack = QStackedWidget()
        body_row.addWidget(self.stack)

        self._build_home_page()
        self.download_center = DownloadCenter()
        self.download_center.pause_requested.connect(self._pause_download)
        self.download_center.cancel_requested.connect(self._cancel_download_by_key)
        self.download_center.delete_requested.connect(self.download_center.remove_item)
        self.stack.addWidget(self.download_center)
        self._personal_page = PersonalPage(
            self.settings, self._open_settings, self._on_wallpaper_change, self._clear_cache
        )
        self.stack.addWidget(self._personal_page)

        self._apply_theme()
        self._load_settings_to_ui()
        self._root.set_wallpaper(self.settings.get("wallpaper", ""))

    def _build_home_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

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

        self.stack.addWidget(scroll)

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

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("ghost")
        self.cancel_btn.setFixedWidth(60)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_download)
        row.addWidget(self.cancel_btn)
        inner.addLayout(row)

        self.body_layout.addWidget(_card(inner))

    def _build_progress_card(self):
        inner = QVBoxLayout()
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(8)

        sec = QLabel("当前下载进度")
        sec.setObjectName("section")
        inner.addWidget(sec)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        inner.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        inner.addWidget(self.status_label)

        self.body_layout.addWidget(_card(inner))

    def _switch_page(self, idx):
        self.stack.setCurrentIndex(idx)

    def _apply_theme(self):
        qss = DARK_QSS if self.theme == "dark" else LIGHT_QSS
        self.setStyleSheet(qss)
        self.title_bar.theme_btn.setText("☀" if self.theme == "dark" else "🌙")
        self.download_center.set_dark(self.theme == "dark")

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

    def _on_wallpaper_change(self, path: str):
        self._root.set_wallpaper(path)

    def _clear_cache(self) -> int:
        dirs = set(self._output_dirs)
        default = self.settings.get("download_path", "")
        if default:
            dirs.add(default)
        count = 0
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for fname in os.listdir(d):
                if fname.endswith(".part"):
                    try:
                        os.remove(os.path.join(d, fname))
                        count += 1
                    except OSError:
                        pass
        return count

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
        if output_dir:
            self._output_dirs.add(output_dir)
        browser = self.browser_combo.currentText()
        if browser == "不使用Cookie":
            browser = None
        speed_limit = self.settings.get("speed_limit", "")

        series_title = self._info.get("title", "未知")
        all_entries = self._info.get("entries", [])
        selected_entries = []
        if all_entries and self.episodes_card.isVisible():
            selected_entries = [
                item.data(Qt.ItemDataRole.UserRole)
                for item in self.episode_list.selectedItems()
            ]

        self.dl_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("下载中...")

        if selected_entries:
            # 串行下载：先把所有集注册到下载中心，再逐集启动
            self._dl_key += 1
            group_key = self._dl_key
            ep_map = {e["index"]: e["title"] for e in all_entries}

            # 预先分配 key 并注册 UI 行
            queue: list[tuple[int, int, str]] = []  # (key, ep_idx, ep_title)
            for ep_idx in selected_entries:
                self._dl_key += 1
                key = self._dl_key
                ep_title = ep_map.get(ep_idx, f"第{ep_idx+1}集")
                self.download_center.add_episode(group_key, series_title, key, ep_title)
                queue.append((key, ep_idx, ep_title))

            self._ep_queue = queue          # 待下载队列
            self._ep_group_key = group_key
            self._ep_params = (url, height, output_dir, browser, speed_limit)
            self._start_next_episode()
        else:
            # 单视频下载
            self._dl_key += 1
            key = self._dl_key
            self.download_center.add_download(key, series_title)
            self._dl_worker = DownloadWorker(url, height, output_dir, browser, None, speed_limit)
            self._dl_workers[key] = self._dl_worker
            self._dl_worker.progress.connect(lambda pct, spd: self._on_progress(key, pct, spd))
            self._dl_worker.finished.connect(lambda _: self._on_done(key, series_title))
            self._dl_worker.cancelled.connect(lambda: self._on_cancelled(key))
            self._dl_worker.error.connect(lambda msg: self._on_error(key, msg))
            self._dl_worker.start()

    def _start_next_episode(self):
        if not getattr(self, "_ep_queue", None):
            return
        key, ep_idx, ep_title = self._ep_queue.pop(0)
        url, height, output_dir, browser, speed_limit = self._ep_params
        worker = DownloadWorker(url, height, output_dir, browser, [ep_idx], speed_limit)
        self._dl_workers[key] = worker
        self._dl_worker = worker
        worker.progress.connect(lambda pct, spd, k=key: self._on_progress(k, pct, spd))
        worker.finished.connect(lambda _, k=key, t=ep_title: self._on_done(k, t))
        worker.cancelled.connect(lambda k=key: self._on_cancelled(k))
        worker.error.connect(lambda msg, k=key: self._on_error(k, msg))
        worker.start()

    def _pause_download(self, key):
        if key in self._dl_workers:
            worker = self._dl_workers[key]
            if hasattr(worker, '_paused'):
                if worker._paused:
                    worker.resume()
                    row = self.download_center._find_row(key)
                    if row is not None:
                        self.download_center._update_item(row, {"state": "downloading"})
                else:
                    worker.pause()
                    row = self.download_center._find_row(key)
                    if row is not None:
                        self.download_center._update_item(row, {"state": "paused"})

    def _cancel_download_by_key(self, key):
        # if the key is still in the queue (not yet started), just remove it
        queue = getattr(self, "_ep_queue", [])
        for item in queue:
            if item[0] == key:
                self._ep_queue.remove(item)
                self.download_center.remove_item(key)
                return
        if key in self._dl_workers:
            worker = self._dl_workers[key]
            if worker.isRunning():
                worker.cancel()

    def _on_progress(self, key, pct, speed):
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"下载中... {pct}%  {speed}")
        self.download_center.update_progress(key, pct, speed)

    def _cancel_download(self):
        # clear queued episodes first so _on_cancelled doesn't start the next one
        self._ep_queue = []
        if self._dl_worker and self._dl_worker.isRunning():
            self._dl_worker.cancel()
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("正在取消...")

    def _on_done(self, key, title):
        self.download_center.mark_done(key)
        if key in self._dl_workers:
            del self._dl_workers[key]
        CompletionToast(self._root, f"下载完成 · {title}")
        if getattr(self, "_ep_queue", None):
            self._start_next_episode()
        elif not self._dl_workers:
            self._reset_home_progress()

    def _on_cancelled(self, key):
        self.download_center.remove_item(key)
        if key in self._dl_workers:
            del self._dl_workers[key]
        # cancel remaining queued episodes too
        for queued_key, _, _ in getattr(self, "_ep_queue", []):
            self.download_center.remove_item(queued_key)
        self._ep_queue = []
        if not self._dl_workers:
            self._reset_home_progress()

    def _on_error(self, key, msg):
        self.status_label.setText(f"错误: {msg}")
        self.download_center.mark_error(key, msg)
        if key in self._dl_workers:
            del self._dl_workers[key]
        # continue with next episode even if one fails
        if getattr(self, "_ep_queue", None):
            self._start_next_episode()
        elif not self._dl_workers:
            self._reset_home_progress()

    def _reset_home_progress(self):
        self.progress_bar.setValue(0)
        self.status_label.setText("就绪")
        self.dl_btn.setEnabled(bool(self._info))
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("BILI-DOWNLOADER")
    win = MainWindow()
    win.resize(900, 700)
    win.show()
    sys.exit(app.exec())
