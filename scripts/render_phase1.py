"""AI CLIPPING STUDIO: Phase 1 Batch Renderer (Clips 01 - 20)
Category 1: Crazy Crashes & High-Speed Car Chases
Full 1080x1920 60FPS with Animated Karaoke Subtitles & EBU R128 Audio
"""
import os
import sys
import time
import json
import wave
import subprocess
from pathlib import Path
import numpy as np

sys.path.insert(0, os.path.abspath("src"))
from captions.compiler import compile_ass_subtitles
from captions.styles import PRESET_STYLES
from dataclasses import replace
import faster_whisper

SOURCE_VIDEO = "workspace_temp/downloads/IShowSpeed_GTA6_1080p.mp4"
OUTPUT_DIR = Path("output_clips/IShowSpeed_GTA6/Phase_01")
TEMP_DIR = Path("workspace_temp/phase_01")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

PHASE_01_CLIPS = [
    {"id": "01", "title": "Speed First Time Driving in GTA 6", "start": 75.0, "end": 102.0, "score": 99},
    {"id": "02", "title": "Full Speed Supercar Highway Crash", "start": 128.0, "end": 153.0, "score": 96},
    {"id": "03", "title": "Speed Flips Car Over Vice City Bridge", "start": 190.0, "end": 216.0, "score": 95},
    {"id": "04", "title": "BRO THIS CAR CANT TURN Rage Drift", "start": 262.0, "end": 287.0, "score": 94},
    {"id": "05", "title": "Speed Hits An Ambulance Head-On", "start": 340.0, "end": 365.0, "score": 97},
    {"id": "06", "title": "Speed Steals a Police Cruiser at 100 MPH", "start": 410.0, "end": 438.0, "score": 98},
    {"id": "07", "title": "Speed Launches Off a Construction Ramp", "start": 485.0, "end": 512.0, "score": 96},
    {"id": "08", "title": "Motorcycle High-Speed Ejection Ragdoll", "start": 554.0, "end": 578.0, "score": 98},
    {"id": "09", "title": "Speed Tries to Outrun a Helicopter on Highway", "start": 620.0, "end": 648.0, "score": 95},
    {"id": "10", "title": "Speed Crashes Straight into Vice City Gas Station", "start": 692.0, "end": 718.0, "score": 99},
    {"id": "11", "title": "Insane Train Collision Speed Didnt See Coming", "start": 765.0, "end": 792.0, "score": 97},
    {"id": "12", "title": "Speed Drives a Boat Onto the Beach at 80 Knots", "start": 842.0, "end": 868.0, "score": 96},
    {"id": "13", "title": "Bicycle Stunt Gone Terribly Wrong", "start": 915.0, "end": 938.0, "score": 93},
    {"id": "14", "title": "Speed Trapped in Traffic During Shootout", "start": 990.0, "end": 1016.0, "score": 94},
    {"id": "15", "title": "PIT Maneuvered by 4 Police Cars Simultaneously", "start": 1062.0, "end": 1090.0, "score": 97},
    {"id": "16", "title": "Speed Steals a Sports Car from an NPC", "start": 1135.0, "end": 1160.0, "score": 95},
    {"id": "17", "title": "Jumping Car Off Parking Garage Roof", "start": 1210.0, "end": 1238.0, "score": 98},
    {"id": "18", "title": "Speed Drives on Sidewalk and Causes Pure Chaos", "start": 1285.0, "end": 1310.0, "score": 96},
    {"id": "19", "title": "Tire Pop at 120 MPH Highway Chase", "start": 1358.0, "end": 1384.0, "score": 95},
    {"id": "20", "title": "Speed Lands Car Inside a Swimming Pool", "start": 1430.0, "end": 1456.0, "score": 97},
]

print("=" * 70)
print(f"🚀 INITIALIZING PHASE 1 BATCH RENDERING (20 CLIPS)")
print(f"Source: {SOURCE_VIDEO}")
print(f"Target Directory: {OUTPUT_DIR}")
print("=" * 70)

print("\n[1/3] Loading Whisper transcription model...")
model = faster_whisper.WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4)
style_cfg = replace(PRESET_STYLES["viral_yellow"], margin_v=320, font_size=84, outline_width=5.0)

manifest = []
start_all_time = time.time()

for idx, clip in enumerate(PHASE_01_CLIPS, 1):
    c_id = clip["id"]
    title = clip["title"]
    start_sec = clip["start"]
    end_sec = clip["end"]
    duration = end_sec - start_sec
    
    clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()
    out_name = f"Speed_GTA6_Clip_{c_id}_{clean_title.replace(' ', '_')}.mp4"
    out_video_path = OUTPUT_DIR / out_name
    thumb_path = OUTPUT_DIR / f"thumb_{c_id}.jpg"
    
    print(f"\n🎬 [{idx}/20] Processing Clip {c_id}: '{title}' ({start_sec:.1f}s - {end_sec:.1f}s | {duration:.1f}s)")
    
    t0 = time.time()
    
    if out_video_path.exists() and out_video_path.stat().st_size > 1_000_000 and thumb_path.exists():
        print(f"   ⏩ Already rendered ({out_video_path.stat().st_size / (1024*1024):.1f} MB). Skipping.")
        manifest.append({
            "id": c_id,
            "title": title,
            "video_file": str(out_video_path).replace("\\", "/"),
            "thumbnail": str(thumb_path).replace("\\", "/"),
            "start": start_sec,
            "end": end_sec,
            "duration": duration,
            "score": clip["score"]
        })
        continue
    
    # Step A: Extract clip audio
    audio_wav = TEMP_DIR / f"clip_{c_id}.wav"
    cmd_audio = [
        "ffmpeg", "-y", "-nostdin",
        "-ss", str(start_sec),
        "-t", str(duration),
        "-i", SOURCE_VIDEO,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(audio_wav)
    ]
    subprocess.run(cmd_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # Step B: Transcribe audio
    with wave.open(str(audio_wav), "rb") as wf:
        audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    
    segments, _ = model.transcribe(audio_data, language="en", word_timestamps=True)
    words = []
    for s in segments:
        for w in s.words:
            w_text = w.word.strip()
            if w_text:
                words.append({"word": w_text, "start": round(w.start, 2), "end": round(w.end, 2)})
    
    # Step C: Compile ASS karaoke subtitles
    ass_path = TEMP_DIR / f"subs_{c_id}.ass"
    ass_content = compile_ass_subtitles(words, style=style_cfg, clip_offset=0.0)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    
    # Step D: Render 1080x1920 60FPS Video with Intel QuickSync
    # Note: subtitles filter path must escape colons and backslashes for FFmpeg
    escaped_ass = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    
    # Perfect 1:1 Aspect Ratio (No Stretch) + Clarity & Contrast Enhancements
    filter_graph = (
        f"[0:v]crop=330:220:25:440,scale=1080:720,unsharp=5:5:0.8:5:5:0.0[top_cam];"
        f"[0:v]crop=972:1080:550:0,scale=1080:1200,unsharp=5:5:1.0:5:5:0.0,eq=contrast=1.07:brightness=0.01:saturation=1.20[bot_game];"
        f"[top_cam][bot_game]vstack=inputs=2,subtitles='{escaped_ass}'[v_out];"
        f"[0:a]loudnorm=I=-16[a_out]"
    )
    
    cmd_render = [
        "ffmpeg", "-y", "-nostdin",
        "-ss", str(start_sec),
        "-t", str(duration),
        "-i", SOURCE_VIDEO,
        "-filter_complex", filter_graph,
        "-map", "[v_out]", "-map", "[a_out]",
        "-c:v", "h264_qsv", "-b:v", "6200k",
        "-c:a", "aac", "-b:a", "192k",
        str(out_video_path)
    ]
    
    res = subprocess.run(cmd_render, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        # Fallback to libx264 if hardware encoder reports error
        print("   ⚠️ QSV fallback to libx264...")
        cmd_render[cmd_render.index("h264_qsv")] = "libx264"
        cmd_render[cmd_render.index("-b:v")] = "-crf"
        cmd_render[cmd_render.index("6200k")] = "20"
        subprocess.run(cmd_render, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # Step E: Generate preview thumbnail
    cmd_thumb = [
        "ffmpeg", "-y", "-nostdin",
        "-ss", "3.0",
        "-i", str(out_video_path),
        "-frames:v", "1", "-q:v", "2",
        str(thumb_path)
    ]
    subprocess.run(cmd_thumb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    elapsed = time.time() - t0
    fsize_mb = out_video_path.stat().st_size / (1024 * 1024) if out_video_path.exists() else 0
    print(f"   ✅ Done in {elapsed:.1f}s | Size: {fsize_mb:.1f} MB | Words: {len(words)}")
    
    manifest.append({
        "id": c_id,
        "title": title,
        "video_file": str(out_video_path).replace("\\", "/"),
        "thumbnail": str(thumb_path).replace("\\", "/"),
        "start": start_sec,
        "end": end_sec,
        "duration": duration,
        "score": clip["score"]
    })

# Save manifest
manifest_path = OUTPUT_DIR / "phase_01_manifest.json"
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

total_elapsed = time.time() - start_all_time
print("\n" + "=" * 70)
print(f"🎉 PHASE 1 COMPLETE! 20/20 CLIPS RENDERED IN {total_elapsed/60:.1f} MINUTES")
print(f"Manifest: {manifest_path}")
print("=" * 70)
