"""Face detection, tracking, layout calculation, and punch-in zoom beats.
Consolidated from OpenShorts, Cutawan, and SupoClip.
"""
from .tracker import FaceTracker, FaceBox, FaceBBox
from .layouts import LayoutCalculator, LayoutType, build_split_filtergraph, detect_podcast_speakers
from .punch_in import compute_zoom_curve

__all__ = ["FaceTracker", "FaceBox", "FaceBBox", "LayoutCalculator", "LayoutType", "compute_zoom_curve", "build_split_filtergraph", "detect_podcast_speakers"]
