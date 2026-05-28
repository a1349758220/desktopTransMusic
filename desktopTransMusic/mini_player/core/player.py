"""
Music player engine wrapping pygame.mixer.music.
Signals allow the UI to react to playback changes without polling.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

import pygame.mixer
from PySide6.QtCore import QObject, QTimer, Signal
from mutagen import File as MutagenFile


SUPPORTED_EXTS = {".mp3", ".flac", ".wav", ".ogg", ".aac", ".m4a", ".wma", ".opus"}


def _read_metadata(filepath: str) -> tuple[str, str]:
    """Return (title, artist) from audio file metadata, falling back to filename."""
    try:
        mf = MutagenFile(filepath)
        if mf is not None and mf.tags:
            title = mf.tags.get("TIT2") or mf.tags.get("\xa9nam") or mf.tags.get("TITLE")
            artist = mf.tags.get("TPE1") or mf.tags.get("\xa9ART") or mf.tags.get("ARTIST")
            title = str(title.text[0]) if title and hasattr(title, "text") else None
            artist = str(artist.text[0]) if artist and hasattr(artist, "text") else None
            if title:
                return (title, artist or "")
    except Exception:
        pass
    name = Path(filepath).stem
    # Try "Artist - Title" pattern from filename
    if " - " in name:
        parts = name.split(" - ", 1)
        return (parts[1].strip(), parts[0].strip())
    return (name, "")


class MusicPlayer(QObject):
    REPEAT_ALL = 0
    REPEAT_SINGLE = 1
    SHUFFLE = 2

    position_changed = Signal(int)        # ms
    duration_changed = Signal(int)        # ms
    track_changed = Signal(str, str)      # title, artist
    track_visual_changed = Signal(str)    # filepath used to pick a visual theme
    playback_state_changed = Signal(bool) # True=playing
    repeat_mode_changed = Signal(int)     # REPEAT_ALL / REPEAT_SINGLE / SHUFFLE

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

        self._playlist: list[str] = []
        self._index: int = -1
        self._state: str = "stopped"  # 'playing' | 'paused' | 'stopped'
        self._position_accumulator: int = 0
        self._repeat_mode: int = self.REPEAT_ALL

        # Prevent premature end-of-track detection just after starting a track.
        # _poll_grace ticks (×100ms) skip get_busy() check.
        self._poll_grace = 0

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._poll)

    # ── Public API ──────────────────────────────────────────────────

    def open_file(self, filepath: str) -> None:
        """Load a single file and play it."""
        directory = str(Path(filepath).parent)
        self._build_playlist_from_file(filepath, directory)
        self._play_index(self._index)

    def toggle_playback(self) -> None:
        if self._state == "playing":
            self.pause()
        elif self._index >= 0:
            self.resume()

    def play(self) -> None:
        if self._state == "paused":
            self.resume()
        elif self._index >= 0:
            self._play_index(self._index)

    def pause(self) -> None:
        if self._state != "playing":
            return
        pygame.mixer.music.pause()
        self._position_accumulator += pygame.mixer.music.get_pos()
        self._state = "paused"
        self._timer.stop()
        self.playback_state_changed.emit(False)

    def resume(self) -> None:
        if self._state == "playing":
            return
        if self._state == "paused":
            pygame.mixer.music.unpause()
            self._state = "playing"
            self._timer.start()
            self.playback_state_changed.emit(True)
        elif self._index >= 0:
            self._play_index(self._index)

    def next(self) -> None:
        if not self._playlist:
            return
        idx = (self._index + 1) % len(self._playlist)
        self._play_index(idx)

    def prev(self) -> None:
        if not self._playlist:
            return
        idx = (self._index - 1) % len(self._playlist)
        self._play_index(idx)

    def set_volume(self, value: float) -> None:
        """value in 0.0 - 1.0"""
        pygame.mixer.music.set_volume(max(0.0, min(1.0, value)))

    def seek(self, position_ms: int) -> None:
        """Seek to position in milliseconds."""
        if self._state == "stopped":
            return
        try:
            pygame.mixer.music.rewind()
            pygame.mixer.music.set_pos(position_ms / 1000.0)
            self._position_accumulator = position_ms
        except Exception:
            pass  # set_pos not supported by all formats/codecs

    # ── Properties ───────────────────────────────────────────────────

    @property
    def is_playing(self) -> bool:
        return self._state == "playing"

    @property
    def playlist(self) -> list[str]:
        return list(self._playlist)

    @property
    def current_index(self) -> int:
        return self._index

    @property
    def current_file(self) -> str | None:
        if 0 <= self._index < len(self._playlist):
            return self._playlist[self._index]
        return None

    @property
    def repeat_mode(self) -> int:
        return self._repeat_mode

    def cycle_repeat_mode(self) -> int:
        """Cycle REPEAT_ALL → REPEAT_SINGLE → SHUFFLE → REPEAT_ALL.
        Returns the new mode."""
        self._repeat_mode = (self._repeat_mode + 1) % 3
        self.repeat_mode_changed.emit(self._repeat_mode)
        return self._repeat_mode

    def jump_to(self, index: int) -> None:
        """Jump to a specific track index in the playlist."""
        if 0 <= index < len(self._playlist):
            self._play_index(index)

    # ── Internals ────────────────────────────────────────────────────

    def _build_playlist_from_file(self, filepath: str, directory: str) -> None:
        """Build a playlist of sibling audio files in the same directory."""
        ext = Path(filepath).suffix.lower()
        self._playlist.clear()
        try:
            for entry in sorted(os.scandir(directory), key=lambda e: e.name.casefold()):
                if entry.is_file() and Path(entry.name).suffix.lower() in SUPPORTED_EXTS:
                    self._playlist.append(entry.path)
        except OSError:
            self._playlist.append(filepath)
        if filepath not in self._playlist:
            self._playlist.append(filepath)
        self._index = self._playlist.index(filepath)

    def _play_index(self, index: int) -> None:
        if index < 0 or index >= len(self._playlist):
            return
        self._index = index
        filepath = self._playlist[index]
        pygame.mixer.music.stop()
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        self._state = "playing"
        self._position_accumulator = 0
        self._poll_grace = 5  # 500ms grace before end-of-track detection
        self._timer.start()

        # Meta
        title, artist = _read_metadata(filepath)
        self.track_changed.emit(title, artist)
        self.track_visual_changed.emit(filepath)

        # Duration
        try:
            info = MutagenFile(filepath)
            if info and info.info and info.info.length:
                duration_ms = int(info.info.length * 1000)
                self.duration_changed.emit(duration_ms)
        except Exception:
            self.duration_changed.emit(0)

        self.playback_state_changed.emit(True)

    def _poll(self) -> None:
        """Timer tick: update position, detect end-of-track."""
        if self._state != "playing":
            return

        # Grace period after starting a new track — skip detection
        if self._poll_grace > 0:
            self._poll_grace -= 1
            return

        if pygame.mixer.music.get_busy():
            pos = self._position_accumulator + pygame.mixer.music.get_pos()
            self.position_changed.emit(pos)
        else:
            # Track ended naturally
            self._timer.stop()
            self._position_accumulator = 0
            self._state = "stopped"
            self.position_changed.emit(0)
            self.playback_state_changed.emit(False)
            self._on_track_ended()

    def _on_track_ended(self) -> None:
        """Called when the current track finishes. Respects repeat mode."""
        if not self._playlist:
            return
        if self._repeat_mode == self.REPEAT_SINGLE:
            self._play_index(self._index)
        elif self._repeat_mode == self.SHUFFLE:
            n = len(self._playlist)
            if n == 1:
                self._play_index(0)
            else:
                idx = random.randrange(n)
                self._play_index(idx)
        else:  # REPEAT_ALL
            next_idx = (self._index + 1) % len(self._playlist)
            self._play_index(next_idx)

    def cleanup(self) -> None:
        self._timer.stop()
        pygame.mixer.music.stop()
        pygame.mixer.quit()
