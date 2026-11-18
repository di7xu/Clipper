"""B-Roll overlay engine for AI Video Clipping.
Consolidated from SupoClip's stock cutaways and overlay engine.
"""
from .overlay import (
    normalize_broll_overlays,
    broll_input_args,
    broll_overlay_graph,
    BrollOverlay
)

__all__ = [
    "normalize_broll_overlays",
    "broll_input_args",
    "broll_overlay_graph",
    "BrollOverlay"
]
