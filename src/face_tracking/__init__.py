"""Face detection, tracking, layout calculation, and punch-in zoom beats.
Consolidated from OpenShorts, Cutawan, and SupoClip.
"""
from .tracker import FaceTracker, FaceBox, FaceBBox
from .layouts import LayoutCalculator, LayoutType
from .punch_in import compute_zoom_curve

__all__ = ["FaceTracker", "FaceBox", "FaceBBox", "LayoutCalculator", "LayoutType", "compute_zoom_curve"]
