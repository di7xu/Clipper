"""Automated tests for Video Ingest and FFprobe metadata extraction."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import config
from video.probe import probe_video, validate_media_file, parse_frame_rate, MediaProbeError


@pytest.fixture(scope="session")
def synthetic_video(tmp_path_factory):
    """Generate a small 2-second synthetic MP4 video with video and audio tracks for testing."""
    temp_dir = tmp_path_factory.mktemp("media")
    video_path = temp_dir / "test_synth_1080p.mp4"

    # Use ffmpeg to generate a 2-second test video with testsrc and sine wave audio
    cmd = [
        str(config.ffmpeg_path),
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=2:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        str(video_path)
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, f"FFmpeg synthetic video generation failed: {res.stderr}"
    assert video_path.is_file()
    return str(video_path)


def test_parse_frame_rate():
    assert parse_frame_rate("30/1") == 30.0
    assert parse_frame_rate("30000/1001") == 29.97
    assert parse_frame_rate("24") == 24.0
    assert parse_frame_rate("0/0") == 30.0
    assert parse_frame_rate(None) == 30.0


def test_validate_media_file(synthetic_video):
    valid = validate_media_file(synthetic_video)
    assert valid.is_file()

    with pytest.raises(MediaProbeError):
        validate_media_file("non_existent_file.mp4")

    # Unsupported format
    txt_file = Path(synthetic_video).parent / "dummy.txt"
    txt_file.write_text("not a video")
    with pytest.raises(MediaProbeError):
        validate_media_file(str(txt_file))


def test_probe_video(synthetic_video):
    info = probe_video(synthetic_video)

    assert info["fileName"] == "test_synth_1080p.mp4"
    assert info["width"] == 1280
    assert info["height"] == 720
    assert info["fps"] == 30.0
    assert info["durationSeconds"] >= 1.9 and info["durationSeconds"] <= 2.1
    assert info["videoCodec"] == "h264"
    assert info["audioCodec"] == "aac"
    assert info["audioChannels"] == 1
    assert len(info["streams"]) >= 2
