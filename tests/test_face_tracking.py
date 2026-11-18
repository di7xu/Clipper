"""Automated tests for Face Tracking, Smooth Camera and Layout Solvers."""
import numpy as np
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from face_tracking.tracker import FaceTracker, FaceBox, SmoothedCamera
from face_tracking.layouts import plan_punch_in_beats, build_split_filtergraph, build_camera_inset_filtergraph


def test_smoothed_camera():
    cam = SmoothedCamera(smoothing_factor=0.2)
    # First update sets initial position directly
    x1, y1 = cam.update(100.0, 200.0)
    assert x1 == 100.0
    assert y1 == 200.0

    # Second update moves smoothly toward target
    x2, y2 = cam.update(200.0, 300.0)
    assert 100.0 < x2 < 200.0
    assert 200.0 < y2 < 300.0
    assert round(x2, 1) == 120.0  # 100 + (200 - 100) * 0.2


def test_crop_window_aspect_ratios():
    tracker = FaceTracker()
    frame_w, frame_h = 1920, 1080

    # 1. 9:16 Vertical Crop
    cx, cy, cw, ch = tracker.compute_crop_window(frame_w, frame_h, face=None, target_aspect="9:16")
    assert ch == 1080
    assert cw == int(round(1080 * 9.0 / 16.0))  # 608
    assert cx == (1920 - cw) // 2
    assert cy == 0

    # 2. 1:1 Square Crop
    cx_sq, cy_sq, cw_sq, ch_sq = tracker.compute_crop_window(frame_w, frame_h, face=None, target_aspect="1:1")
    assert ch_sq == 1080
    assert cw_sq == 1080
    assert cx_sq == (1920 - 1080) // 2

    # 3. Off-center Face Tracking
    tracker.camera.reset()
    fake_face = FaceBox(x=300, y=200, w=150, h=150, score=0.95, centroid_x=375, centroid_y=275)
    cx_face, _, _, _ = tracker.compute_crop_window(frame_w, frame_h, face=fake_face, target_aspect="9:16")
    assert cx_face < cx  # Crop shifted left to follow face centroid


def test_plan_punch_in_beats():
    words = [
        {"word": "Welcome", "start": 1.0, "end": 1.5},
        {"word": "This", "start": 2.0, "end": 2.4},
        {"word": "is", "start": 2.5, "end": 2.7},
        {"word": "a", "start": 2.8, "end": 2.9},
        {"word": "massive", "start": 4.0, "end": 4.5},
        {"word": "mistake", "start": 4.6, "end": 5.1},
        {"word": "in", "start": 5.2, "end": 5.4},
        {"word": "software", "start": 5.5, "end": 6.0},
        {"word": "never", "start": 12.0, "end": 12.5},
        {"word": "do", "start": 12.6, "end": 12.9},
        {"word": "this", "start": 13.0, "end": 13.5}
    ]

    punches = plan_punch_in_beats(words, clip_duration=20.0, max_punches=2, punch_scale=1.15)
    assert len(punches) == 2
    assert punches[0]["time"] == 4.0
    assert punches[0]["scale"] == 1.15
    assert punches[1]["time"] == 12.0


def test_split_and_inset_filtergraphs():
    split_fg = build_split_filtergraph(1920, 1080, speaker_a_x=100, speaker_b_x=800)
    assert "split=2" in split_fg
    assert "vstack=inputs=2" in split_fg
    assert "scale=1080:960" in split_fg

    inset_fg = build_camera_inset_filtergraph(1920, 1080, inset_rect=(1400, 700, 480, 360))
    assert "split=2" in inset_fg
    assert "vstack=inputs=2" in inset_fg
    assert "crop=480:360:1400:700" in inset_fg
