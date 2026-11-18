"""AI CLIPPING STUDIO: SubRip (.srt) Subtitle Exporter."""
import math
from typing import Any, Dict, List


def format_srt_time(seconds: float) -> str:
    """Format seconds into SRT timestamp HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000))
    milliseconds = ms % 1000
    total_seconds = ms // 1000
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    return f"{h:02d}:{m:02d}:{s:02d},{milliseconds:03d}"


def export_srt(words: List[Dict[str, Any]], clip_offset: float = 0.0, max_words_per_line: int = 5) -> str:
    """Generate standard SubRip (.srt) subtitle string from word timestamps."""
    from .compiler import chunk_words

    chunks = chunk_words(words, max_words_per_line=max_words_per_line)
    lines: List[str] = []

    for idx, chunk in enumerate(chunks, start=1):
        c_start = max(0.0, chunk[0]["start"] - clip_offset)
        c_end = max(c_start + 0.1, chunk[-1]["end"] - clip_offset)
        text = " ".join(w["word"] for w in chunk)

        lines.append(str(idx))
        lines.append(f"{format_srt_time(c_start)} --> {format_srt_time(c_end)}")
        lines.append(text)
        lines.append("")  # Blank separator line

    return "\n".join(lines)
