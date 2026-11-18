"""AI Video Processing Environment: Master CLI & Execution Engine.

Unified entry point for AI Video Processing & Short-form Clipping:
1. Validates / Downloads source video (FFprobe / updated yt-dlp)
2. Transcribes locally with faster-whisper (CTranslate2 + Silero VAD)
3. Scores clips using multimodal heuristics (Hooks, Audio Energy, Story Arcs - 0 API cost)
4. Tightens speech (prunes filler words & silences, retimes subtitles)
5. Reframes dynamically (YuNet face tracking, camera smoothing, 9:16 / 1:1)
6. Compiles animated CapCut-style ASS karaoke subtitles (Anton, Poppins, Montserrat)
7. Optionally composites contextual B-roll cutaway overlays with alpha crossfades
8. Renders hardware-accelerated video clips (QSV / NVENC / libx264 + loudnorm)
9. Generates companion social media metadata (.meta.json)
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional

# Ensure src is in python path
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Ensure real-time line buffering so logs never buffer
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

from config import config
from captions.compiler import compile_ass_subtitles
from clip_detection.score_clips import ClipScorer
from editor.edit_plan import create_edit_plan
from editor.tighten import plan_cuts
from export.social_pack import generate_social_metadata, write_meta_package
from face_tracking.layouts import detect_podcast_speakers
from rendering.engine import RenderEngine
from transcription.engine import TranscribeEngine
from video.probe import probe_video, validate_media_file


def download_url(url: str, output_dir: Path) -> Path:
    """Download video from public URL using bundled/discovered yt-dlp."""
    output_dir.mkdir(parents=True, exist_ok=True)
    video_id = url.split("v=")[-1].split("?")[0].split("&")[0].split("/")[-1]

    # Check if already downloaded
    matching = [f for f in output_dir.glob("*.mp4") if video_id in f.name and f.stat().st_size > 1000000]
    if matching:
        downloaded = sorted(matching, key=lambda f: f.stat().st_mtime, reverse=True)[0]
        print(f"[yt-dlp] Using already downloaded source video: {downloaded.name}", flush=True)
        return downloaded

    out_template = str(output_dir / "%(title).50s [%(id)s].%(ext)s")
    ytdlp = config.ytdlp_path or "yt-dlp"

    print(f"[yt-dlp] Downloading video from: {url}", flush=True)
    cmd = [
        str(ytdlp),
        "--format", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--no-warnings",
        "--output", out_template,
        url
    ]

    proc = subprocess.run(cmd, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp failed to download video with code {proc.returncode}")

    # Find the downloaded mp4 file
    video_id = url.split("v=")[-1].split("?")[0].split("&")[0].split("/")[-1]
    matching = [f for f in output_dir.glob("*.mp4") if video_id in f.name]
    if matching:
        downloaded = sorted(matching, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    else:
        mp4_files = sorted(output_dir.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not mp4_files:
            raise FileNotFoundError(f"yt-dlp download completed but no MP4 found in {output_dir}")
        downloaded = mp4_files[0]

    print(f"[yt-dlp] Downloaded successfully: {downloaded.name}")
    return downloaded


def process_video(
    input_path: Optional[str] = None,
    url: Optional[str] = None,
    output_dir: Optional[str] = None,
    clip_count: int = 3,
    aspect_ratio: str = "9:16",
    caption_style: str = "viral_yellow",
    whisper_model: str = "base",
    task: str = "translate",
    language: Optional[str] = None,
    layout: str = "auto",
    clips_json: Optional[str] = None,
    tighten: bool = True,
    burn_captions: bool = True,
    platform: str = "youtube_shorts",
    broll_path: Optional[str] = None,
    target_duration: float = 30.0,
    min_duration: float = 15.0,
    max_duration: float = 60.0
) -> List[Dict[str, Any]]:
    """Execute the full end-to-end AI clipping pipeline."""
    # Resolve target directories
    out_dir = Path(output_dir).resolve() if output_dir else config.root_dir / "output_clips"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Acquire video file
    if url:
        downloads_dir = config.temp_dir / "downloads"
        source_video = download_url(url, downloads_dir)
    elif input_path:
        source_video = validate_media_file(input_path)
    else:
        raise ValueError("Either --input or --url must be provided.")

    print("\n" + "=" * 60)
    print("       AI VIDEO PROCESSING ENVIRONMENT")
    print(f" Source Video: {source_video.name}")
    print(f" Target Aspect: {aspect_ratio} | Captions: {caption_style}")
    print(f" Hardware Encoder: {config.hardware.preferred_encoder}")
    print("=" * 60 + "\n")

    # 2. Probe media
    print("[1/6] Probing video streams and container metadata...")
    media_info = probe_video(str(source_video))
    dur = media_info["durationSeconds"]
    w = media_info["width"]
    h = media_info["height"]
    print(f"  Duration: {dur:.1f}s | Resolution: {w}x{h} ({media_info['aspectRatio']}) | FPS: {media_info['fps']}")

    # 3. Transcribe with local faster-whisper
    transcript_cache = out_dir / f"{source_video.stem}_transcript_{task}.json"
    print(f"\n[2/6] Transcribing speech with local faster-whisper ({whisper_model} model, task={task})...")
    transcribe_engine = TranscribeEngine()
    transcript = transcribe_engine.transcribe(
        media_path=str(source_video),
        output_json=str(transcript_cache),
        model_size=whisper_model,
        language=language,
        task=task
    )
    words = transcript.get("words", [])
    sentences = transcript.get("sentences", [])
    print(f"  Transcribed {len(words)} words across {len(sentences)} complete sentences.")

    if not words:
        print("  Warning: No speech detected in video. Proceeding with video highlights.")

    # 4. Multimodal Clip Selection (Model-Curated or Heuristic Scoring)
    if clips_json:
        import json
        print(f"\n[3/6] Loading Antigravity Model confirmed clips from: {clips_json[:40]}...")
        if os.path.isfile(clips_json):
            with open(clips_json, "r", encoding="utf-8") as f:
                curated_raw = json.load(f)
        else:
            curated_raw = json.loads(clips_json)

        selected_clips = []
        for c_idx, c in enumerate(curated_raw, 1):
            c_start = float(c["start"])
            c_end = float(c["end"])
            c_words = [w for w in words if float(w.get("start", 0)) >= c_start - 0.2 and float(w.get("end", 0)) <= c_end + 0.2]
            selected_clips.append({
                "id": c.get("id", f"clip_{c_idx:02d}"),
                "start": c_start,
                "end": c_end,
                "title": c.get("title", f"Clip {c_idx}"),
                "hook": c.get("hook", c.get("title", "")),
                "overallScore": float(c.get("score", 95.0)),
                "words": c_words
            })
    else:
        print("\n[3/6] Scoring viral candidate clips (Hooks, Emotion, Energy & Story Arc)...")
        scorer = ClipScorer()
        candidates = scorer.score_project(
            transcript=transcript,
            options={
                "min_len": min_duration,
                "max_len": max_duration,
                "target_len": target_duration
            }
        )

        if not candidates:
            print("  No candidate clips met the criteria. Creating full video clip.")
            candidates = [{
                "id": "clip_01",
                "start": 0.0,
                "end": min(dur, max_duration),
                "title": source_video.stem[:40],
                "hook": "Must watch highlight",
                "overallScore": 85.0,
                "transcript": transcript.get("text", "")[:200],
                "words": words
            }]

        # Select top N clips
        selected_clips = candidates[:clip_count]

    print(f"  Selected top {len(selected_clips)} clips for production:")
    for idx, c in enumerate(selected_clips, 1):
        c_dur = c["end"] - c["start"]
        print(f"    {idx}. [{c['overallScore']:.1f} pts] \"{c.get('title', 'Clip')}\" ({c['start']:.1f}s - {c['end']:.1f}s | {c_dur:.1f}s)")

    # Prepare optional B-roll overlays
    broll_overlays = []
    if broll_path and Path(broll_path).is_file():
        # Place a 3-second cutaway midway through each clip
        broll_overlays.append({
            "path": str(Path(broll_path).resolve()),
            "start": 6.0,
            "duration": 3.0,
            "offset": 0.0,
            "fade_in": True,
            "fade_out": True
        })
        print(f"  B-Roll enabled: {Path(broll_path).name} (3.0s cutaway at 6.0s)")

    # 5. Render selected clips
    print("\n[4/6] Reframing, subtitle compiling, and hardware-accelerated rendering...")
    renderer = RenderEngine()
    rendered_results = []

    for idx, clip in enumerate(selected_clips, 1):
        clip_id = clip.get("id", f"clip_{idx:02d}")
        title = clip.get("title", f"Clip {idx}")
        print(f"\n  --> Processing Clip {idx}/{len(selected_clips)}: \"{title}\"")

        # Resolve Layout: Check for podcast 2-person dialogue
        if layout in ("split", "stacked"):
            chosen_layout = "split"
            _, xa, xb = detect_podcast_speakers(str(source_video), clip["start"], clip["end"] - clip["start"], w, h)
            layout_cfg = {"speaker_a_x": xa, "speaker_b_x": xb}
        elif layout == "single":
            chosen_layout = "single_speaker"
            layout_cfg = {}
        else: # auto
            is_split, xa, xb = detect_podcast_speakers(str(source_video), clip["start"], clip["end"] - clip["start"], w, h)
            if is_split and aspect_ratio == "9:16":
                chosen_layout = "split"
                layout_cfg = {"speaker_a_x": xa, "speaker_b_x": xb}
                print(f"      Podcast 2-speaker shot detected: Applying Top-Bottom Stacked Layout (Speaker A: {xa}px, Speaker B: {xb}px)", flush=True)
            else:
                chosen_layout = "single_speaker"
                layout_cfg = {}

        # Create edit plan
        plan = create_edit_plan(
            clip=clip,
            project_id=source_video.stem[:20],
            source_path=str(source_video),
            output_dir=str(out_dir),
            aspect_ratio=aspect_ratio,
            caption_style=caption_style if burn_captions else "minimal_white",
            tighten=tighten,
            layout=chosen_layout,
            layout_config=layout_cfg,
            broll_overlays=broll_overlays
        )

        plan_dict = plan.to_dict()
        if not burn_captions:
            plan_dict["captionStyle"] = "none"

        # Execute render
        print(f"      Rendering {aspect_ratio} MP4 with {config.hardware.preferred_encoder}...")
        render_res = renderer.render(plan_dict)

        if render_res.get("success"):
            out_mp4 = render_res["outputPath"]
            print(f"      Rendered successfully: {Path(out_mp4).name}")

            # 6. Generate Social Metadata (.meta.json)
            social_meta = generate_social_metadata(clip, platform_preset=platform)
            meta_file = write_meta_package(social_meta, out_mp4)
            print(f"      Generated social pack: {meta_file.name}")

            rendered_results.append({
                "clip": clip,
                "video_path": out_mp4,
                "meta_path": str(meta_file),
                "social_metadata": social_meta
            })
        else:
            print(f"      Render failed: {render_res.get('error')}")

    print("\n" + "=" * 60)
    print("       PIPELINE COMPLETED SUCCESSFULLY!")
    print(f" Rendered {len(rendered_results)}/{len(selected_clips)} clips to:")
    print(f" {out_dir}")
    print("=" * 60 + "\n")

    return rendered_results


def main():
    parser = argparse.ArgumentParser(
        description="AI Video Processing Environment: Transform long-form videos into viral vertical clips."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--input", help="Path to local input video file (MP4, MOV, MKV, etc.)")
    group.add_argument("-u", "--url", help="Public video URL (YouTube, Vimeo, Twitch) to download and clip")

    parser.add_argument("-o", "--output", default="output_clips", help="Output directory for rendered clips (default: output_clips/)")
    parser.add_argument("-n", "--count", type=int, default=3, help="Number of clips to extract and render (default: 3)")
    parser.add_argument("-a", "--aspect", choices=["9:16", "1:1", "16:9"], default="9:16", help="Target aspect ratio (default: 9:16)")
    parser.add_argument("-s", "--style", choices=["viral_yellow", "clean_cyan", "bold_coral", "minimal_white"], default="viral_yellow", help="Caption style (default: viral_yellow)")
    parser.add_argument("-m", "--model", choices=["tiny", "base", "small", "medium"], default="base", help="Whisper model size (default: base)")
    parser.add_argument("-p", "--platform", choices=["youtube_shorts", "tiktok", "instagram_reels"], default="youtube_shorts", help="Social media preset (default: youtube_shorts)")
    parser.add_argument("-b", "--broll", help="Optional path to B-roll video file for stock cutaway overlays")
    parser.add_argument("-l", "--layout", choices=["auto", "single", "split", "stacked"], default="auto", help="Video framing layout: auto (podcast split detection), single (centered face), or split/stacked (top-bottom) (default: auto)")
    parser.add_argument("-t", "--task", choices=["translate", "transcribe"], default="translate", help="Whisper task: translate (translates foreign speech to clean English) or transcribe (default: translate)")
    parser.add_argument("--lang", "--language", dest="language", default=None, help="Spoken language code (e.g. 'hi' for Hindi, default: auto-detect)")
    parser.add_argument("--clips-json", default=None, help="Path to JSON file or raw JSON string of model-curated clips [{start, end, title}]")
    parser.add_argument("--no-tighten", action="store_true", help="Disable filler word and silence tightening")
    parser.add_argument("--no-captions", action="store_true", help="Disable burned-in animated karaoke captions")

    args = parser.parse_args()

    try:
        results = process_video(
            input_path=args.input,
            url=args.url,
            output_dir=args.output,
            clip_count=args.count,
            aspect_ratio=args.aspect,
            caption_style=args.style,
            whisper_model=args.model,
            task=args.task,
            language=args.language,
            layout=args.layout,
            clips_json=args.clips_json,
            tighten=not args.no_tighten,
            burn_captions=not args.no_captions,
            platform=args.platform,
            broll_path=args.broll
        )
        print(f"Completed! {len(results)} clips generated.")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
