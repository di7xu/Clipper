"""Automated integration tests for Video Rendering, Encoders and Social Metadata."""
from pathlib import Path
import subprocess
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import config
from editor.edit_plan import create_edit_plan
from export.presets import EXPORT_PRESETS
from export.social_pack import generate_social_metadata, write_meta_package
from rendering.encoders import get_encoder_args
from rendering.engine import RenderEngine
from video.probe import probe_video


@pytest.fixture(scope="session")
def render_source_video(tmp_path_factory):
    """Generate a 3-second synthetic 16:9 test video for rendering tests."""
    temp_dir = tmp_path_factory.mktemp("render_test")
    video_path = temp_dir / "source_16x9.mp4"

    cmd = [
        str(config.ffmpeg_path),
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=3:size=1920x1080:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=800:duration=3",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        str(video_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return str(video_path)


def test_encoder_args():
    args_nvenc = get_encoder_args("h264_nvenc")
    assert "-c:v" in args_nvenc
    assert "h264_nvenc" in args_nvenc
    assert "yuv420p" in args_nvenc

    args_cpu = get_encoder_args("libx264")
    assert "libx264" in args_cpu
    assert "-crf" in args_cpu


def test_social_metadata_and_package(tmp_path):
    clip = {
        "id": "clip_01",
        "title": "Massive Software Mistake",
        "hook": "Do not make this mistake",
        "transcript": "Why is that a massive mistake in software development? Because customers will never trust your tool again.",
        "overallScore": 9.2
    }

    meta = generate_social_metadata(clip, platform_preset="youtube_shorts")
    assert meta["title"] == "Massive Software Mistake"
    assert len(meta["hashtags"]) >= 4
    assert "#Shorts" in meta["hashtags"]

    dummy_mp4 = tmp_path / "clip_01.mp4"
    dummy_mp4.write_text("mp4 data")

    meta_file = write_meta_package(meta, str(dummy_mp4))
    assert meta_file.is_file()
    assert meta_file.name == "clip_01.meta.json"


def test_end_to_end_render(render_source_video, tmp_path):
    clip = {
        "id": "clip_test_01",
        "start": 0.5,
        "end": 2.5,
        "words": [
            {"word": "HELLO", "start": 0.6, "end": 1.2},
            {"word": "WORLD", "start": 1.3, "end": 2.2}
        ]
    }

    # Create 9:16 vertical edit plan
    plan = create_edit_plan(
        clip=clip,
        project_id="test_proj",
        source_path=render_source_video,
        output_dir=str(tmp_path),
        aspect_ratio="9:16",
        caption_style="viral_yellow",
        tighten=False
    )

    renderer = RenderEngine()
    result = renderer.render(plan.to_dict())

    assert result["success"] is True
    out_file = Path(result["outputPath"])
    assert out_file.is_file()
    assert out_file.stat().st_size > 0

    # Probe rendered output with ffprobe
    meta = probe_video(str(out_file))
    assert meta["width"] == 1080
    assert meta["height"] == 1920
    assert meta["aspectRatio"] == "9:16"
    assert meta["durationSeconds"] >= 1.9 and meta["durationSeconds"] <= 2.1
    assert meta["audioChannels"] == 2  # Stereo AAC
