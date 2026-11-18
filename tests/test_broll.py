"""Unit tests for B-Roll cutaways and overlay filtergraph generation."""
from pathlib import Path
import pytest
from broll.overlay import (
    normalize_broll_overlays,
    broll_input_args,
    broll_overlay_graph,
    BrollOverlay
)


def test_broll_normalization_and_timing(tmp_path):
    test_media = tmp_path / "stock_01.mp4"
    test_media.write_bytes(b"dummy")

    overlays = [
        {"path": str(test_media), "start": 5.0, "duration": 4.0, "fade_in": True, "fade_out": True},
        {"path": str(test_media), "start": 6.0, "duration": 3.0},  # Overlapping: should be discarded
        {"path": str(tmp_path / "non_existent.mp4"), "start": 15.0, "duration": 3.0},  # Missing file
        {"path": str(test_media), "start": 12.0, "duration": 3.0, "fade_in": False}
    ]

    cleaned = normalize_broll_overlays(overlays, clip_duration=20.0)
    assert len(cleaned) == 2
    assert cleaned[0]["start"] == 5.0
    assert cleaned[0]["duration"] == 4.0
    assert cleaned[1]["start"] == 12.0


def test_broll_filter_graph_generation(tmp_path):
    test_media = tmp_path / "cutaway.mp4"
    test_media.write_bytes(b"dummy")

    overlays = [
        {"path": str(test_media), "start": 2.0, "duration": 3.0, "offset": 0.0, "fade_in": True, "fade_out": True}
    ]

    args = broll_input_args(overlays)
    assert "-i" in args
    assert str(test_media) in args

    graph, out_label = broll_overlay_graph("[base_v]", overlays, width=1080, height=1920, first_input=1)
    assert "scale=1080:1920" in graph
    assert "overlay=0:0" in graph
    assert out_label == "[withbroll0]"
