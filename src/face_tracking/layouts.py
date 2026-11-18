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
    out_height: int = 1920
) -> str:
    """Construct an FFmpeg filtergraph stacking two cropped speakers into 9:16 vertical."""
    half_h = out_height // 2  # 960
    crop_w = int(round(source_height * (out_width / half_h)))  # 1215 for 1080p
    crop_w = min(crop_w, source_width)

    filtergraph = (
        f"[0:v]split=2[in_a][in_b];"
        f"[in_a]crop={crop_w}:{source_height}:{speaker_a_x}:0,scale={out_width}:{half_h}[top];"
        f"[in_b]crop={crop_w}:{source_height}:{speaker_b_x}:0,scale={out_width}:{half_h}[bottom];"
        f"[top][bottom]vstack=inputs=2[v_stacked]"
    )
    return filtergraph


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
