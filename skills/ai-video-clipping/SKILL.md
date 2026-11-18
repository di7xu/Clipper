---
name: ai-video-clipping
description: >-
  Universal AI Video Processing Environment and Autonomous Agent Skill.
  Transforms long-form videos (podcasts, interviews, gaming, webinars, lectures, talking-head videos)
  into publication-ready viral short-form clips (YouTube Shorts, TikTok, Instagram Reels, Square 1:1, Landscape highlights).
  Consolidates the best algorithms from Cutawan, Chopify, OpenShorts, SupoClip, Clips-Studio, and AutoClip.
  Operates 100% locally and offline with zero paid API dependencies.
---

# AI Video Processing Environment & Autonomous Agent Skill

Unified multimodal video processing toolkit and autonomous agent skill. Operates **100% locally and offline with zero external API dependencies**, consolidating the strongest algorithms from six open-source video processing repositories:

- **Chopify:** Lexical hook detection, speech energy scoring, and complete story arc validation.
- **Cutawan:** Local `faster-whisper` transcription with Silero VAD and CapCut-style ASS karaoke subtitles.
- **OpenShorts:** OpenCV YuNet ONNX face detection, smooth camera trajectory, split/inset layouts, and punch-in beats.
- **SupoClip:** Contextual B-roll cutaway composite overlays with alpha crossfades and multi-layout directing.
- **Clips-Studio:** Signal-level acoustic excitement profiling (loudness RMS, spike ratio, burst onset density).
- **AutoClip:** Media stream probing, container validation, and fault-tolerant video preflights.

---

## Capabilities & Architecture

```
src/
├── cli.py                    # Master CLI tool and autonomous execution engine
├── config.py                 # Cross-platform path resolver, hardware acceleration discovery
├── audio/                    # Acoustic signal excitement & energy analysis (Clips-Studio)
├── broll/                    # B-roll cutaway composite overlays with alpha crossfades (SupoClip)
├── captions/                 # Animated ASS karaoke subtitles & SRT exporters (Cutawan)
├── clip_detection/           # Multimodal heuristic virality brain (Chopify + Clips-Studio)
├── editor/                   # Declarative edit planning & speech tightening (Chopify + AutoClip)
├── export/                   # Social media viral packaging (.meta.json) for Shorts/TikTok/Reels
├── face_tracking/            # YuNet face tracking, smooth trajectory, punch-in beats (OpenShorts)
├── rendering/                # Hardware-accelerated GPU export (QSV/NVENC/libx264 + loudnorm)
├── transcription/            # Local faster-whisper + Silero VAD + CTranslate2 (Cutawan)
└── video/                    # Media probing, stream validation, scene cut detection (AutoClip)
```

1. **Video Ingest & Validation:**
   - Local files: `MP4`, `MOV`, `MKV`, `WEBM`, `AVI`, `M4V`
   - Public URLs: YouTube, Twitch, Vimeo (via bundled/updated `yt-dlp`)
2. **Local Speech-to-Text (`faster-whisper`):**
   - Millisecond word timestamps, token probabilities, and Silero VAD pre-filtering via CTranslate2
   - Direct PCM NumPy array streaming (100% PyAV compatibility)
3. **Multimodal Heuristic Scoring Brain (0 API Cost):**
   - Opening hook analysis (questions, curiosity gap, bold assertions)
   - Acoustic burst and volume spike detection
   - Guaranteed complete narrative arcs (strictly avoids cutting sentences mid-phrase)
4. **AI Speech Tightening:**
   - Prunes conversational filler words (`um`, `uh`, `you know`)
   - Trims awkward silence pauses $> 0.6$s and mathematically retimes subtitle timestamps
5. **Dynamic Reframing & Face Tracking:**
   - OpenCV YuNet ONNX face detector with exponential camera smoothing ($\alpha=0.12$)
   - Aspect ratios: `9:16` (Vertical), `1:1` (Square), `16:9` (Landscape)
   - Specialized layouts: Single Speaker, Split Reaction (stacked), and Screen + Webcam Inset
   - Focal punch-in zoom beats ($12\%$ push) on emphatic words
6. **B-Roll Cutaway Overlays:**
   - Seamlessly dissolves stock B-roll cutaways in and out over footage
   - Retains visible subtitles and hook titles over the cutaways
7. **Animated Karaoke Subtitles:**
   - Word-by-word active highlight styling compiled into native Advanced SubStation Alpha (`.ass`)
   - Pre-bundled viral typography (Anton, Poppins Bold, Archivo Black, Montserrat)
   - Style presets: `viral_yellow`, `clean_cyan`, `bold_coral`, `minimal_white`
8. **Hardware-Accelerated Render Engine:**
   - Automatic GPU encoder selection: Intel QuickSync (`h264_qsv`), NVIDIA NVENC (`h264_nvenc`), Apple VideoToolbox (`h264_videotoolbox`), or CPU `libx264`
   - Integrated EBU R128 loudness audio normalization (`loudnorm`)
9. **Social Media Metadata Generator:**
   - Generates companion `.meta.json` files with viral titles, hooks, descriptions, and hashtags

---

## Agent Usage & CLI Runbook

The master execution CLI is located at:
`c:\MyProject\Mycreate\Clipping\src\cli.py`

### 1. Clip a Local Video File (Default: Top 3 Vertical 9:16 Shorts)

```powershell
python "c:\MyProject\Mycreate\Clipping\src\cli.py" -i "path\to\video.mp4" -o "output_clips" -n 3 --aspect 9:16 --style viral_yellow
```

### 2. Clip a Public YouTube / Web Video Directly

```powershell
python "c:\MyProject\Mycreate\Clipping\src\cli.py" -u "https://www.youtube.com/watch?v=VIDEO_ID" -o "output_clips" -n 3
```

### 3. Clip with B-Roll Cutaway Insertion

```powershell
python "c:\MyProject\Mycreate\Clipping\src\cli.py" -i "interview.mp4" -b "stock_broll.mp4" -o "output_clips" -n 3
```

### 4. Podcast 2-Person Stacked Layout (Top-Bottom "Upar-Niche")

For interviews and 2-person podcasts, the split/stacked layout automatically detects both speakers (Host and Guest) and stacks them vertically (1080x960 each) into a 1080x1920 9:16 frame. This guarantees full visibility of both subjects without slicing faces or bodies in half:

```powershell
python "c:\MyProject\Mycreate\Clipping\src\cli.py" -i "podcast.mp4" -o "output_clips" --layout split --task translate
```

### 5. Antigravity Model Curated Clips (--clips-json)

Use the Antigravity LLM's superior context and YouTube knowledge to curate and confirm exact clip timestamps:

```powershell
python "c:\MyProject\Mycreate\Clipping\src\cli.py" -i "podcast.mp4" --clips-json "curated_clips.json" --layout auto --task translate
```

---

## CLI Options & Flags

| Flag | Long Option | Allowed Values | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-i` | `--input` | File path | None | Source video file path (MP4, MOV, MKV, etc.) |
| `-u` | `--url` | Web URL | None | Public video URL to download and process |
| `-o` | `--output` | Directory path | `output_clips/` | Destination directory for rendered MP4 clips and `.meta.json` |
| `-n` | `--count` | Integer | `3` | Number of top viral clips to extract and render |
| `-a` | `--aspect` | `9:16`, `1:1`, `16:9` | `9:16` | Output aspect ratio |
| `-s` | `--style` | `viral_yellow`, `clean_cyan`, `bold_coral`, `minimal_white` | `viral_yellow` | Caption karaoke style preset |
| `-l` | `--layout` | `auto`, `single`, `split`, `stacked` | `auto` | Framing layout: auto (detects podcast 2-speakers), single (centered), or split/stacked (top-bottom) |
| `-t` | `--task` | `translate`, `transcribe` | `translate` | Whisper task: translate (translates foreign speech to clean English) or transcribe |
| | `--lang` | Language code (e.g. `hi`) | None | Source spoken language code (default: auto-detect) |
| | `--clips-json` | Path or JSON string | None | Path or JSON string of model-curated clips `[{start, end, title}]` |
| `-m` | `--model` | `tiny`, `base`, `small`, `medium` | `base` | Local `faster-whisper` model size |
| `-p` | `--platform`| `youtube_shorts`, `tiktok`, `instagram_reels` | `youtube_shorts` | Social metadata platform preset |
| `-b` | `--broll` | File path | None | Optional stock B-roll cutaway video file to overlay |
| | `--no-tighten` | Flag | False | Disable filler word and silence trimming |
| | `--no-captions`| Flag | False | Disable burned-in animated karaoke subtitles |

---

## Output Artifacts

For each rendered clip, the toolkit generates:
1. `<video_name>_<clip_id>_<aspect>.mp4`: Production-ready vertical/square clip with face-tracked reframing, loudnorm audio, and burned-in karaoke subtitles.
2. `<video_name>_<clip_id>_<aspect>.meta.json`: Ready-to-post metadata package with viral title, hook opening line, video description, and hashtags.
3. `<video_name>_transcript.json`: Cached word-level Whisper transcript for instant reuse.
