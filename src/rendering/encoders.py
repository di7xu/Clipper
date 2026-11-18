"""AI CLIPPING STUDIO: Hardware-Accelerated Video Encoder Configurations.

Detects and optimizes encoding parameters for NVIDIA NVENC, Intel QSV,
Apple VideoToolbox, and CPU libx264.
"""
from typing import Dict, List, Optional, Tuple

from config import config


def get_encoder_args(encoder_name: str = "auto", quality: str = "high") -> List[str]:
    """Return optimized FFmpeg encoding CLI arguments for the specified encoder."""
    if encoder_name == "auto":
        encoder_name = config.hardware.preferred_encoder

    if encoder_name == "h264_nvenc":
        # NVIDIA NVENC Hardware Accelerated
        preset = "p5" if quality == "high" else "p4"
        return [
            "-c:v", "h264_nvenc",
            "-preset", preset,
            "-tune", "hq",
            "-rc", "vbr",
            "-cq", "22",
            "-b:v", "0",
            "-maxrate", "12M",
            "-bufsize", "24M",
            "-pix_fmt", "yuv420p"
        ]
    elif encoder_name == "h264_qsv":
        # Intel QuickSync Video
        return [
            "-c:v", "h264_qsv",
            "-preset", "medium",
            "-global_quality", "22",
            "-r", "30",
            "-pix_fmt", "nv12"
        ]
    elif encoder_name == "h264_videotoolbox":
        # Apple Silicon / macOS VideoToolbox
        return [
            "-c:v", "h264_videotoolbox",
            "-q:v", "68",
            "-pix_fmt", "yuv420p"
        ]
    else:
        # High quality multi-threaded CPU fallback
        preset = "medium" if quality == "high" else "fast"
        return [
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", "22",
            "-pix_fmt", "yuv420p"
        ]


def get_audio_args(loudnorm: bool = True) -> Tuple[List[str], Optional[str]]:
    """Return AAC audio encoding arguments and optional loudnorm filter string."""
    audio_flags = [
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-ac", "2"
    ]
    audio_filter = "loudnorm=I=-16:TP=-1.5:LRA=11" if loudnorm else None
    return audio_flags, audio_filter
