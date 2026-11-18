"""Composite stock B-roll cutaways and media overlays into video renders.

Consolidated and adapted from SupoClip's broll_overlay engine:
- B-roll is overlaid on the reframed canvas inside the FFmpeg filter graph.
- Captions and hook titles stay on screen over the B-roll.
- Each cutaway smoothly dissolves in and out over the footage instead of dipping to black.
- Scales and crops B-roll media to match target vertical/square dimensions.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

BROLL_FADE_SECONDS = 0.25
MIN_BROLL_SECONDS = 0.5


@dataclass
class BrollOverlay:
    path: Path
    start: float
    duration: float
    offset: float = 0.0
    fade_in: bool = True
    fade_out: bool = True
    fade_duration: float = BROLL_FADE_SECONDS


def normalize_broll_overlays(
    overlays: Optional[Iterable[Dict[str, Any]]],
    clip_duration: Optional[float] = None,
    min_duration: float = MIN_BROLL_SECONDS,
) -> List[Dict[str, Any]]:
    """Validate and sort non-overlapping overlays in chronological order."""
    cleaned: List[Dict[str, Any]] = []
    for overlay in overlays or []:
        try:
            path = Path(overlay["path"])
            start = max(0.0, float(overlay["start"]))
            duration = float(overlay["duration"])
        except (KeyError, TypeError, ValueError):
            continue

        if not path.is_file():
            continue

        try:
            offset = max(0.0, float(overlay.get("offset") or 0.0))
        except (TypeError, ValueError):
            offset = 0.0

        if clip_duration is not None:
            duration = min(duration, max(0.0, clip_duration - start))

        fade_in = overlay.get("fade_in", True) is not False
        fade_out = overlay.get("fade_out", True) is not False

        if duration < min_duration:
            continue

        fade_duration = min(BROLL_FADE_SECONDS, duration / 3.0)
        try:
            fade_duration = min(BROLL_FADE_SECONDS, max(0.01, float(overlay.get("fade_duration") or fade_duration)))
        except (TypeError, ValueError):
            pass

        cleaned.append({
            "path": path,
            "start": round(start, 3),
            "duration": round(duration, 3),
            "offset": round(offset, 3),
            "fade_in": fade_in,
            "fade_out": fade_out,
            "fade_duration": round(fade_duration, 3),
        })

    cleaned.sort(key=lambda x: x["start"])
    result: List[Dict[str, Any]] = []
    for overlay in cleaned:
        if result:
            prev = result[-1]
            if overlay["start"] < prev["start"] + prev["duration"] - 0.01:
                # Skip overlapping entries
                continue
        result.append(overlay)
    return result


def broll_input_args(overlays: List[Dict[str, Any]]) -> List[str]:
    """Generate FFmpeg input CLI arguments for B-roll media files."""
    args: List[str] = []
    for overlay in overlays:
        read_len = overlay.get("offset", 0.0) + overlay["duration"] + 0.5
        args += ["-t", f"{read_len:.3f}", "-i", str(overlay["path"])]
    return args


def broll_overlay_graph(
    base_label: str,
    overlays: List[Dict[str, Any]],
    width: int,
    height: int,
    first_input: int = 1,
) -> Tuple[str, str]:
    """Construct FFmpeg filter graph fragment that overlays each cutaway onto base_label."""
    if not overlays:
        return "", base_label

    parts: List[str] = []
    current = base_label

    for index, overlay in enumerate(overlays):
        start = overlay["start"]
        duration = overlay["duration"]
        end = start + duration
        fade = overlay.get("fade_duration", min(BROLL_FADE_SECONDS, duration / 3.0))
        clip_label = f"[broll{index}]"
        out_label = f"[withbroll{index}]"

        fades = ""
        if overlay.get("fade_in", True):
            fades += f",fade=t=in:st={start:.3f}:d={fade:.3f}:alpha=1"
        if overlay.get("fade_out", True):
            fades += f",fade=t=out:st={end - fade:.3f}:d={fade:.3f}:alpha=1"

        parts.append(
            f"[{first_input + index}:v]settb=AVTB,"
            f"trim=start={overlay.get('offset', 0.0):.3f}:duration={duration + 0.1:.3f},"
            f"setpts=PTS-STARTPTS+{start:.3f}/TB,"
            f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={width}:{height},setsar=1,format=yuva420p{fades}{clip_label}"
        )
        parts.append(
            f"{current}{clip_label}overlay=0:0:eof_action=repeat:"
            f"enable='between(t,{start:.3f},{end:.3f})'{out_label}"
        )
        current = out_label

    return ";".join(parts), current
