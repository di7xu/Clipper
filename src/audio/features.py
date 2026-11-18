"""Audio excitement signals and acoustic energy profiling, fully local.

Consolidated and adapted from Clips-Studio:
Decodes mono PCM via FFmpeg into NumPy:
- loudness: RMS energy per second
- spike: how loud this second is vs. rolling 30s median (shouts, hype moments)
- burst: density of sudden energy onsets (>2x jump) per second (laughter, cheers)
- noisiness: zero-crossing rate (broadband laughter vs. clean speech)
"""
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Dict, Optional
import numpy as np

from config import config

SAMPLE_RATE = 16000
FRAME = SAMPLE_RATE // 20  # 50 ms analysis frames


@dataclass
class AudioExcitementFeatures:
    loudness: np.ndarray
    spike: np.ndarray
    burst: np.ndarray
    noisiness: np.ndarray
    duration_seconds: float


def _decode_mono_pcm(video_path: Path) -> np.ndarray:
    """Extract raw 16kHz 16-bit mono PCM bytes via FFmpeg."""
    ffmpeg_bin = str(config.ffmpeg_path or "ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-nostdin",
        "-v", "error",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", str(SAMPLE_RATE),
        "-f", "s16le",
        "-"
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
        return np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    except Exception:
        return np.array([], dtype=np.float32)


def _rolling_median(arr: np.ndarray, window_size: int) -> np.ndarray:
    """Compute rolling median over window_size using sliding window."""
    if len(arr) == 0:
        return arr
    half = window_size // 2
    pad = np.pad(arr, (half, half), mode="edge")
    out = np.zeros_like(arr)
    for i in range(len(arr)):
        out[i] = np.median(pad[i : i + window_size])
    return out


def extract_audio_features(video_path: Path) -> Optional[AudioExcitementFeatures]:
    """Calculate acoustic excitement signals per second."""
    pcm = _decode_mono_pcm(video_path)
    if pcm.size < SAMPLE_RATE:
        return None

    n_frames = pcm.size // FRAME
    frames = pcm[: n_frames * FRAME].reshape(n_frames, FRAME)
    frame_rms = np.sqrt(np.mean(frames**2, axis=1) + 1e-12)

    frames_per_sec = SAMPLE_RATE // FRAME
    n_secs = n_frames // frames_per_sec
    if n_secs == 0:
        return None

    per_sec = frame_rms[: n_secs * frames_per_sec].reshape(n_secs, frames_per_sec)
    loudness = per_sec.mean(axis=1)

    # Spike: ratio of current second loudness to rolling 30s median
    spike = loudness / np.maximum(_rolling_median(loudness, 30), 1e-6)
    spike = np.clip(spike, 0.0, 5.0)

    # Burst: count of frame-level onsets (>2x energy jump over prior frame)
    onsets = frame_rms[1:] > 2.0 * np.maximum(frame_rms[:-1], 1e-6)
    onsets = np.concatenate([[False], onsets])
    burst = (
        onsets[: n_secs * frames_per_sec]
        .reshape(n_secs, frames_per_sec)
        .sum(axis=1)
        .astype(np.float32)
    )

    # Noisiness: zero-crossing rate per second
    signs = np.sign(pcm[: n_secs * SAMPLE_RATE])
    zero_crossings = (signs[1:] != signs[:-1]).astype(np.float32)
    noisiness = (
        np.concatenate([[0.0], zero_crossings])
        .reshape(n_secs, SAMPLE_RATE)
        .mean(axis=1)
    )

    return AudioExcitementFeatures(
        loudness=loudness,
        spike=spike,
        burst=burst,
        noisiness=noisiness,
        duration_seconds=float(n_secs)
    )
