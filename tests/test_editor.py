"""Automated tests for AI Tightening, Filler Word Pruning and Edit Plan."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from editor.tighten import plan_cuts, clean_token
from editor.edit_plan import create_edit_plan


def test_clean_token():
    assert clean_token("Um...") == "um"
    assert clean_token("uh!") == "uh"
    assert clean_token("Hello,") == "hello"


def test_tighten_filler_words():
    words = [
        {"word": "So", "start": 0.0, "end": 0.3},
        {"word": "um", "start": 0.4, "end": 0.8},        # Filler: um
        {"word": "the", "start": 0.9, "end": 1.1},
        {"word": "you", "start": 1.2, "end": 1.4},
        {"word": "know", "start": 1.5, "end": 1.7},     # Filler: you know
        {"word": "solution", "start": 1.8, "end": 2.3},
        {"word": "is", "start": 2.4, "end": 2.6},
        {"word": "here", "start": 2.7, "end": 3.0}
    ]

    res = plan_cuts(words, clip_start=0.0, clip_end=3.0, fillers=True, silence=False)

    retimed = res["retimedWords"]
    retimed_tokens = [w["word"].lower() for w in retimed]

    assert "um" not in retimed_tokens
    assert "you" not in retimed_tokens
    assert "know" not in retimed_tokens
    assert "solution" in retimed_tokens

    # Verify monotonic time ordering
    for i in range(len(retimed) - 1):
        assert retimed[i]["start"] < retimed[i]["end"]
        assert retimed[i]["end"] <= retimed[i + 1]["start"] + 0.001


def test_tighten_silence_removal():
    words = [
        {"word": "Hello", "start": 0.5, "end": 1.0},
        # 2.0 second awkward silence gap
        {"word": "World", "start": 3.0, "end": 3.5}
    ]

    res = plan_cuts(words, clip_start=0.0, clip_end=4.0, gap=0.6, fillers=False, silence=True)

    assert res["savedDuration"] > 1.0
    assert res["newDuration"] < 4.0
    assert len(res["keepRanges"]) >= 2


def test_create_edit_plan(tmp_path):
    clip = {
        "id": "clip_42",
        "start": 10.0,
        "end": 25.0,
        "words": [
            {"word": "Great", "start": 10.5, "end": 11.0},
            {"word": "video", "start": 11.2, "end": 12.0}
        ]
    }

    plan = create_edit_plan(
        clip=clip,
        project_id="proj_01",
        source_path="c:/test/source.mp4",
        output_dir=str(tmp_path),
        aspect_ratio="9:16",
        caption_style="viral_yellow"
    )

    p_dict = plan.to_dict()
    assert p_dict["clipId"] == "clip_42"
    assert p_dict["aspectRatio"] == "9:16"
    assert p_dict["targetWidth"] == 1080
    assert p_dict["targetHeight"] == 1920
    assert "proj_01_clip_42_9_16.mp4" in p_dict["outputPath"]
    assert len(p_dict["keepRanges"]) > 0
    assert len(p_dict["words"]) == 2
