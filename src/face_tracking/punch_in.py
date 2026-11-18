"""Punch-in zoom curve generator for dynamic vertical video reframing.

Consolidated and adapted from OpenShorts punch_in:
- Pushes toward the subject on emphasis beats (word emphasis or audio spikes).
- Asymmetric push envelope: fast snap in (0.25s), hold (1.3s), slow drift out (0.55s).
- Smoothstep easing ensures motion reads as deliberate editorial intent rather than mechanical jitter.
- Max zoom 1.12 (12% punch) keeps faces properly framed without awkward cropping.
"""
from typing import List, Optional
import numpy as np

DEFAULT_MAX_ZOOM = 1.12
RISE_SECONDS = 0.25
HOLD_SECONDS = 1.30
FALL_SECONDS = 0.55
MIN_GAP_SECONDS = 12.0


def _ease(t: float) -> float:
    """Smoothstep on [0, 1]."""
    t = min(max(t, 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def compute_zoom_curve(
    n_frames: int,
    fps: float,
    emphasis_times: List[float],
    max_zoom: float = DEFAULT_MAX_ZOOM,
    start_offset: float = 0.0
) -> List[float]:
    """Calculate per-frame zoom multiplier factor (1.0 = normal canvas, >1.0 = zoomed in)."""
    zooms = [1.0] * max(0, n_frames)
    if not zooms or max_zoom <= 1.0 or not emphasis_times or fps <= 0:
        return zooms

    # Filter beats within the scene window with minimum gap
    clean_beats: List[float] = []
    last_beat = -999.0
    for beat in sorted(emphasis_times):
        relative_t = beat - start_offset
        if 0.0 <= relative_t <= (n_frames / fps) and (relative_t - last_beat) >= MIN_GAP_SECONDS:
            clean_beats.append(relative_t)
            last_beat = relative_t

    if not clean_beats:
        return zooms

    for i in range(n_frames):
        t = i / fps
        factor = 1.0
        for beat in clean_beats:
            dt = t - beat
            if dt < 0:
                continue
            if dt < RISE_SECONDS:
                # Snapping in
                progress = _ease(dt / RISE_SECONDS)
                factor = max(factor, 1.0 + (max_zoom - 1.0) * progress)
            elif dt < (RISE_SECONDS + HOLD_SECONDS):
                # Holding peak zoom
                factor = max(factor, max_zoom)
            elif dt < (RISE_SECONDS + HOLD_SECONDS + FALL_SECONDS):
                # Smoothly drifting back
                progress = 1.0 - _ease((dt - RISE_SECONDS - HOLD_SECONDS) / FALL_SECONDS)
                factor = max(factor, 1.0 + (max_zoom - 1.0) * progress)
        zooms[i] = round(factor, 4)

    return zooms
