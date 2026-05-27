def format_time(ms: int) -> str:
    """Convert milliseconds to 'm:ss' (0:00)."""
    if ms < 0:
        ms = 0
    total_sec = ms // 1000
    minutes = total_sec // 60
    seconds = total_sec % 60
    return f"{minutes}:{seconds:02d}"


AUDIO_EXTENSIONS = (
    "*.mp3 *.flac *.wav *.ogg *.aac *.m4a *.wma *.opus *.mid *.midi"
)


def audio_name_filter() -> str:
    """Return a file-dialog filter string for audio files."""
    return (
        "Audio Files (*.mp3 *.flac *.wav *.ogg *.aac *.m4a *.wma *.opus "
        "*.mid *.midi);;All Files (*)"
    )
