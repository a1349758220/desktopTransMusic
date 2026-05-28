# Vinyl Record Mini Bar Design

## Summary

Add a compact vinyl-record visual to the far left of the existing 400 x 50 mini player bar. This change targets the current 400 x 50 theme only. A future 200 x 80 theme can use a larger variant, but that is outside this scope.

## Goals

- Keep the mini player window size at 400 x 50.
- Add a small record player effect at the far left.
- Show the current track cover in the record center when embedded cover art exists.
- Fall back to a pure record graphic when the current track has no cover art.
- Rotate the record only while music is playing.
- Move the tonearm onto the record only while music is playing.
- Move the tonearm outside the record when paused, stopped, or no track is loaded.

## Non-Goals

- Do not implement the future 200 x 80 theme.
- Do not redesign the whole mini player layout.
- Do not add external image assets for the record or tonearm.
- Do not change audio playback behavior.

## Existing Context

The app is a PySide6 mini player. The main bar lives in `desktopTransMusic/mini_player/ui/mini_bar.py` and currently has a fixed 400 x 50 frameless window. Playback state and metadata come from `desktopTransMusic/mini_player/core/player.py`, which already uses `mutagen` for title, artist, and duration.

The reference music folder is `C:\Users\Suen ZtaYrua\Desktop\music`. It contains tracks with embedded cover art and one observed track without cover art:

- Cover examples: `一万个舍不得 - 庄心妍&祁隆.mp3`, `天空之上（电影《玛纳斯人之失落的秘境》主题曲）.mp3`, `泡沫-邓紫棋.mp3`, `红山果 安与骑兵.mp3`
- No-cover example: `追梦赤子心-GALA.mp3`

## Proposed UI

Create a compact `VinylRecordWidget` placed as the first child in the `MiniBar` horizontal layout.

Approximate dimensions:

- Widget size: 42 x 44 px.
- Record diameter: 38 px.
- Cover circle: about 20 px diameter.
- Tonearm: code-drawn white arm and cartridge, scaled for the 50 px bar.

The rest of the controls remain in the existing order:

1. Vinyl record widget
2. Previous button
3. Play / pause button
4. Next button
5. Track indicator
6. Progress slider
7. Time label

The existing 400 px width remains unchanged, so the progress slider will give up a small amount of horizontal space.

## State Behavior

### No Track Loaded

- Record is visible as a default vinyl graphic.
- No cover art is shown.
- Tonearm rests outside the record.
- Rotation timer is stopped.

### Playing

- Record rotates continuously.
- Tonearm rests over the record.
- If embedded cover art exists, it appears clipped to a circular center label.
- If no embedded cover art exists, the record center remains part of the default vinyl graphic.

### Paused Or Stopped

- Record stops rotating at its current angle.
- Tonearm moves outside the record.
- Current cover art remains visible if a track is loaded and has cover art.

## Cover Art Extraction

Add cover extraction in `core/player.py` using the existing `mutagen` dependency.

Supported cases:

- MP3 ID3 `APIC` frames.
- MP4/M4A `covr` tags.
- FLAC/Vorbis pictures when available through mutagen metadata.

Expose cover changes through a new signal, for example:

```python
cover_changed = Signal(object)  # bytes | None
```

When a track starts, emit the cover bytes if available, otherwise emit `None`. UI code converts bytes into a `QPixmap`.

## Animation

`VinylRecordWidget` owns a lightweight `QTimer` for animation.

- Timer interval: about 40 ms.
- Each tick increments the record angle and calls `update()`.
- `set_playing(True)` starts the timer.
- `set_playing(False)` stops the timer and repaints the tonearm outside the record.

The record graphic and cover art rotate together. The tonearm does not rotate; it changes between two fixed poses.

## Rendering

Use `QPainter` to draw the component.

Record layers:

- Outer black disc.
- Subtle radial grooves.
- Inner circular cover area when cover art exists.
- Small center hole.

Tonearm layers:

- Pivot circle.
- White arm line.
- Cartridge/head shape.

All drawing uses anti-aliasing and transparent backgrounds so it blends with the existing acrylic-style mini bar.

## Tests

Add focused tests where practical:

- Cover extraction returns bytes for a known cover-art file.
- Cover extraction returns `None` for the no-cover reference file.
- `VinylRecordWidget.set_playing(True)` starts its animation timer.
- `VinylRecordWidget.set_playing(False)` stops its animation timer.
- `VinylRecordWidget.set_cover_bytes(None)` clears cover state without raising.

If a full Qt test harness is not already present, keep UI tests minimal and prefer isolated helper tests for metadata extraction.

## Acceptance Criteria

- The mini player window remains 400 x 50.
- The record widget appears at the far left.
- Playing music rotates the record and moves the tonearm onto it.
- Pausing or stopping music stops rotation and moves the tonearm outside the record.
- Tracks with embedded cover art show a circular cover in the record center.
- Tracks without embedded cover art show only the default record graphic.
- Existing controls still work and remain visible.
