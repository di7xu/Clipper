"""Declarative Edit Plan Builder & Serializer.

Defines the universal editing plan consumed by the native FFmpeg rendering pipeline:
segment timing, speech tightening, camera reframing, B-roll overlays, and karaoke subtitles.
Consolidated from Chopify, OpenShorts, and SupoClip.
"""
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import config
from captions.styles import CaptionStyleConfig, PRESET_STYLES
from editor.tighten import plan_cuts
from face_tracking.layouts import plan_punch_in_beats


@dataclass
class EditPlan:
    clip_id: str
    project_id: str
    source_path: str
    output_path: str
    clip_start: float
    clip_end: float
    aspect_ratio: str = "9:16"
    target_width: int = 1080
    target_height: int = 1920
    layout: str = "single_speaker"
    layout_config: Dict[str, Any] = field(default_factory=dict)
    caption_style: str = "viral_yellow"
    tighten: bool = True
    keep_ranges: List[Tuple[float, float]] = field(default_factory=list)
    words: List[Dict[str, Any]] = field(default_factory=list)
    punch_ins: List[Dict[str, Any]] = field(default_factory=list)
    broll_overlays: List[Dict[str, Any]] = field(default_factory=list)
    watermark_path: Optional[str] = None
    watermark_position: str = "top_center"
    audio_norm: bool = True
    encoder: str = "auto"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clipId": self.clip_id,
            "projectId": self.project_id,
            "sourcePath": self.source_path,
            "outputPath": self.output_path,
            "clipStart": self.clip_start,
            "clipEnd": self.clip_end,
            "aspectRatio": self.aspect_ratio,
            "targetWidth": self.target_width,
            "targetHeight": self.target_height,
            "layout": self.layout,
            "layoutConfig": self.layout_config,
            "captionStyle": self.caption_style,
            "tighten": self.tighten,
            "keepRanges": self.keep_ranges,
            "words": self.words,
            "punchIns": self.punch_ins,
            "brollOverlays": self.broll_overlays,
            "watermarkPath": self.watermark_path,
            "watermarkPosition": self.watermark_position,
            "audioNorm": self.audio_norm,
            "encoder": self.encoder
        }


def create_edit_plan(
    clip: Dict[str, Any],
    project_id: str,
    source_path: str,
    output_dir: str,
    aspect_ratio: str = "9:16",
    caption_style: str = "viral_yellow",
    tighten: bool = True,
    layout: str = "single_speaker",
    layout_config: Optional[Dict[str, Any]] = None,
    audio_norm: bool = True,
    broll_overlays: Optional[List[Dict[str, Any]]] = None,
    watermark_path: Optional[str] = None,
    watermark_position: str = "top_center"
) -> EditPlan:
    """Construct and configure an optimized Edit Plan for a candidate clip."""
    clip_id = clip.get("id", "clip_01")
    c_start = float(clip["start"])
    c_end = float(clip["end"])
    words = clip.get("words", [])

    # Resolve output dimensions
    if aspect_ratio == "9:16":
        w, h = 1080, 1920
    elif aspect_ratio == "1:1":
        w, h = 1080, 1080
    else:  # 16:9
        w, h = 1920, 1080

    output_path = str(Path(output_dir) / f"{project_id}_{clip_id}_{aspect_ratio.replace(':', '_')}.mp4")

    # Tighten cuts if enabled
    if tighten and words:
        tighten_res = plan_cuts(words, c_start, c_end, gap=0.6, fillers=True, silence=True)
        keep_ranges = tighten_res["keepRanges"]
        active_words = tighten_res["retimedWords"]
        final_duration = tighten_res["newDuration"]
    else:
        keep_ranges = [(0.0, round(c_end - c_start, 3))]
        active_words = [
            {"word": w["word"], "start": round(float(w["start"]) - c_start, 3), "end": round(float(w["end"]) - c_start, 3)}
            for w in words
        ]
        final_duration = round(c_end - c_start, 3)

    # Schedule punch-in zoom beats
    punch_ins = plan_punch_in_beats(active_words, clip_duration=final_duration, max_punches=3)

    # Detect encoder
    preferred_encoder = config.hardware.preferred_encoder

    return EditPlan(
        clip_id=clip_id,
        project_id=project_id,
        source_path=str(Path(source_path).resolve()),
        output_path=output_path,
        clip_start=c_start,
        clip_end=c_end,
        aspect_ratio=aspect_ratio,
        target_width=w,
        target_height=h,
        layout=layout,
        layout_config=layout_config or {},
        caption_style=caption_style,
        tighten=tighten,
        keep_ranges=keep_ranges,
        words=active_words,
        punch_ins=punch_ins,
        broll_overlays=broll_overlays or [],
        watermark_path=watermark_path,
        watermark_position=watermark_position,
        audio_norm=audio_norm,
        encoder=preferred_encoder
    )
