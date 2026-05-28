"""
400×50 frameless always-on-top mini player bar.
Semi-transparent dark gray — Themia-style.
SVG icons with toggle buttons.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QEvent, QSize, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QLabel,
    QFileDialog, QMenu, QApplication, QSystemTrayIcon,
)
from PySide6.QtGui import (
    QMouseEvent, QDragEnterEvent, QDropEvent, QAction,
    QPainter, QColor, QIcon,
)

from core.player import MusicPlayer
from utils.format import format_time

MINI_WIDTH = 400
MINI_HEIGHT = 50
AUDIO_EXTS = {".mp3", ".flac", ".wav", ".ogg", ".aac", ".m4a", ".wma", ".opus"}
ICON_SZ = QSize(18, 18)

# ── Resource path ────────────────────────────────────────────────────
_RESOURCE = Path(__file__).parent.parent / "resource"


def _icon(name: str) -> QIcon:
    return QIcon(str(_RESOURCE / f"{name}.svg"))


STYLESHEET = """
    QWidget#MiniBar {
        background: transparent;
    }
    QPushButton {
        background: transparent;
        border: none;
        min-width: 20px;
        max-width: 20px;
        min-height: 20px;
        max-height: 20px;
        border-radius: 3px;
        padding: 0px;
    }
    QPushButton:hover {
        background-color: rgba(255, 255, 255, 25);
    }
    QPushButton:pressed {
        background-color: rgba(255, 255, 255, 45);
    }
    QLabel {
        background: transparent;
        color: rgba(200, 200, 215, 155);
        font-size: 11px;
    }
    QLabel#TimeLabel {
        font-family: "Consolas", "Courier New", monospace;
        font-size: 10px;
        min-width: 68px;
        max-width: 68px;
    }
    QSlider::groove:horizontal {
        border: none;
        height: 3px;
        background: rgba(200, 200, 215, 50);
        border-radius: 1px;
    }
    QSlider::handle:horizontal {
        background: rgba(200, 200, 215, 170);
        border: none;
        width: 8px;
        height: 8px;
        margin: -2px 0;
        border-radius: 4px;
    }
    QSlider::handle:horizontal:hover {
        background: rgba(220, 220, 235, 220);
    }
    QSlider::sub-page:horizontal {
        background: rgba(200, 200, 215, 110);
        border-radius: 1px;
    }
"""


class SeekSlider(QSlider):
    """QSlider that jumps to clicked position."""

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            ratio = event.position().x() / self.width()
            self.setValue(int(ratio * self.maximum()))
        super().mousePressEvent(event)


class TrackPopup(QWidget):
    """Popup playlist list that appears below the track indicator."""
    track_selected = Signal(int)

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(220)
        self._above: bool = False
        self._playlist: list[str] = []
        self._current_index: int = 0
        self._labels: list[QLabel] = []
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 4, 0, 4)
        self._layout.setSpacing(1)
        self.installEventFilter(self)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(24, 24, 32, 140))
        painter.drawRoundedRect(self.rect(), 6, 6)

    def set_tracks(self, playlist: list[str], current_index: int) -> None:
        """Rebuild the track list from playlist paths."""
        self._playlist = playlist
        self._current_index = current_index
        for lbl in self._labels:
            self._layout.removeWidget(lbl)
            lbl.deleteLater()
        self._labels.clear()

        total = len(playlist)
        max_show = 8

        if total <= max_show:
            visible_indices = list(range(total))
            overflow_count = 0
        else:
            visible = max_show - 1  # 7 songs + 1 overflow line
            half = visible // 2
            start = max(0, current_index - half)
            end = min(total, start + visible)
            start = max(0, end - visible)
            visible_indices = list(range(start, end))
            overflow_count = total - end

        # Build items: (text, track_index | None, is_current)
        items: list[tuple[str, int | None, bool]] = []
        for idx in visible_indices:
            name = os.path.basename(playlist[idx])
            items.append((f"{idx + 1}. {name}", idx, idx == current_index))

        if overflow_count > 0:
            items.append((f"... 还有 {overflow_count} 首", None, False))

        if self._above:
            items.reverse()

        for text, track_idx, is_current in items:
            lbl = QLabel(text)
            if track_idx is None:
                lbl.setEnabled(False)
                lbl.setStyleSheet(
                    "color: rgba(200,200,215,160); padding: 2px 8px; font-size: 10px;"
                )
            else:
                lbl.setProperty("track_index", track_idx)
                lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                if is_current:
                    lbl.setStyleSheet(
                        "color: rgba(220,220,235,220); padding: 2px 8px; font-size: 10px; "
                        "background: rgba(255,255,255,18); border-radius: 3px;"
                    )
                else:
                    lbl.setStyleSheet(
                        "color: rgba(200,200,215,160); padding: 2px 8px; font-size: 10px; "
                        "border-radius: 3px;"
                    )
                lbl.installEventFilter(self)
            self._labels.append(lbl)
            self._layout.addWidget(lbl)

        self.setFixedHeight(len(items) * 20 + 10)

    def eventFilter(self, obj, event) -> bool:
        if isinstance(obj, QLabel) and obj.property("track_index") is not None:
            etype = event.type()
            if etype == QEvent.Type.MouseButtonPress:
                idx = obj.property("track_index")
                if idx != self._current_index:
                    self.track_selected.emit(idx)
                self.hide()
                return True
            elif etype == QEvent.Type.Enter:
                idx = obj.property("track_index")
                if idx != self._current_index:
                    obj.setStyleSheet(
                        "color: rgba(220,220,235,200); padding: 2px 8px; font-size: 10px; "
                        "background: rgba(255,255,255,10); border-radius: 3px;"
                    )
            elif etype == QEvent.Type.Leave:
                idx = obj.property("track_index")
                if idx != self._current_index:
                    obj.setStyleSheet(
                        "color: rgba(200,200,215,160); padding: 2px 8px; font-size: 10px; "
                        "border-radius: 3px;"
                    )
        return False

    def show_at(self, bar: QWidget, playlist: list[str], current_index: int) -> None:
        """Position popup 3px from the bar edge, flipping above if overflow."""
        GAP = 3
        self._above = False
        self.set_tracks(playlist, current_index)
        popup_h = self.height()

        bar_global = bar.mapToGlobal(QPoint(0, 0))
        screen = QApplication.primaryScreen().availableGeometry()

        if bar_global.y() + bar.height() + GAP + popup_h > screen.bottom():
            self._above = True
            self.set_tracks(playlist, current_index)

        x = bar_global.x() + (bar.width() - self.width()) // 2
        if self._above:
            pos = QPoint(x, bar_global.y() - popup_h - GAP)
        else:
            pos = QPoint(x, bar_global.y() + bar.height() + GAP)
        self.move(pos)
        self.show()


class TrackIndicator(QLabel):
    """Clickable track count indicator: '3 / 12 ▾'."""
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__("0 / 0", parent)
        self._current: int = 0
        self._total: int = 0
        self.setFixedHeight(25)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QLabel {
                color: rgba(200, 200, 215, 150);
                font-size: 10px;
                padding: 2px 6px;
                background: rgba(255, 255, 255, 8);
                border-radius: 4px;
            }
            QLabel:hover {
                color: rgba(220, 220, 235, 200);
                background: rgba(255, 255, 255, 18);
            }
        """)

    def set_count(self, current: int, total: int) -> None:
        self._current = current
        self._total = total
        if total == 0:
            self.setText("0 / 0")
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setToolTip("")
        else:
            self.setText(f"{current + 1} / {total} ▾")
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._total > 0:
            self.clicked.emit()
        super().mousePressEvent(event)


class MiniBar(QWidget):
    def __init__(self, player: MusicPlayer | None = None):
        super().__init__()
        self._player = player or MusicPlayer(self)
        self._muted = False
        self._pre_mute_volume = 0.7
        self._duration_ms = 0
        self._seeking = False

        # Playlist popup
        self._track_popup: TrackPopup | None = None

        # Drag state
        self._drag_press_global: QPoint | None = None
        self._drag_window_start: QPoint | None = None
        self._drag_active = False

        self._setup_window()
        self._build_ui()
        self._connect_signals()
        self._setup_tray()
        self._player.set_volume(0.7)

    def _setup_window(self) -> None:
        self.setWindowTitle("Mini Player")
        self.setFixedSize(MINI_WIDTH, MINI_HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("MiniBar")
        self.setStyleSheet(STYLESHEET)
        self.setAcceptDrops(True)
        QApplication.instance().installEventFilter(self)

    def _setup_tray(self) -> None:
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(_icon("tray_icon"))
        self._tray_icon.setToolTip("Mini Player")

        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: rgba(30, 30, 40, 240);
                border: 1px solid rgba(255,255,255,20);
                border-radius: 6px; padding: 4px; color: rgba(220,220,235,200);
            }
            QMenu::item { padding: 5px 20px; border-radius: 3px; }
            QMenu::item:selected { background-color: rgba(255,255,255,18); }
            QMenu::separator {
                height: 1px; background: rgba(255,255,255,20); margin: 3px 8px;
            }
        """)

        self._tray_show_action = QAction("隐藏", self)
        self._tray_show_action.triggered.connect(self._toggle_visibility)
        tray_menu.addAction(self._tray_show_action)
        tray_menu.addSeparator()

        play_action = QAction("播放 / 暂停", self)
        play_action.triggered.connect(self._on_play_clicked)
        tray_menu.addAction(play_action)

        prev_action = QAction("上一首", self)
        prev_action.triggered.connect(self._player.prev)
        tray_menu.addAction(prev_action)

        next_action = QAction("下一首", self)
        next_action.triggered.connect(self._player.next)
        tray_menu.addAction(next_action)
        tray_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(exit_action)

        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_visibility()

    def _toggle_visibility(self) -> None:
        if self.isVisible():
            if self._track_popup and self._track_popup.isVisible():
                self._track_popup.hide()
            self.hide()
            self._tray_show_action.setText("显示")
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            self._tray_show_action.setText("隐藏")

    def _quit_app(self) -> None:
        self._tray_icon.hide()
        self._player.cleanup()
        QApplication.instance().removeEventFilter(self)
        QApplication.quit()

    def _ensure_popup(self) -> TrackPopup:
        if self._track_popup is None:
            self._track_popup = TrackPopup(None)
            self._track_popup.track_selected.connect(self._player.jump_to)
        return self._track_popup

    def _on_track_indicator_clicked(self) -> None:
        if len(self._player.playlist) == 0:
            return
        popup = self._ensure_popup()
        if popup.isVisible():
            popup.hide()
            return
        popup.show_at(self, self._player.playlist, self._player.current_index)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(24, 24, 32, 140))
        painter.drawRoundedRect(self.rect(), 10, 10)

    # ── Drag-from-anywhere via event filter ──────────────────────────

    def _is_descendant(self, obj) -> bool:
        from PySide6.QtWidgets import QWidget as _QWidget
        if not isinstance(obj, _QWidget):
            return False
        w = obj
        while w is not None:
            if w is self:
                return True
            w = w.parentWidget()
        return False

    def eventFilter(self, obj, event) -> bool:
        if not self._is_descendant(obj):
            return False
        if isinstance(obj, QSlider):
            return False

        etype = event.type()
        if etype == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_press_global = event.globalPosition().toPoint()
                self._drag_window_start = self.pos()
                self._drag_active = False
        elif etype == QEvent.Type.MouseMove:
            if self._drag_press_global is not None:
                delta = event.globalPosition().toPoint() - self._drag_press_global
                if self._drag_active:
                    self.move(self._drag_window_start + delta)
                    return True
                elif delta.manhattanLength() > 5:
                    self._drag_active = True
                    self.move(self._drag_window_start + delta)
                    return True
        elif etype == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                was_drag = self._drag_active
                self._drag_press_global = None
                self._drag_window_start = None
                self._drag_active = False
                if was_drag:
                    return True
        return False

    # ── UI ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(4)

        # Prev
        self._btn_prev = QPushButton()
        self._btn_prev.setIcon(_icon("previous"))
        self._btn_prev.setIconSize(ICON_SZ)
        self._btn_prev.setToolTip("上一首")
        layout.addWidget(self._btn_prev)

        # Play / Pause (toggle)
        self._btn_play = QPushButton()
        self._btn_play.setIcon(_icon("play"))
        self._btn_play.setIconSize(ICON_SZ)
        self._btn_play.setToolTip("播放 / 暂停")
        layout.addWidget(self._btn_play)

        # Next
        self._btn_next = QPushButton()
        self._btn_next.setIcon(_icon("next"))
        self._btn_next.setIconSize(ICON_SZ)
        self._btn_next.setToolTip("下一首")
        layout.addWidget(self._btn_next)

        # Repeat mode (toggle: repeat_all → repeat_single → shuffle)
        self._btn_repeat = QPushButton()
        self._btn_repeat.setIcon(_icon("repeat_all"))
        self._btn_repeat.setIconSize(ICON_SZ)
        self._btn_repeat.setToolTip("列表循环")
        layout.addWidget(self._btn_repeat)

        # Track indicator (playlist position)
        self._track_indicator = TrackIndicator(self)
        layout.addWidget(self._track_indicator)

        # Progress
        self._progress = SeekSlider(Qt.Orientation.Horizontal)
        self._progress.setRange(0, 1000)
        self._progress.setValue(0)
        self._progress.setToolTip("播放进度")
        layout.addWidget(self._progress, 1)

        layout.addSpacing(4)

        # Time
        self._time_label = QLabel("0:00 / 0:00")
        self._time_label.setObjectName("TimeLabel")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._time_label)

        layout.addSpacing(3)

        # Volume icon (auto-switch: high / medium / mute)
        self._btn_vol = QPushButton()
        self._btn_vol.setIcon(_icon("volume_high"))
        self._btn_vol.setIconSize(ICON_SZ)
        self._btn_vol.setToolTip("静音 / 取消静音")
        layout.addWidget(self._btn_vol)

        # Volume slider
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(70)
        self._vol_slider.setToolTip("音量")
        self._vol_slider.setFixedWidth(44)
        self._vol_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none; height: 2px;
                background: rgba(200,200,215,45);
                border-radius: 1px;
            }
            QSlider::handle:horizontal {
                background: rgba(200,200,215,160);
                border: none; width: 7px; height: 7px;
                margin: -2px 0; border-radius: 3px;
            }
            QSlider::handle:horizontal:hover {
                background: rgba(220,220,235,210);
            }
            QSlider::sub-page:horizontal {
                background: rgba(200,200,215,100);
                border-radius: 1px;
            }
        """)
        layout.addWidget(self._vol_slider)

    def _connect_signals(self) -> None:
        self._btn_play.clicked.connect(self._on_play_clicked)
        self._btn_prev.clicked.connect(self._player.prev)
        self._btn_next.clicked.connect(self._player.next)
        self._btn_repeat.clicked.connect(self._on_repeat_clicked)
        self._btn_vol.clicked.connect(self._on_vol_clicked)
        self._progress.sliderPressed.connect(self._on_seek_press)
        self._progress.sliderReleased.connect(self._on_seek_release)
        self._progress.valueChanged.connect(self._on_progress_value_changed)
        self._vol_slider.valueChanged.connect(self._on_vol_slider_changed)
        self._player.position_changed.connect(self._on_position)
        self._player.duration_changed.connect(self._on_duration)
        self._player.track_changed.connect(self._on_track)
        self._player.playback_state_changed.connect(self._on_state)
        self._player.repeat_mode_changed.connect(self._on_repeat_mode_changed)
        self._track_indicator.clicked.connect(self._on_track_indicator_clicked)

    # ── Slots ────────────────────────────────────────────────────────

    def _on_play_clicked(self) -> None:
        if self._player.current_file is None:
            self._open_file_dialog()
            return
        if self._player.is_playing:
            self._player.pause()
        else:
            self._player.resume()

    def _on_repeat_clicked(self) -> None:
        """Cycle repeat mode via the player engine."""
        self._player.cycle_repeat_mode()

    def _on_repeat_mode_changed(self, mode: int) -> None:
        if mode == MusicPlayer.REPEAT_ALL:
            self._btn_repeat.setIcon(_icon("repeat_all"))
            self._btn_repeat.setToolTip("列表循环")
        elif mode == MusicPlayer.REPEAT_SINGLE:
            self._btn_repeat.setIcon(_icon("repeat_single"))
            self._btn_repeat.setToolTip("单曲循环")
        else:
            self._btn_repeat.setIcon(_icon("shuffle"))
            self._btn_repeat.setToolTip("随机播放")

    def _update_volume_icon(self, value: int) -> None:
        """Switch volume icon based on value."""
        if value == 0:
            self._btn_vol.setIcon(_icon("mute"))
        elif value <= 49:
            self._btn_vol.setIcon(_icon("volume_medium"))
        else:
            self._btn_vol.setIcon(_icon("volume_high"))

    def _on_vol_clicked(self) -> None:
        if self._muted:
            self._muted = False
            v = self._pre_mute_volume
            self._vol_slider.setValue(int(v * 100))
            self._player.set_volume(v)
            self._update_volume_icon(int(v * 100))
        else:
            self._muted = True
            self._pre_mute_volume = self._vol_slider.value() / 100.0
            self._vol_slider.setValue(0)
            self._player.set_volume(0)
            self._update_volume_icon(0)

    def _on_vol_slider_changed(self, value: int) -> None:
        vol = value / 100.0
        if vol > 0 and self._muted:
            self._muted = False
        elif vol == 0 and not self._muted:
            self._muted = True
        self._player.set_volume(vol)
        self._update_volume_icon(value)

    def _on_seek_press(self) -> None:
        self._seeking = True

    def _on_seek_release(self) -> None:
        self._seeking = False
        self._player.seek(int(self._duration_ms * self._progress.value() / 1000.0))

    def _on_progress_value_changed(self, value: int) -> None:
        if self._seeking and self._duration_ms > 0:
            pos_ms = int(self._duration_ms * value / 1000.0)
            self._time_label.setText(
                f"{format_time(pos_ms)} / {format_time(self._duration_ms)}"
            )

    def _on_position(self, pos_ms: int) -> None:
        if self._seeking or self._duration_ms <= 0:
            return
        self._progress.blockSignals(True)
        self._progress.setValue(int(pos_ms / self._duration_ms * 1000))
        self._progress.blockSignals(False)
        self._time_label.setText(
            f"{format_time(pos_ms)} / {format_time(self._duration_ms)}"
        )

    def _on_duration(self, duration_ms: int) -> None:
        self._duration_ms = duration_ms

    def _on_track(self, title: str, artist: str) -> None:
        tooltip = f"{artist} - {title}" if artist else title
        self.setToolTip(tooltip)
        self._tray_icon.setToolTip(tooltip)
        self._track_indicator.set_count(self._player.current_index, len(self._player.playlist))
        if self._track_popup and self._track_popup.isVisible():
            self._track_popup.set_tracks(self._player.playlist, self._player.current_index)

    def _on_state(self, playing: bool) -> None:
        self._btn_play.setIcon(_icon("pause" if playing else "play"))

    # ── File dialog ──────────────────────────────────────────────────

    def _open_file_dialog(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self, "打开音频文件", "",
            "Audio Files (*.mp3 *.flac *.wav *.ogg *.aac *.m4a *.wma *.opus);;All Files (*)",
        )
        if filepath:
            self._player.open_file(filepath)

    # ── Drag & Drop ──────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in AUDIO_EXTS:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in AUDIO_EXTS:
                self._player.open_file(url.toLocalFile())
                return

    # ── Right-click menu ─────────────────────────────────────────────

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(30, 30, 40, 240);
                border: 1px solid rgba(255,255,255,20);
                border-radius: 6px; padding: 4px; color: rgba(220,220,235,200);
            }
            QMenu::item { padding: 5px 20px; border-radius: 3px; }
            QMenu::item:selected { background-color: rgba(255,255,255,18); }
            QMenu::separator {
                height: 1px; background: rgba(255,255,255,20); margin: 3px 8px;
            }
        """)
        open_action = QAction("打开文件...", self)
        open_action.triggered.connect(self._open_file_dialog)
        menu.addAction(open_action)
        menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self._quit_app)
        menu.addAction(exit_action)
        menu.exec(event.globalPos())

    def closeEvent(self, event) -> None:
        self.hide()
        event.ignore()
