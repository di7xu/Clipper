"""AI CLIPPING STUDIO: Advanced SubStation Alpha (.ass) Subtitle Compiler.

Compiles millisecond word timestamps into word-by-word animated CapCut-style
karaoke subtitles for burning into MP4 videos via the FFmpeg subtitles filter.
"""
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from .styles import CaptionStyleConfig, PRESET_STYLES


def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp H:MM:SS.cs (centiseconds)."""
    if seconds < 0:
        seconds = 0.0
    centiseconds = int(round(seconds * 100))
    cs = centiseconds % 100
    total_seconds = centiseconds // 100
    s = total_seconds % 60
    total_minutes = total_seconds // 60
    m = total_minutes % 60
    h = total_minutes // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def chunk_words(words: List[Dict[str, Any]], max_words_per_line: int = 4, max_gap: float = 0.5) -> List[List[Dict[str, Any]]]:
    """Group sequential words into readable mobile-screen line chunks."""
    if not words:
        return []

    chunks: List[List[Dict[str, Any]]] = []
    current_chunk: List[Dict[str, Any]] = []

    for idx, w in enumerate(words):
        if not current_chunk:
            current_chunk.append(w)
            continue

        prev_end = current_chunk[-1]["end"]
        curr_start = w["start"]

        # Split on natural speech pause (> 0.5s) or reaching line word limit
        if len(current_chunk) >= max_words_per_line or (curr_start - prev_end) > max_gap:
            chunks.append(current_chunk)
            current_chunk = [w]
        else:
            current_chunk.append(w)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def compile_ass_subtitles(
    words: List[Dict[str, Any]],
    style: Optional[CaptionStyleConfig] = None,
    clip_offset: float = 0.0,
    video_width: int = 1080,
    video_height: int = 1920
) -> str:
    """Compile words into a complete, standalone .ass subtitle script."""
    cfg = style or PRESET_STYLES["viral_yellow"]

    # Scale font size and margin relative to video dimensions
    scale_factor = video_height / 1920.0
    scaled_font_size = int(round(cfg.font_size * scale_factor))
    scaled_margin_v = int(round(cfg.margin_v * scale_factor))
    scaled_outline = round(cfg.outline_width * scale_factor, 1)
    scaled_shadow = round(cfg.shadow_distance * scale_factor, 1)

    header = f"""[Script Info]
Title: AI Clipping Studio Generated Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {video_width}
PlayResY: {video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{cfg.font_family},{scaled_font_size},{cfg.primary_color},{cfg.highlight_color},{cfg.outline_color},{cfg.shadow_color},{cfg.bold},0,0,0,100,100,0,0,1,{scaled_outline},{scaled_shadow},{cfg.alignment},40,40,{scaled_margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogue_lines: List[str] = []
    chunks = chunk_words(words)

    for chunk in chunks:
        if not chunk:
            continue

        chunk_start = max(0.0, chunk[0]["start"] - clip_offset)
        chunk_end = max(chunk_start + 0.1, chunk[-1]["end"] - clip_offset)

        if not cfg.karaoke_effect:
            # Simple line without karaoke word highlight
            line_text = " ".join(w["word"] for w in chunk)
            if cfg.uppercase:
                line_text = line_text.upper()
            start_str = format_ass_time(chunk_start)
            end_str = format_ass_time(chunk_end)
            dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")
        else:
            # Word-by-word animated CapCut highlight
            # Emit a sub-dialogue event for each word's active window
            for active_idx, active_word in enumerate(chunk):
                w_start = max(chunk_start, active_word["start"] - clip_offset)
                w_end = min(chunk_end, active_word["end"] - clip_offset)
                if w_end <= w_start:
                    w_end = w_start + 0.1

                formatted_tokens = []
                for idx, token in enumerate(chunk):
                    text = token["word"].upper() if cfg.uppercase else token["word"]
                    if idx == active_idx:
                        # Active speaking word receives highlight color and subtle emphasis
                        formatted_tokens.append(f"{{\\c{cfg.highlight_color}&}}{text}{{\\c{cfg.primary_color}&}}")
                    else:
                        formatted_tokens.append(text)

                event_text = " ".join(formatted_tokens)
                start_str = format_ass_time(w_start)
                end_str = format_ass_time(w_end)
                dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{event_text}")

    return header + "\n".join(dialogue_lines) + "\n"
