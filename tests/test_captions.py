"""Automated tests for Smart Captions, ASS and SRT Compilers."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from captions.compiler import format_ass_time, chunk_words, compile_ass_subtitles
from captions.srt import format_srt_time, export_srt
from captions.styles import PRESET_STYLES, hex_to_ass_color


def test_time_formatters():
    # 0.0s
    assert format_ass_time(0.0) == "0:00:00.00"
    assert format_srt_time(0.0) == "00:00:00,000"

    # 65.43s -> 1 min, 5 sec, 43 cs / 430 ms
    assert format_ass_time(65.43) == "0:01:05.43"
    assert format_srt_time(65.43) == "00:01:05,430"

    # 3661.12s -> 1 hr, 1 min, 1 sec, 12 cs
    assert format_ass_time(3661.12) == "1:01:01.12"
    assert format_srt_time(3661.12) == "01:01:01,120"


def test_chunk_words():
    words = [
        {"word": "One", "start": 0.0, "end": 0.3},
        {"word": "Two", "start": 0.4, "end": 0.7},
        {"word": "Three", "start": 0.8, "end": 1.1},
        {"word": "Four", "start": 1.2, "end": 1.5},
        {"word": "Five", "start": 1.6, "end": 1.9},
        {"word": "Six", "start": 3.0, "end": 3.3}  # Gap > 0.5s -> pause break
    ]

    chunks = chunk_words(words, max_words_per_line=3)
    assert len(chunks) == 3
    assert len(chunks[0]) == 3  # One, Two, Three
    assert len(chunks[1]) == 2  # Four, Five
    assert len(chunks[2]) == 1  # Six (separated by gap)


def test_compile_ass_subtitles():
    words = [
        {"word": "Hello", "start": 1.0, "end": 1.4},
        {"word": "World", "start": 1.5, "end": 2.0}
    ]

    ass_script = compile_ass_subtitles(words, style=PRESET_STYLES["viral_yellow"], clip_offset=1.0)

    assert "[Script Info]" in ass_script
    assert "[V4+ Styles]" in ass_script
    assert "[Events]" in ass_script
    assert "Style: Default,Anton" in ass_script
    assert "Dialogue:" in ass_script
    # Check word highlight tag is present
    assert "\\c&H0000E6FF&" in ass_script
    assert "HELLO" in ass_script  # Uppercase viral style


def test_export_srt():
    words = [
        {"word": "Build", "start": 10.0, "end": 10.4},
        {"word": "great", "start": 10.5, "end": 10.8},
        {"word": "tools", "start": 10.9, "end": 11.5}
    ]

    srt_text = export_srt(words, clip_offset=10.0)
    lines = srt_text.strip().splitlines()

    assert lines[0] == "1"
    assert lines[1] == "00:00:00,000 --> 00:00:01,500"
    assert lines[2] == "Build great tools"


def test_hex_to_ass_color():
    # #FFCC00 (R=FF, G=CC, B=00) -> &H0000CCFF
    assert hex_to_ass_color("#FFCC00") == "&H0000CCFF"
    # #FFFFFF -> &H00FFFFFF
    assert hex_to_ass_color("#FFFFFF") == "&H00FFFFFF"
