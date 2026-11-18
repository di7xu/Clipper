"""Universal FFmpeg Video Rendering & Export Pipeline.

Executes declarative Edit Plans: combines dynamic reframing, B-roll overlays,
ASS karaoke subtitle burning, EBU R128 audio normalization, and hardware-accelerated GPU export.
Consolidated from Cutawan, OpenShorts, SupoClip, and Chopify.
"""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Callable, Dict, List, Optional

from config import config
from captions.compiler import compile_ass_subtitles
from captions.styles import PRESET_STYLES
from rendering.encoders import get_encoder_args, get_audio_args
from broll.overlay import normalize_broll_overlays, broll_input_args, broll_overlay_graph


class RenderError(Exception):
    """Raised when video rendering fails."""
    pass


class RenderEngine:
    """Orchestrates FFmpeg filter construction, subtitle burning, and hardware encoding."""

    def __init__(self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.progress_callback = progress_callback

    def render(self, edit_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute video render from declarative Edit Plan dictionary."""
        source_path = Path(edit_plan["sourcePath"]).resolve()
        if not source_path.is_file():
            raise RenderError(f"Source video does not exist: {source_path}")

        output_path = Path(edit_plan["outputPath"]).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        clip_start = float(edit_plan.get("clipStart", 0.0))
        clip_end = float(edit_plan.get("clipEnd", 0.0))
        clip_duration = clip_end - clip_start
        if clip_duration <= 0.0:
            raise RenderError(f"Invalid clip duration: {clip_duration}s")

        aspect = edit_plan.get("aspectRatio", "9:16")
        target_w = int(edit_plan.get("targetWidth", 1080))
        target_h = int(edit_plan.get("targetHeight", 1920))
        audio_norm = edit_plan.get("audioNorm", True)
        encoder = edit_plan.get("encoder", "auto")
        words = edit_plan.get("words", [])
        caption_style_name = edit_plan.get("captionStyle", "viral_yellow")
        style = PRESET_STYLES.get(caption_style_name, PRESET_STYLES["viral_yellow"])

        keep_ranges = edit_plan.get("keepRanges", [(0.0, clip_duration)])
        raw_broll = edit_plan.get("brollOverlays", [])
        broll_overlays = normalize_broll_overlays(raw_broll, clip_duration=clip_duration)
        layout_type = edit_plan.get("layout", "single_speaker")
        layout_config = edit_plan.get("layoutConfig", {})
        is_split_layout = (layout_type in ("split", "split_screen", "stacked", "podcast_split")) and (aspect == "9:16")

        # Temporary subtitle file
        ass_temp_path = config.temp_dir / f"subs_{int(time.time() * 1000)}.ass"

        try:
            # Step 1: Compile ASS subtitles if words are present
            has_captions = bool(words) and caption_style_name != "none"
            if has_captions:
                ass_content = compile_ass_subtitles(
                    words=words,
                    style=style,
                    clip_offset=0.0,
                    video_width=target_w,
                    video_height=target_h
                )
                ass_temp_path.write_text(ass_content, encoding="utf-8")

            # Aspect ratio cropping & scaling
            if aspect == "9:16":
                reframe_filter = f"crop=ih*(9/16):ih:(iw-ow)/2:0,scale={target_w}:{target_h}"
            elif aspect == "1:1":
                reframe_filter = f"crop=ih:ih:(iw-ow)/2:0,scale={target_w}:{target_h}"
            else:  # 16:9
                reframe_filter = f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2"

            sub_filter = ""
            if has_captions and ass_temp_path.is_file():
                escaped_ass = str(ass_temp_path).replace("\\", "/").replace(":", "\\:")
                escaped_fonts = str(config.fonts_dir).replace("\\", "/").replace(":", "\\:")
                sub_filter = f"subtitles='{escaped_ass}':fontsdir='{escaped_fonts}'"

            # Step 2: Build FFmpeg Command Line
            if len(keep_ranges) == 1 and not broll_overlays and not is_split_layout:
                # Optimized single range without B-roll or multi-speaker split
                k_start, k_end = keep_ranges[0]
                exact_start = clip_start + k_start
                exact_dur = k_end - k_start

                vf_chain = [reframe_filter]
                if sub_filter:
                    vf_chain.append(sub_filter)

                cmd = [
                    str(config.ffmpeg_path),
                    "-y",
                    "-nostdin",
                    "-ss", str(exact_start),
                    "-t", str(exact_dur),
                    "-i", str(source_path),
                    "-vf", ",".join(vf_chain)
                ]

                audio_flags, audio_filter = get_audio_args(loudnorm=audio_norm)
                cmd.extend(audio_flags)
                if audio_filter:
                    cmd.extend(["-af", audio_filter])

                cmd.extend(get_encoder_args(encoder_name=encoder))
                cmd.extend(["-progress", "pipe:1", str(output_path)])

            else:
                # Filter-complex pipeline (handles split stacked podcast layout, multi-cut tightening, B-roll overlays)
                cmd = [
                    str(config.ffmpeg_path),
                    "-y",
                    "-nostdin",
                    "-i", str(source_path),
                ]

                # Append B-roll input files
                if broll_overlays:
                    cmd.extend(broll_input_args(broll_overlays))

                complex_parts: List[str] = []

                if is_split_layout:
                    # Resolve source dimensions for podcast split layout
                    from video.probe import probe_video
                    try:
                        s_info = probe_video(str(source_path))
                        s_w, s_h = int(s_info["width"]), int(s_info["height"])
                    except Exception:
                        s_w, s_h = 1280, 720

                    half_h = target_h // 2  # 960
                    crop_w = min(s_w, int(round(s_h * (target_w / half_h))))  # 810 for 720p

                    spk_a_x = layout_config.get("speaker_a_x", 0)
                    spk_b_x = layout_config.get("speaker_b_x", max(0, s_w - crop_w))
                    spk_a_x = max(0, min(s_w - crop_w, int(spk_a_x)))
                    spk_b_x = max(0, min(s_w - crop_w, int(spk_b_x)))

                if len(keep_ranges) == 1:
                    k_s, k_e = keep_ranges[0]
                    abs_s = clip_start + k_s
                    abs_e = clip_start + k_e

                    if is_split_layout:
                        complex_parts.append(f"[0:v]trim=start={abs_s}:end={abs_e},setpts=PTS-STARTPTS,split=2[in_top][in_bot]")
                        complex_parts.append(f"[in_top]crop={crop_w}:{s_h}:{spk_a_x}:0,scale={target_w}:{half_h}[top_v]")
                        complex_parts.append(f"[in_bot]crop={crop_w}:{s_h}:{spk_b_x}:0,scale={target_w}:{half_h}[bot_v]")
                        complex_parts.append(f"[top_v][bot_v]vstack=inputs=2[base_v]")
                    else:
                        complex_parts.append(f"[0:v]trim=start={abs_s}:end={abs_e},setpts=PTS-STARTPTS,{reframe_filter}[base_v]")

                    complex_parts.append(f"[0:a]atrim=start={abs_s}:end={abs_e},asetpts=PTS-STARTPTS[a_cat]")

                else:
                    # Concat keep ranges for speech tightening
                    for idx, (k_start, k_end) in enumerate(keep_ranges):
                        abs_s = clip_start + k_start
                        abs_e = clip_start + k_end
                        complex_parts.append(f"[0:v]trim=start={abs_s}:end={abs_e},setpts=PTS-STARTPTS[v{idx}]")
                        complex_parts.append(f"[0:a]atrim=start={abs_s}:end={abs_e},asetpts=PTS-STARTPTS[a{idx}]")

                    v_inputs = "".join(f"[v{i}]" for i in range(len(keep_ranges)))
                    a_inputs = "".join(f"[a{i}]" for i in range(len(keep_ranges)))

                    if is_split_layout:
                        complex_parts.append(f"{v_inputs}concat=n={len(keep_ranges)}:v=1:a=0,split=2[in_top][in_bot]")
                        complex_parts.append(f"[in_top]crop={crop_w}:{s_h}:{spk_a_x}:0,scale={target_w}:{half_h}[top_v]")
                        complex_parts.append(f"[in_bot]crop={crop_w}:{s_h}:{spk_b_x}:0,scale={target_w}:{half_h}[bot_v]")
                        complex_parts.append(f"[top_v][bot_v]vstack=inputs=2[base_v]")
                    else:
                        complex_parts.append(f"{v_inputs}concat=n={len(keep_ranges)}:v=1:a=0,{reframe_filter}[base_v]")

                    complex_parts.append(f"{a_inputs}concat=n={len(keep_ranges)}:v=0:a=1[a_cat]")

                current_v = "[base_v]"

                # Apply B-roll overlay graph if present
                if broll_overlays:
                    broll_graph, current_v = broll_overlay_graph(
                        base_label="[base_v]",
                        overlays=broll_overlays,
                        width=target_w,
                        height=target_h,
                        first_input=1
                    )
                    complex_parts.append(broll_graph)

                if audio_norm:
                    norm_filter = "loudnorm=I=-16:TP=-1.5:LRA=11"
                    complex_parts.append(f"[a_cat]{norm_filter}[a_out]")
                    a_map = "[a_out]"
                else:
                    a_map = "[a_cat]"

                # Apply subtitles on top of composite
                if sub_filter:
                    complex_parts.append(f"{current_v}{sub_filter}[v_out]")
                else:
                    complex_parts.append(f"{current_v}null[v_out]")

                cmd.extend(["-filter_complex", ";".join(complex_parts)])
                cmd.extend(["-map", "[v_out]", "-map", a_map])

                audio_flags, _ = get_audio_args(loudnorm=False)
                cmd.extend(audio_flags)

                cmd.extend(get_encoder_args(encoder_name=encoder))
                cmd.extend(["-progress", "pipe:1", str(output_path)])

            # Step 3: Execute FFmpeg Process and Parse Progress
            self._emit_progress(0, "Starting FFmpeg render engine...")
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            log_lines: List[str] = []
            expected_micros = int(clip_duration * 1_000_000)
            last_pct = -20
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                stripped = line.strip()
                log_lines.append(stripped)
                if stripped.startswith("out_time_us="):
                    try:
                        curr_us = int(stripped.split("=")[1])
                        pct = min(99, int((curr_us / expected_micros) * 100))
                        if pct >= last_pct + 20:
                            print(f"      [Render Engine] Progress: {pct}% complete", flush=True)
                            last_pct = pct
                        self._emit_progress(pct, f"Rendering video ({pct}%)...")
                    except Exception:
                        pass

            proc.wait()
            if proc.returncode != 0:
                full_log = "\n".join(log_lines[-25:])
                raise RenderError(f"FFmpeg render exited with code {proc.returncode}:\n{full_log}")

            self._emit_progress(100, "Render completed successfully!")
            return {
                "success": True,
                "outputPath": str(output_path),
                "duration": clip_duration,
                "resolution": f"{target_w}x{target_h}",
                "aspectRatio": aspect,
                "captions": has_captions,
                "brollCount": len(broll_overlays)
            }

        finally:
            if ass_temp_path.is_file():
                try:
                    ass_temp_path.unlink()
                except Exception:
                    pass

    def _emit_progress(self, percent: int, message: str):
        if self.progress_callback:
            self.progress_callback({"percent": percent, "message": message})
