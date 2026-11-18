"""AI CLIPPING STUDIO: Face Detection, Tracking & Dynamic Reframing.

Uses OpenCV YuNet ONNX face detection to compute jitter-free, smoothed camera
trajectories for 9:16 vertical, 1:1 square, and custom crop windows.
"""
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from config import config


@dataclass
class FaceBox:
    x: float
    y: float
    w: float
    h: float
    score: float
    centroid_x: float
    centroid_y: float


FaceBBox = FaceBox


class SmoothedCamera:
    """Exponentially smoothed camera trajectory solver to eliminate jitter."""

    def __init__(self, smoothing_factor: float = 0.12):
        self.smoothing = smoothing_factor
        self.current_center_x: Optional[float] = None
        self.current_center_y: Optional[float] = None

    def update(self, target_center_x: float, target_center_y: float) -> Tuple[float, float]:
        if self.current_center_x is None:
            self.current_center_x = target_center_x
            self.current_center_y = target_center_y
        else:
            self.current_center_x += (target_center_x - self.current_center_x) * self.smoothing
            self.current_center_y += (target_center_y - self.current_center_y) * self.smoothing
        return self.current_center_x, self.current_center_y

    def reset(self):
        self.current_center_x = None
        self.current_center_y = None


class FaceTracker:
    """Detects faces in video frames and calculates dynamic reframing crop windows."""

    def __init__(self, score_threshold: float = 0.6):
        self.score_threshold = score_threshold
        self.model_path = str(config.yunet_model)
        self.camera = SmoothedCamera()

        # Cache detector instances by input resolution
        self._detectors: Dict[Tuple[int, int], cv2.FaceDetectorYN] = {}

    def _get_detector(self, width: int, height: int) -> cv2.FaceDetectorYN:
        key = (width, height)
        if key not in self._detectors:
            detector = cv2.FaceDetectorYN.create(
                model=self.model_path,
                config="",
                input_size=(width, height),
                score_threshold=self.score_threshold,
                nms_threshold=0.3,
                top_k=5000
            )
            self._detectors[key] = detector
        return self._detectors[key]

    def detect_faces(self, frame: np.ndarray) -> List[FaceBox]:
        """Detect all faces in a BGR frame above the confidence threshold."""
        h, w = frame.shape[:2]
        detector = self._get_detector(w, h)

        _, raw_faces = detector.detect(frame)
        if raw_faces is None or len(raw_faces) == 0:
            return []

        results = []
        for f in raw_faces:
            fx, fy, fw, fh = float(f[0]), float(f[1]), float(f[2]), float(f[3])
            score = float(f[14])
            if score >= self.score_threshold and fw > 20 and fh > 20:
                results.append(FaceBox(
                    x=fx,
                    y=fy,
                    w=fw,
                    h=fh,
                    score=score,
                    centroid_x=fx + (fw / 2.0),
                    centroid_y=fy + (fh / 2.0)
                ))

        # Sort by face area (descending)
        results.sort(key=lambda b: b.w * b.h, reverse=True)
        return results

    def compute_crop_window(
        self,
        frame_width: int,
        frame_height: int,
        face: Optional[FaceBox],
        target_aspect: str = "9:16"
    ) -> Tuple[int, int, int, int]:
        """Calculate the crop rectangle (x, y, w, h) for the target aspect ratio."""
        if target_aspect == "9:16":
            # For 9:16 on a 16:9 source, crop height is the full frame height
            crop_h = frame_height
            crop_w = int(round(crop_h * 9.0 / 16.0))
        elif target_aspect == "1:1":
            crop_h = frame_height
            crop_w = frame_height
        else: # 16:9 or default
            return (0, 0, frame_width, frame_height)

        if face is not None:
            target_x = face.centroid_x
            target_y = face.centroid_y
        else:
            target_x = frame_width / 2.0
            target_y = frame_height / 2.0

        smoothed_x, _ = self.camera.update(target_x, target_y)

        # Center the crop box horizontally on the smoothed face center
        crop_x = int(round(smoothed_x - (crop_w / 2.0)))
        crop_y = 0

        # Clamp within frame boundaries
        crop_x = max(0, min(frame_width - crop_w, crop_x))
        crop_y = max(0, min(frame_height - crop_h, crop_y))

        return (crop_x, crop_y, crop_w, crop_h)

    def generate_reframe_trajectory(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        sample_fps: float = 4.0,
        target_aspect: str = "9:16"
    ) -> List[Dict[str, Any]]:
        """Sample video frames across time range and compute a smooth camera path."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video for tracking: {video_path}")

        source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000.0)
        self.camera.reset()

        step_seconds = 1.0 / sample_fps
        current_time = start_time
        trajectory = []

        while current_time <= end_time:
            cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000.0)
            ret, frame = cap.read()
            if not ret:
                break

            faces = self.detect_faces(frame)
            main_face = faces[0] if faces else None
            cx, cy, cw, ch = self.compute_crop_window(frame_w, frame_h, main_face, target_aspect)

            trajectory.append({
                "time": round(current_time - start_time, 2),
                "x": cx,
                "y": cy,
                "width": cw,
                "height": ch,
                "hasFace": main_face is not None
            })

            current_time += step_seconds

        cap.release()
        return trajectory
