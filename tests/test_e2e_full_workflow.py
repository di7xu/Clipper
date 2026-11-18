"""End-to-end integration test verifying the unified AI Video Processing pipeline:
Probe -> Heuristic Score -> Tighten -> Edit Plan -> B-roll -> Render Vertical (9:16) -> Social Pack.
"""
from pathlib import Path
import json
import subprocess
import sys
import pytest

from config import config
from editor.edit_plan import create_edit_plan
from export.social_pack import generate_social_metadata, write_meta_package
from rendering.engine import RenderEngine
from video.probe import probe_video


@pytest.fixture(scope="module")
def sample_video(tmp_path_factory):
    """Generate a 4-second synthetic 1920x1080 test video with a sine wave tone."""
    temp_dir = tmp_path_factory.mktemp("e2e_test")
    video_file = temp_dir / "sample_interview.mp4"

    cmd = [
        str(config.ffmpeg_path),
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=4:size=1920x1080:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        str(video_file)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return str(video_file)


def test_full_pipeline_e2e(sample_video, tmp_path):
    # 1. Probe Media
    probe_res = probe_video(sample_video)
    assert probe_res["width"] == 1920
    assert probe_res["height"] == 1080
    assert probe_res["durationSeconds"] >= 3.8

    # 2. Mock scored candidate clip
    clip = {
        "id": "e2e_clip_01",
        "start": 0.5,
        "end": 3.5,
        "title": "Viral Breakthrough Moment",
        "hook": "Wait till the end",
        "overallScore": 92.5,
        "words": [
            {"word": "This", "start": 0.5, "end": 0.8},
            {"word": "is", "start": 0.9, "end": 1.1},
            {"word": "an", "start": 1.2, "end": 1.4},
            {"word": "insane", "start": 1.5, "end": 2.2},
            {"word": "result.", "start": 2.3, "end": 3.4}
        ]
    }

    # 3. Create Edit Plan with B-roll cutaway
    broll_file = tmp_path / "stock_cutaway.mp4"
    cmd_broll = [
        str(config.ffmpeg_path),
        "-y",
        "-f", "lavfi", "-i", "testsrc=duration=2:size=1920x1080:rate=30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(broll_file)
    ]
    subprocess.run(cmd_broll, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    broll_overlays = [{
        "path": str(broll_file),
        "start": 1.0,
        "duration": 1.5,
        "offset": 0.0,
        "fade_in": True,
        "fade_out": True
    }]

    out_dir = tmp_path / "out_clips"
    out_dir.mkdir(parents=True, exist_ok=True)

    plan = create_edit_plan(
        clip=clip,
        project_id="e2e_proj",
        source_path=sample_video,
        output_dir=str(out_dir),
        aspect_ratio="9:16",
        caption_style="viral_yellow",
        tighten=True,
        broll_overlays=broll_overlays
    )
    assert plan.target_width == 1080
    assert plan.target_height == 1920
    assert len(plan.broll_overlays) == 1

    # 4. Render vertical 9:16 clip
    renderer = RenderEngine()
    render_res = renderer.render(plan.to_dict())
    assert render_res["success"] is True
    out_mp4 = Path(render_res["outputPath"])
    assert out_mp4.is_file()
    assert out_mp4.stat().st_size > 5000

    # 5. Verify Output Resolution
    out_probe = probe_video(str(out_mp4))
    assert out_probe["width"] == 1080
    assert out_probe["height"] == 1920

    # 6. Generate Social Media Package
    meta = generate_social_metadata(clip, platform_preset="youtube_shorts")
    meta_path = write_meta_package(meta, str(out_mp4))
    assert meta_path.is_file()

    with open(meta_path, "r", encoding="utf-8") as f:
        saved_meta = json.load(f)
    assert "title" in saved_meta
    assert "hashtags" in saved_meta
