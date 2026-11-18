"""Multimodal Video Layout Solvers & Punch-In Directing.

Implements specialized framing layouts:
- Single Speaker 9:16 / 1:1 Dynamic Tracking
- Split Layout: Stacks two speakers vertically (1080x960 each) for dialogue/podcasts
- Camera Inset: Separates gameplay/screen recording top from webcam bottom
- Punch-In Zoom: Subtle 10-15% focal pushes during emphatic speech beats
Consolidated from OpenShorts, SupoClip, and Clips-Studio.
"""
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple


class LayoutType(str, Enum):
    SINGLE = "single_speaker"
    SPLIT = "split_screen"
    INSET = "camera_inset"
    TALKING_HEAD = "talking_head"


class LayoutCalculator:
    """Calculates crop windows and filtergraphs for various layout types."""

    @staticmethod
    def calculate_split_crop(source_w: int, source_h: int, target_w: int = 1080, target_h: int = 1920) -> Tuple[int, int]:
        half_h = target_h // 2
        crop_w = int(round(source_h * (target_w / half_h)))
        return min(crop_w, source_w), source_h


def plan_punch_in_beats(
    words: List[Dict[str, Any]],
    clip_duration: float,
    max_punches: int = 3,
    punch_scale: float = 1.15,
    punch_duration: float = 2.5
) -> List[Dict[str, Any]]:
    """Identify emphatic words and schedule subtle 10-15% zoom-in beats."""
    if clip_duration < 10.0 or not words:
        return []

    beats: List[Dict[str, Any]] = []
    emphatic_tokens = {"never", "always", "huge", "massive", "secret", "mistake", "critical", "insane", "amazing", "stop", "why", "shocking"}

    candidates = []
    for w in words:
        clean = w.get("word", "").lower().strip(".,!?\"'")
        if clean in emphatic_tokens:
            candidates.append(float(w["start"]))

    last_punch_end = -10.0
    for t in candidates:
        if t >= 2.0 and t + punch_duration <= clip_duration - 2.0:
            if t > last_punch_end + 4.0:
                beats.append({
                    "time": round(t, 2),
                    "scale": punch_scale,
                    "duration": punch_duration
                })
                last_punch_end = t + punch_duration
                if len(beats) >= max_punches:
                    break

    return beats


def build_split_filtergraph(
    source_width: int,
    source_height: int,
    speaker_a_x: int,
    speaker_b_x: int,
    out_width: int = 1080,
    out_height: int = 1920,
    crop_width: Optional[int] = None,
    input_label: str = "0:v",
    output_label: str = "v_stacked"
) -> str:
    """Construct an FFmpeg filtergraph stacking two cropped speakers into 9:16 vertical without neighbor bleed."""
    half_h = out_height // 2  # 960
    # Use tightly isolated crop width (<= 46% of width) if not provided
    crop_w = crop_width if crop_width else min(int(round(source_width * 0.46)), int(round(source_height * (out_width / half_h))))
    crop_w = min(crop_w, source_width)

    x_a = max(0, min(source_width - crop_w, speaker_a_x))
    x_b = max(0, min(source_width - crop_w, speaker_b_x))

    filtergraph = (
        f"[{input_label}]split=2[in_a][in_b];"
        f"[in_a]crop={crop_w}:{source_height}:{x_a}:0,scale={out_width}:{half_h}[top];"
        f"[in_b]crop={crop_w}:{source_height}:{x_b}:0,scale={out_width}:{half_h}[bottom];"
        f"[top][bottom]vstack=inputs=2[{output_label}]"
    )
    return filtergraph


def detect_podcast_speakers(
    video_path: str,
    start_time: float,
    duration: float,
    source_w: int,
    source_h: int
) -> Tuple[bool, int, int, int, str]:
    """Analyze video frames to classify layout: Single Speaker (Full 9:16) vs Wide 2-Speaker (Stacked 9:16).
    
    Prevents:
    1. Duplicating single-camera close-ups on top and bottom (switches to Full Screen 9:16).
    2. Side neighbor bleeding in wide shots by enforcing strict mid-point isolation bounds.
    """
    try:
        import cv2
        from .tracker import FaceTracker

        tracker = FaceTracker()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            w_iso = min(source_w, int(round(source_h * 0.75)))
            return False, 0, max(0, source_w - w_iso), w_iso, "single_speaker"

        left_xs: List[float] = []
        right_xs: List[float] = []
        all_centroids: List[float] = []
        dual_face_frame_count = 0

        # Sample 10 frames evenly across the segment
        sample_count = 10
        step = max(0.4, duration / max(1, sample_count))
        mid_x = source_w * 0.50

        for i in range(sample_count):
            t = start_time + (i * step)
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
            ret, frame = cap.read()
            if not ret:
                continue

            faces = tracker.detect_faces(frame)
            # Filter valid speaker faces (w >= 70 ignores background picture frames and figurines)
            valid_faces = [f for f in faces if f.w >= 70 and f.score >= 0.70]

            # Count simultaneous faces in this exact frame
            l_in_frame = [f for f in valid_faces if f.centroid_x < mid_x - 30]
            r_in_frame = [f for f in valid_faces if f.centroid_x > mid_x + 30]

            if l_in_frame and r_in_frame:
                dual_face_frame_count += 1
                for f in l_in_frame:
                    left_xs.append(f.centroid_x)
                for f in r_in_frame:
                    right_xs.append(f.centroid_x)

            for f in valid_faces:
                all_centroids.append(f.centroid_x)

        cap.release()

        # Strict isolation crop width: strictly <= 46% of source width so left & right NEVER overlap
        w_isolated = min(int(round(source_w * 0.46)), int(round(source_h * 0.85)))

        # CASE A: Majority (>= 45%) of frames have 2 SIMULTANEOUS faces -> True 2-person wide angle conversation!
        if dual_face_frame_count >= max(2, int(sample_count * 0.45)) and len(left_xs) >= 2 and len(right_xs) >= 2:
            avg_left = sum(left_xs) / len(left_xs)
            avg_right = sum(right_xs) / len(right_xs)

            # Left speaker crop: strictly bounded to left half (stops at or before mid_x)
            x_a = max(0, min(int(mid_x - w_isolated), int(round(avg_left - (w_isolated / 2.0)))))

            # Right speaker crop: strictly bounded to right half (starts at or after mid_x)
            x_b = max(int(mid_x), min(source_w - w_isolated, int(round(avg_right - (w_isolated / 2.0)))))

            return True, x_a, x_b, w_isolated, "split"

        # CASE B: Single-speaker camera close-up (only 1 person visible in shot)
        # -> Render in FULL SCREEN 9:16 (Centered on that speaker, never duplicate top & bottom!)
        full_w = int(round(source_h * 9.0 / 16.0))
        avg_c = sum(all_centroids) / len(all_centroids) if all_centroids else mid_x
        single_x = max(0, min(source_w - full_w, int(round(avg_c - (full_w / 2.0)))))

        return False, single_x, single_x, full_w, "single_speaker"

    except Exception:
        full_w = int(round(source_h * 9.0 / 16.0))
        return False, 0, 0, full_w, "single_speaker"


def build_camera_inset_filtergraph(
    source_width: int,
    source_height: int,
    inset_rect: Tuple[int, int, int, int],  # x, y, w, h
    out_width: int = 1080,
    out_height: int = 1920
) -> str:
    """Separate screen recording / gameplay (top) from creator webcam (bottom)."""
    ix, iy, iw, ih = inset_rect
    screen_h = int(out_height * 0.6)  # 60% screen
    face_h = out_height - screen_h    # 40% facecam

    filtergraph = (
        f"[0:v]split=2[v_scr][v_cam];"
        f"[v_scr]scale={out_width}:{screen_h}:force_original_aspect_ratio=decrease,pad={out_width}:{screen_h}:(ow-iw)/2:(oh-ih)/2:black[top];"
        f"[v_cam]crop={iw}:{ih}:{ix}:{iy},scale={out_width}:{face_h}:force_original_aspect_ratio=increase,crop={out_width}:{face_h}[bottom];"
        f"[top][bottom]vstack=inputs=2[v_stacked]"
    )
    return filtergraph
