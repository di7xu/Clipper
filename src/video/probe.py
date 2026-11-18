"""AI CLIPPING STUDIO: Video Ingest, Stream Validation & Metadata Extraction.

Inspects video files using FFprobe, extracting precise resolution, aspect ratio,
frame rates, audio channels, and stream parameters.
"""
import fractions
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional

from config import config

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


class MediaProbeError(Exception):
    """Raised when media probing or validation fails."""
    pass


def validate_media_file(file_path: str) -> Path:
    """Validate that the file exists, is non-empty, and has a supported container extension."""
    path = Path(file_path).resolve()
    if not path.is_file():
        raise MediaProbeError(f"File not found: {file_path}")

    if path.stat().st_size == 0:
        raise MediaProbeError(f"File is empty (0 bytes): {file_path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise MediaProbeError(
            f"Unsupported format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    return path


def parse_frame_rate(fps_str: Optional[str]) -> float:
    """Safely parse FFprobe fractional frame rate strings (e.g. '30000/1001', '24/1', '60')."""
    if not fps_str or fps_str == "0/0" or fps_str == "0":
        return 30.0
    try:
        if "/" in fps_str:
            num, den = fps_str.split("/")
            return round(float(num) / float(den), 3) if float(den) != 0 else 30.0
        return round(float(fps_str), 3)
    except Exception:
        return 30.0


def probe_video(file_path: str) -> Dict[str, Any]:
    """Inspect video file with FFprobe and return structured MediaInfo metadata."""
    valid_path = validate_media_file(file_path)

    if not config.ffprobe_path or not config.ffprobe_path.is_file():
        raise MediaProbeError(f"FFprobe executable not found at: {config.ffprobe_path}")

    cmd = [
        str(config.ffprobe_path),
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(valid_path)
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            check=False
        )
    except subprocess.TimeoutExpired:
        raise MediaProbeError(f"FFprobe timed out while inspecting: {file_path}")
    except Exception as e:
        raise MediaProbeError(f"Failed to execute FFprobe: {e}")

    if proc.returncode != 0:
        raise MediaProbeError(f"FFprobe error: {proc.stderr.strip() or 'Unknown error'}")

    try:
        data = json.loads(proc.stdout)
    except Exception as e:
        raise MediaProbeError(f"Failed to parse FFprobe JSON output: {e}")

    streams = data.get("streams", [])
    format_info = data.get("format", {})

    video_stream: Optional[Dict[str, Any]] = None
    audio_stream: Optional[Dict[str, Any]] = None
    stream_details: List[Dict[str, Any]] = []

    for s in streams:
        codec_type = s.get("codec_type")
        idx = s.get("index", len(stream_details))
        codec_name = s.get("codec_name", "unknown")

        detail = {
            "index": idx,
            "codecType": codec_type,
            "codecName": codec_name
        }

        if codec_type == "video" and not video_stream:
            video_stream = s
            detail["width"] = s.get("width")
            detail["height"] = s.get("height")
            detail["fps"] = parse_frame_rate(s.get("r_frame_rate") or s.get("avg_frame_rate"))
            detail["bitrate"] = int(s.get("bit_rate")) if s.get("bit_rate") else None
        elif codec_type == "audio" and not audio_stream:
            audio_stream = s
            detail["channels"] = s.get("channels")
            detail["sampleRate"] = int(s.get("sample_rate")) if s.get("sample_rate") else None
            detail["bitrate"] = int(s.get("bit_rate")) if s.get("bit_rate") else None

        stream_details.append(detail)

    if not video_stream:
        raise MediaProbeError(f"File contains no valid video stream: {file_path}")

    width = int(video_stream.get("width") or 1920)
    height = int(video_stream.get("height") or 1080)
    fps = parse_frame_rate(video_stream.get("r_frame_rate") or video_stream.get("avg_frame_rate"))

    # Determine display aspect ratio string
    gcd = fractions.Fraction(width, height)
    aspect_ratio_str = f"{gcd.numerator}:{gcd.denominator}"
    if width == 1920 and height == 1080:
        aspect_ratio_str = "16:9"
    elif width == 1080 and height == 1920:
        aspect_ratio_str = "9:16"
    elif width == height:
        aspect_ratio_str = "1:1"

    duration = float(format_info.get("duration") or video_stream.get("duration") or 0.0)
    file_size = int(format_info.get("size") or valid_path.stat().st_size)

    return {
        "filePath": str(valid_path),
        "fileName": valid_path.name,
        "fileSizeBytes": file_size,
        "formatName": format_info.get("format_name", "unknown"),
        "durationSeconds": round(duration, 3),
        "width": width,
        "height": height,
        "fps": fps,
        "aspectRatio": aspect_ratio_str,
        "videoCodec": video_stream.get("codec_name", "unknown"),
        "audioCodec": audio_stream.get("codec_name", "none") if audio_stream else "none",
        "audioChannels": int(audio_stream.get("channels") or 0) if audio_stream else 0,
        "audioSampleRate": int(audio_stream.get("sample_rate") or 0) if audio_stream else 0,
        "streams": stream_details
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        info = probe_video(sys.argv[1])
        print(json.dumps(info, indent=2))
    else:
        print("Usage: python src/video/probe.py <video_path>")
