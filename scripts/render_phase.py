"""AI CLIPPING STUDIO: Universal Multi-Phase Video Batch Renderer
Optimized for Local PC, Kaggle GPU (T4 x2), and Cloud VM Environments.
Supports all 5 Phases (100 Clips) with Auto-Hardware Detection (CUDA/QSV/CPU).
"""
import os
import sys
import time
import json
import wave
import argparse
import subprocess
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, os.path.abspath("src"))
from captions.compiler import compile_ass_subtitles
from captions.styles import PRESET_STYLES
from dataclasses import replace
import faster_whisper

# 100 Clips Blueprint Partitioned into 5 Phases
ALL_PHASES = {
    1: [
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
    ],
    2: [
        {"id": "21", "title": "Speed Barks at Screen After Dying Instantly", "start": 165.0, "end": 188.0, "score": 99},
        {"id": "22", "title": "Desk Slam After Failing Simple Driving Mission", "start": 228.0, "end": 252.0, "score": 97},
        {"id": "23", "title": "HOW DID HE SHOOT ME Ultimate Voice Crack", "start": 310.0, "end": 335.0, "score": 96},
        {"id": "24", "title": "Speed Screaming at GTA 6 GPS Directions", "start": 450.0, "end": 475.0, "score": 94},
        {"id": "25", "title": "Speed Rages at Chat for Trolling Coordinates", "start": 525.0, "end": 550.0, "score": 95},
        {"id": "26", "title": "Headset Throw After Getting Busted by Cops", "start": 600.0, "end": 624.0, "score": 98},
        {"id": "27", "title": "Speed Tries to Speak Spanish to Miami NPC", "start": 665.0, "end": 690.0, "score": 98},
        {"id": "28", "title": "High-Pitched Scream When Car Blows Up", "start": 735.0, "end": 760.0, "score": 96},
        {"id": "29", "title": "Speed Roasts the GTA 6 Main Character", "start": 805.0, "end": 832.0, "score": 95},
        {"id": "30", "title": "I AM NOT PLAYING THIS GAME ANYMORE", "start": 880.0, "end": 908.0, "score": 99},
        {"id": "31", "title": "Speed Barks Aggressively at Dog NPC in Alley", "start": 950.0, "end": 975.0, "score": 99},
        {"id": "32", "title": "Controller Almost Snapped in Half", "start": 1025.0, "end": 1050.0, "score": 97},
        {"id": "33", "title": "Speed Threatens to Call Rockstar Games Support", "start": 1100.0, "end": 1126.0, "score": 96},
        {"id": "34", "title": "Speed Reacts to In-Game Radio Station Song", "start": 1175.0, "end": 1202.0, "score": 94},
        {"id": "35", "title": "Chair Flip After Getting Sniped Out of Nowhere", "start": 1248.0, "end": 1272.0, "score": 98},
        {"id": "36", "title": "Speed Crying Tears of Rage After 10th Death", "start": 1320.0, "end": 1346.0, "score": 97},
        {"id": "37", "title": "Speed Argues With Siri While Playing GTA", "start": 1395.0, "end": 1422.0, "score": 95},
        {"id": "38", "title": "Barking Duet with Chat Donation Sound", "start": 1470.0, "end": 1495.0, "score": 96},
        {"id": "39", "title": "WHO PROGRAMMED THIS AI Crash Rage", "start": 1540.0, "end": 1566.0, "score": 95},
        {"id": "40", "title": "Speed Does Backflip in Room After Survived Chase", "start": 1610.0, "end": 1638.0, "score": 99},
    ],
    3: [
        {"id": "41", "title": "Speed Arrives at Vice City Beach for First Time", "start": 110.0, "end": 138.0, "score": 99},
        {"id": "42", "title": "Speed Tries to Pick Up an NPC on the Boardwalk", "start": 200.0, "end": 226.0, "score": 98},
        {"id": "43", "title": "Bodybuilder NPC Knocks Speed Out Cold", "start": 295.0, "end": 322.0, "score": 99},
        {"id": "44", "title": "Speed Punches a Skateboarder and Regrets It", "start": 375.0, "end": 400.0, "score": 95},
        {"id": "45", "title": "Speed Steals Beach Umbrella and Weapons It", "start": 460.0, "end": 485.0, "score": 94},
        {"id": "46", "title": "NPC Calls Speed Broke in Miami Accent", "start": 540.0, "end": 565.0, "score": 97},
        {"id": "47", "title": "Speed Challenges Entire Beach Volleyball Team", "start": 630.0, "end": 656.0, "score": 96},
        {"id": "48", "title": "Lifeguard Tackles Speed Into Ocean Waves", "start": 705.0, "end": 732.0, "score": 97},
        {"id": "49", "title": "Speed Encounters an Alligator on Vice City Beach", "start": 780.0, "end": 808.0, "score": 100},
        {"id": "50", "title": "Speed Tries to Enter Strip Club & Bouncer Refuses", "start": 855.0, "end": 882.0, "score": 98},
        {"id": "51", "title": "Grandma NPC Pulls Out a Weapon on Speed", "start": 930.0, "end": 955.0, "score": 99},
        {"id": "52", "title": "Speed Stares at Beach NPC Graphics in Disbelief", "start": 1005.0, "end": 1030.0, "score": 96},
        {"id": "53", "title": "Speed Tries to Rollerblade Down the Pier", "start": 1080.0, "end": 1105.0, "score": 93},
        {"id": "54", "title": "Accidental 1-Hit Knockout by Security Guard", "start": 1155.0, "end": 1180.0, "score": 97},
        {"id": "55", "title": "Speed Steals a Jet Ski and Does Sick Flips", "start": 1225.0, "end": 1252.0, "score": 95},
        {"id": "56", "title": "Speed Starts Massive 20-Person Street Brawl", "start": 1300.0, "end": 1328.0, "score": 98},
        {"id": "57", "title": "Speed Trolls Vice City Taxi Driver with No Fare", "start": 1375.0, "end": 1402.0, "score": 96},
        {"id": "58", "title": "Police Horse Scares Speed to Death", "start": 1450.0, "end": 1475.0, "score": 97},
        {"id": "59", "title": "Speed Tries to Rob a Convenience Store & Fails", "start": 1520.0, "end": 1548.0, "score": 98},
        {"id": "60", "title": "Speed Gets Run Over by His Own Stolen Car", "start": 1590.0, "end": 1615.0, "score": 99},
    ],
    4: [
        {"id": "61", "title": "Speed Triggers 5-Star Wanted Level Instantly", "start": 145.0, "end": 172.0, "score": 99},
        {"id": "62", "title": "SWAT Truck Rams Speeds Car into a Building", "start": 215.0, "end": 242.0, "score": 97},
        {"id": "63", "title": "Speed Hides in a Dumpster to Escape the Cops", "start": 280.0, "end": 306.0, "score": 98},
        {"id": "64", "title": "Police Helicopter Spotlight Blind Speed", "start": 355.0, "end": 382.0, "score": 95},
        {"id": "65", "title": "RPG vs Police Cruiser Epic Explosion", "start": 430.0, "end": 458.0, "score": 98},
        {"id": "66", "title": "Speed Trapped on a Rooftop With 1 Health Bar", "start": 505.0, "end": 532.0, "score": 97},
        {"id": "67", "title": "Speed Base Jumps Off Skyscraper to Escape Cops", "start": 580.0, "end": 608.0, "score": 99},
        {"id": "68", "title": "Parachute Fails to Open in Mid-Air", "start": 610.0, "end": 634.0, "score": 100},
        {"id": "69", "title": "Speed Snipes Police Pilot Out of the Sky", "start": 680.0, "end": 706.0, "score": 98},
        {"id": "70", "title": "Underground Subway Shootout Last Stand", "start": 755.0, "end": 782.0, "score": 96},
        {"id": "71", "title": "Speed Steals an Armored Bank Van", "start": 828.0, "end": 855.0, "score": 95},
        {"id": "72", "title": "Police Spikestrip Shreds All 4 Tires", "start": 902.0, "end": 928.0, "score": 96},
        {"id": "73", "title": "Speed Surrenders to Cops and Then Sucker Punches", "start": 978.0, "end": 1005.0, "score": 98},
        {"id": "74", "title": "Military Tank Spawns in Front of Speed", "start": 1052.0, "end": 1080.0, "score": 99},
        {"id": "75", "title": "Speed Runs on Foot Through Airport Runway", "start": 1125.0, "end": 1152.0, "score": 97},
        {"id": "76", "title": "Speed Gets Sucked Into a Jet Engine", "start": 1155.0, "end": 1178.0, "score": 100},
        {"id": "77", "title": "Speed Hides Behind Billboard While 10 Cops Pass", "start": 1230.0, "end": 1256.0, "score": 96},
        {"id": "78", "title": "Speed Swims Across Bay to Lose 4 Stars", "start": 1312.0, "end": 1340.0, "score": 94},
        {"id": "79", "title": "Shark Attacks Speed While Escaping Police", "start": 1342.0, "end": 1370.0, "score": 100},
        {"id": "80", "title": "Ultimate 5-Star Escape with 0.1s Left on Timer", "start": 1415.0, "end": 1445.0, "score": 99},
    ],
    5: [
        {"id": "81", "title": "Speed First Sees GTA 6 Sunset & Mind is Blown", "start": 45.0, "end": 72.0, "score": 98},
        {"id": "82", "title": "LOOK AT THE WATER GRAPHICS CHAT", "start": 175.0, "end": 202.0, "score": 96},
        {"id": "83", "title": "Car Glitches into Ground and Launches into Sky", "start": 245.0, "end": 272.0, "score": 99},
        {"id": "84", "title": "Speed Discovers Mud Physics in Everglades", "start": 325.0, "end": 352.0, "score": 95},
        {"id": "85", "title": "NPC T-Pose Glitch Scares Speed", "start": 395.0, "end": 420.0, "score": 97},
        {"id": "86", "title": "Speed Finds Ronaldo Poster in Miami Apartment", "start": 470.0, "end": 498.0, "score": 100},
        {"id": "87", "title": "Speed Does SIUUU Celebration in GTA 6", "start": 500.0, "end": 525.0, "score": 100},
        {"id": "88", "title": "GTA 6 Hair Physics Leaves Speed Speechless", "start": 565.0, "end": 590.0, "score": 94},
        {"id": "89", "title": "Speed Shoots at Glass & Cant Believe Destruction", "start": 645.0, "end": 672.0, "score": 95},
        {"id": "90", "title": "Speed Tries to Rob Bank With Finger Guns", "start": 720.0, "end": 746.0, "score": 98},
        {"id": "91", "title": "Car Drives on Two Wheels Down Highway", "start": 795.0, "end": 820.0, "score": 96},
        {"id": "92", "title": "Speed Gets Trapped Inside Changing Room", "start": 870.0, "end": 895.0, "score": 97},
        {"id": "93", "title": "Infinite Falling Through Map Glitch", "start": 945.0, "end": 972.0, "score": 99},
        {"id": "94", "title": "Speed Tests Fall Damage From Top of Lighthouse", "start": 1035.0, "end": 1060.0, "score": 98},
        {"id": "95", "title": "Speed Reacts to Female Protagonist Lucia", "start": 1110.0, "end": 1138.0, "score": 99},
        {"id": "96", "title": "Driving Invisible Car Glitch in Vice City", "start": 1188.0, "end": 1215.0, "score": 98},
        {"id": "97", "title": "Speed Tries to Fly Boeing 747 Under Low Bridge", "start": 1265.0, "end": 1295.0, "score": 99},
        {"id": "98", "title": "Speed Finds a Secret Underground Tunnel", "start": 1335.0, "end": 1362.0, "score": 95},
        {"id": "99", "title": "Speed Accidental 720 Barrel Roll Car Landing", "start": 1400.0, "end": 1428.0, "score": 97},
        {"id": "100", "title": "Speed Final Rating of GTA 6 & Emotional Speech", "start": 2030.0, "end": 2070.0, "score": 99},
    ]
}

SOURCE_VIDEO_DEFAULT = "workspace_temp/downloads/IShowSpeed_GTA6_1080p.mp4"
YT_STREAM_URL = "https://www.youtube.com/watch?v=kR8bhkVAgBY"

def detect_hardware():
    """Detect GPU / Hardware Acceleration capabilities."""
    has_cuda = False
    try:
        import torch
        has_cuda = torch.cuda.is_available()
    except Exception:
        pass
    
    # Check FFmpeg encoders
    try:
        res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True)
        out = res.stdout
    except Exception:
        out = ""
    
    has_nvenc = "h264_nvenc" in out
    has_qsv = "h264_qsv" in out
    
    if has_cuda and has_nvenc:
        return "cuda", "h264_nvenc", "Nvidia GPU (CUDA + NVENC)"
    elif has_qsv:
        return "cpu", "h264_qsv", "Intel QuickSync (QSV)"
    elif has_cuda:
        return "cuda", "libx264", "Nvidia GPU (CUDA Whisper) + CPU FFmpeg"
    else:
        return "cpu", "libx264", "CPU Mode (Standard)"

def ensure_source_video(source_path):
    p = Path(source_path)
    if p.exists() and p.stat().st_size > 10_000_000:
        return str(p)
    
    print(f"📥 Source video not found locally. Downloading 1080p stream from YouTube...")
    p.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format", "mp4",
        "-o", str(p),
        YT_STREAM_URL
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Source video ready: {p} ({p.stat().st_size / (1024*1024):.1f} MB)")
    return str(p)

def main():
    parser = argparse.ArgumentParser(description="Render clips in 20-clip phases.")
    parser.add_argument("--phase", type=int, default=2, choices=[1, 2, 3, 4, 5], help="Phase number to render (1-5)")
    parser.add_argument("--source", type=str, default=SOURCE_VIDEO_DEFAULT, help="Path to source video")
    args = parser.parse_args()

    phase_num = args.phase
    clips = ALL_PHASES[phase_num]

    device, vcodec, hw_label = detect_hardware()
    out_dir = Path(f"output_clips/IShowSpeed_GTA6/Phase_{phase_num:02d}")
    temp_dir = Path(f"workspace_temp/phase_{phase_num:02d}")
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"🎬 AI CLIPPING STUDIO: PHASE {phase_num} (Clips {clips[0]['id']} - {clips[-1]['id']})")
    print(f"🖥️ Hardware Detected: {hw_label}")
    print(f"📁 Target Output: {out_dir}")
    print("=" * 70)

    source_path = ensure_source_video(args.source)

    # Initialize Whisper
    compute_type = "float16" if device == "cuda" else "int8"
    print(f"\n[1/2] Loading Whisper model on {device.upper()} ({compute_type})...")
    model = faster_whisper.WhisperModel("base", device=device, compute_type=compute_type, cpu_threads=4)
    style_cfg = replace(PRESET_STYLES["viral_yellow"], margin_v=320, font_size=84, outline_width=5.0)

    manifest = []
    t_start_all = time.time()

    for idx, clip in enumerate(clips, 1):
        c_id = clip["id"]
        title = clip["title"]
        start_sec = clip["start"]
        end_sec = clip["end"]
        duration = end_sec - start_sec

        clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()
        out_name = f"Speed_GTA6_Clip_{c_id}_{clean_title.replace(' ', '_')}.mp4"
        out_video_path = out_dir / out_name
        thumb_path = out_dir / f"thumb_{c_id}.jpg"

        print(f"\n[{idx}/20] Clip {c_id}: '{title}' ({start_sec:.1f}s - {end_sec:.1f}s | {duration:.1f}s)")
        t0 = time.time()

        if out_video_path.exists() and out_video_path.stat().st_size > 1_000_000 and thumb_path.exists():
            print(f"   ⏩ Already rendered. Skipping.")
            manifest.append({
                "id": c_id, "title": title, "video_file": str(out_video_path).replace("\\", "/"),
                "thumbnail": str(thumb_path).replace("\\", "/"), "start": start_sec, "end": end_sec,
                "duration": duration, "score": clip["score"]
            })
            continue

        # Extract audio
        audio_wav = temp_dir / f"clip_{c_id}.wav"
        subprocess.run([
            "ffmpeg", "-y", "-nostdin", "-ss", str(start_sec), "-t", str(duration),
            "-i", source_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            str(audio_wav)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Transcribe
        with wave.open(str(audio_wav), "rb") as wf:
            audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

        segments, _ = model.transcribe(audio_data, language="en", word_timestamps=True)
        words = []
        for s in segments:
            for w in s.words:
                w_text = w.word.strip()
                if w_text:
                    words.append({"word": w_text, "start": round(w.start, 2), "end": round(w.end, 2)})

        # Subtitles
        ass_path = temp_dir / f"subs_{c_id}.ass"
        ass_content = compile_ass_subtitles(words, style=style_cfg, clip_offset=0.0)
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

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
            "-ss", str(start_sec), "-t", str(duration),
            "-i", source_path,
            "-filter_complex", filter_graph,
            "-map", "[v_out]", "-map", "[a_out]",
            "-c:v", vcodec, "-b:v", "6200k",
            "-c:a", "aac", "-b:a", "192k",
            str(out_video_path)
        ]

        res = subprocess.run(cmd_render, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            cmd_render[cmd_render.index(vcodec)] = "libx264"
            cmd_render[cmd_render.index("-b:v")] = "-preset"
            cmd_render[cmd_render.index("6200k")] = "veryfast"
            subprocess.run(cmd_render, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Thumbnail
        subprocess.run([
            "ffmpeg", "-y", "-nostdin", "-ss", "3.0", "-i", str(out_video_path),
            "-frames:v", "1", "-q:v", "2", str(thumb_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        elapsed = time.time() - t0
        fsize = out_video_path.stat().st_size / (1024*1024) if out_video_path.exists() else 0
        print(f"   ✅ Done in {elapsed:.1f}s | Size: {fsize:.1f} MB | Words: {len(words)}")

        manifest.append({
            "id": c_id, "title": title, "video_file": str(out_video_path).replace("\\", "/"),
            "thumbnail": str(thumb_path).replace("\\", "/"), "start": start_sec, "end": end_sec,
            "duration": duration, "score": clip["score"]
        })

    # Save manifest
    manifest_path = out_dir / f"phase_{phase_num:02d}_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    total_time = time.time() - t_start_all
    print("\n" + "=" * 70)
    print(f"🎉 PHASE {phase_num} COMPLETED! 20/20 CLIPS IN {total_time/60:.1f} MIN")
    print(f"📁 Manifest: {manifest_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()
