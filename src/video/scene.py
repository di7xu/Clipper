"""Scene change detection using FFmpeg's internal scene score filter.
Consolidated from OpenShorts and Chopify.
"""
from pathlib import Path
import re
import subprocess
from typing import List

from config import config


def detect_scene_cuts(video_path: Path, threshold: float = 0.35) -> List[float]:
    """Detect visual scene transitions and cuts in seconds."""
    ffmpeg_bin = str(config.ffmpeg_path or "ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-nostdin",
        "-v", "info",
        "-i", str(video_path),
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null",
        "-"
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False)
        output = proc.stderr or ""
    except Exception:
        return [0.0]

    cuts: List[float] = [0.0]
    # Parse showinfo pts_time: \bpts_time:([0-9.]+)
    for match in re.finditer(r"pts_time:([0-9.]+)", output):
        t = float(match.group(1))
        if t > cuts[-1] + 0.5:  # Debounce cuts closer than 0.5s
            cuts.append(round(t, 3))

    return cuts
