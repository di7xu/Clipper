# REPOSITORY AUDIT: AI VIDEO CLIPPING STUDIO
**Document Version:** 1.0  
**Date:** November 2026  
**Auditor:** Senior Software Architect & AI/ML Systems Engineer  
**Scope:** Deep Technical Audit of Six Open-Source Video Clipping Repositories

---

## 1. Executive Summary

This document presents a comprehensive, code-level technical audit of six open-source repositories evaluated for the construction of **AI CLIPPING STUDIO** ("One Video. Multiple Stories. Powered by AI.").

| Repository | Origin / Maintainer | Primary Language / Stack | Stated License | Code-Verified License Status | Architectural Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cutawan** | JeremySNR / Cutawan Contributors | TypeScript, Electron, React, ONNX | MIT | **Permissive MIT** | Primary Desktop Shell, Timeline Editor & ONNX ASD/VAD Pipeline |
| **Chopify** | Mehbul Islam | Python 3, FFmpeg, OpenCV, NumPy | MIT | **Permissive MIT** | Core Python Audio/Visual Evidence & Fast Dynamic ASS Rendering |
| **OpenShorts** | mutonby / OpenShorts | Python 3, PySceneDetect, FFmpeg, MediaPipe | MIT | **Permissive MIT** | Multimodal Layouts (Split, Camera Inset, Punch-In) & Reframe v2 |
| **AutoClip** | zhouxiaoka / AutoClip Team | Python (FastAPI/Celery), React, Tauri | MIT | **Permissive MIT** | Project/Task Data Models, Multi-step Outline & Scoring Pipeline |
| **Clips Studio** | ColinGPT9 (Clips Kitty) | Python 3, FastAPI, PyTorch, YOLO | GNU AGPL-3.0 | **Strong Copyleft (AGPL-3.0)** | Architectural Reference Only (Do Not Vendor - Prevents AGPL Infection) |
| **SupoClip** | Shiori LLC | Python (FastAPI), Next.js, Prisma | SupoClip Noncommercial | **Proprietary / Noncommercial** | Architectural Reference Only (Do Not Vendor - Prevents NC Infection) |

---

## 2. In-Depth Audit: Cutawan

### 2.1 Project Overview & Repository Identity
- **Repository URL:** `https://github.com/JeremySNR/cutawan.git`
- **Target Audience:** Desktop video creators, podcasters, clipping operators.
- **Commit History & Maturity:** Active 2026 release cycle (v0.14.0), highly disciplined modular structure.

### 2.2 Legal & Licensing Verification
- **License File:** `LICENSE` (MIT License, Copyright 2026 Cutawan Contributors).
- **Bundled Models & Weights:**
  - `face-detection-yunet.onnx` (YuNet, MIT License).
  - `silero-vad.onnx` (Silero VAD, MIT License).
  - `ultraface-rfb-320.onnx` (UltraFace, MIT License).
  - `lr-asd-frontend.onnx` & `lr-asd-backend.onnx` (Lightweight Active Speaker Detection ONNX models).
- **Bundled Fonts:** `Anton-Regular.ttf`, `Poppins-Bold.ttf`, `Poppins-Medium.ttf` (SIL Open Font License 1.1).
- **License Verdict:** **100% Permissive (MIT + OFL). Clean for reuse.**

### 2.3 Dependencies & Build Systems
- **Package Manager:** `npm` / `package.json`.
- **Core Runtime Dependencies:**
  - `electron`: v33+ runtime.
  - `onnxruntime-node`: v1.20+ for native high-performance model inference.
  - `ffmpeg-static` & `@ffprobe-installer/ffprobe`: bundled cross-platform multimedia binaries.
- **Frontend Dependencies:**
  - `react`: 19.x, `react-dom`.
  - `@tailwindcss/vite`: Tailwind CSS v4 styling.
  - `lucide-react`: Modern icon suite.
  - `electron-vite`: Lightning-fast HMR and bundling.

### 2.4 Architecture & Folder Structure
```
cutawan/
├── electron.vite.config.ts
├── package.json
├── resources/
│   ├── fonts/           # Anton, Poppins (OFL)
│   ├── local-whisper/   # Standalone Python faster-whisper runner
│   └── models/          # ONNX: YuNet, Silero VAD, ASD, UltraFace
├── src/
│   ├── main/
│   │   ├── index.ts     # Electron main lifecycle & window management
│   │   ├── ipc.ts       # Typed IPC handlers (projects, media, inference)
│   │   ├── localWhisper.ts # Local whisper process controller
│   │   ├── inference/   # Worker thread ONNX inference protocol
│   │   └── pipeline/    # 35+ pipeline stages (vad, faces, reframe, captions)
│   ├── preload/         # Context isolation bridge
│   ├── renderer/        # React 19 UI
│   │   └── src/components/ (TimelineEditor, PreviewPlayer, CompositionControls, etc.)
│   └── shared/          # Universal types, layout math, camera paths, ranking
```

### 2.5 Video Processing Pipeline
- **FFmpeg Integration:** Uses `fluent-ffmpeg` / custom child process executor (`src/main/pipeline/ffmpeg.ts`).
- **Decoder/Encoder Support:** Auto-detects hardware acceleration:
  - NVIDIA NVENC (`h264_nvenc`)
  - Apple VideoToolbox (`h264_videotoolbox`)
  - Intel QuickSync (`h264_qsv`)
  - Software fallback (`libx264`)
- **Pipeline Stages:**
  1. Ingest & FFprobe metadata extraction (width, height, fps, SAR, sample rate).
  2. Audio extraction (16kHz mono WAV) for transcription & VAD.
  3. Video probe & low-resolution proxy generation for analysis.
  4. Face detection & active speaker track generation.
  5. Multi-aspect ratio reframing (9:16 vertical, 1:1 square, 16:9 landscape).

### 2.6 AI Models & Inference
- **Local ONNX Inference Engine:** Executed off-thread in a dedicated Node.js worker (`src/main/inference/worker.ts`) using `onnxruntime-node`.
- **Models Utilized:**
  - `silero-vad.onnx`: Millisecond-precision voice activity detection.
  - `face-detection-yunet.onnx`: Fast, accurate 5-point landmark face detector.
  - `lr-asd`: Lightweight Lip-sync / Audio-Visual Active Speaker Detector.

### 2.7 Transcription Engine
- **Engine:** `faster-whisper` run via embedded Python script (`resources/local-whisper/transcribe.py`).
- **Word Timestamps:** Extracts exact start/end timestamps and confidence per word.
- **Sentence Grouping:** Natural pause segmentation via `src/shared/sentences.ts`.
- **Cloud Fallback:** Optional OpenRouter / OpenAI API client (`src/main/openrouter.ts`).

### 2.8 Caption Generation & Subtitling
- **Implementation:** `src/main/pipeline/captions.ts` & `src/shared/captionLayout.ts`.
- **Format:** Compiles into Advanced SubStation Alpha (`.ass`) with font metrics, word-by-word animation styles, and karaoke tags (`\k`).
- **Font Rendering:** Injected into FFmpeg using `subtitles` filter with font directory registration.

### 2.9 Face Tracking & Auto-Reframing
- **Algorithm:**
  - Detects faces with YuNet across downsampled frames.
  - Builds temporal face tracks (`facetracks.ts`) by IOU matching and landmark distance.
  - Identifies active speaker via lip motion and audio correlation (`asd.ts`).
  - Computes smooth camera pan/zoom using a PID-damped trajectory (`cameraPath.ts`) preventing jarring camera shakes.

### 2.10 Built-in Video Editor & UI
- **Components:**
  - `TimelineEditor.tsx`: Multi-track timeline displaying audio waveform, video strips, and caption segments.
  - `PreviewPlayer.tsx`: HTML5 Canvas / Video preview synchronized with timeline playback.
  - `TranscriptEditor.tsx`: In-place transcript word correction with instant subtitle update.
  - `CompositionControls.tsx`: Aspect ratio, crop position, and zoom toggles.

### 2.11 Reusable Components & Assessment
- **Top Reusable Assets:**
  - Complete Electron + Vite + React desktop scaffold.
  - ONNX inference worker and model files (`yunet.onnx`, `silero-vad.onnx`).
  - Timeline editor and waveform preview React components.
  - ASS subtitle styling and layout math.
  - Multi-encoder FFmpeg rendering pipeline.

---

## 3. In-Depth Audit: Chopify

### 3.1 Project Overview & Repository Identity
- **Repository URL:** `https://github.com/mehbul/chopify.git`
- **Target Audience:** Content creators seeking fast, zero-cost, local-first clipping CLI and dashboard.
- **Code-Verified Philosophy:** Pure Python, zero paid APIs, deterministic heuristics + optional local Ollama LLM.

### 3.2 Legal & Licensing Verification
- **License File:** `LICENSE` (MIT License, Copyright 2026 Mehbul Islam).
- **License Verdict:** **100% Permissive MIT. Fully clean for reuse.**

### 3.3 Dependencies & Requirements
- **Requirements:** Extremely lean (`yt-dlp`, `faster-whisper`, `opencv-python`, `numpy`).
- **Native Tools:** Requires system `ffmpeg`.

### 3.4 Architecture & Folder Structure
```
chopify/
├── branding.py          # Brand presets (colors, logos, font templates)
├── captions.py          # Transcript validation & SRT export
├── chopify.py           # CLI orchestrator & argument parsing
├── dashboard.py         # Local web UI server
├── download_and_transcribe.py # yt-dlp & faster-whisper ingest
├── evidence.py          # 16kHz audio FFT energy, flux & silence analysis
├── ingest.py            # Local file verification & audio extraction
├── projects.py          # Manifest storage & workspace state
├── render_clips.py      # 34KB FFmpeg ASS render & YuNet speaker crop
├── score_clips.py       # 77KB Built-in heuristic scoring brain
├── sections.py          # Topic & chapter boundary detection
├── semantic.py          # Local Ollama semantic re-ranking
├── tighten.py           # Filler word & silence removal algorithm
└── visual.py            # 28KB frame-difference motion & scene change
```

### 3.5 Video Processing Pipeline
- **Implementation:** `render_clips.py` executes native FFmpeg filtergraphs directly.
- **Reframing:** Dynamic speaker crop using OpenCV YuNet (`cv2.FaceDetectorYN`) with snap-on-cut and exponential smoothing.
- **Audio Normalization:** Implements two-pass `loudnorm` (`I=-16, LRA=11, TP=-1.5`).

### 3.6 Clip Scoring & Multimodal Intelligence ("The Brain")
- **Implementation:** `score_clips.py` (1,753 lines of pure algorithmic intelligence).
- **Audio Evidence (`evidence.py`):**
  - Resamples mono 16kHz audio.
  - Computes 50ms spectral flux (Hanning window + FFT) and RMS energy.
  - Caches timeline as `audio_features.npz`.
- **Visual Evidence (`visual.py`):**
  - Decodes frames at 2 fps (160x90).
  - Calculates frame-to-frame pixel delta for motion energy.
  - Detects cuts, UI/slide changes, and face motion.
- **Transcript Heuristics:**
  - Energy scoring (words-per-second acceleration).
  - Lexical cue matching: hook words, shock/surprise, humor, controversy, actionable insights.
  - Story arc completion: guarantees clips do not start or end mid-sentence.
- **Optional Local LLM:** Re-ranks candidates via local Ollama (`qwen2.5:7b`, `llama3.2`) without shifting timestamps; graceful fallback if Ollama is absent.

### 3.7 AI Editing & Tightening
- **Implementation:** `tighten.py`.
- **Filler Word Elimination:** Identifies filler tokens (`um`, `uh`, `you know`, `i mean`).
- **Silence Pruning:** Prunes gaps > 0.6 seconds while retaining 150ms natural speech buffer.
- **Timestamp Retiming:** Mathematically shifts all subsequent word timestamps so rendered ASS subtitles maintain sub-frame synchronization.

### 3.8 Reusable Components & Assessment
- **Top Reusable Assets:**
  - Complete multimodal scoring engine (`score_clips.py`, `evidence.py`, `visual.py`).
  - Precision filler and silence removal algorithm (`tighten.py`).
  - CapCut-style animated ASS subtitle builder.
  - Social media metadata generator (titles, descriptions, hashtags in `.meta.json`).

---

## 4. In-Depth Audit: OpenShorts

### 4.1 Project Overview & Repository Identity
- **Repository URL:** `https://github.com/mutonby/openshorts.git`
- **Target Audience:** Creators, stream clippers, and podcast editors.
- **Code Highlights:** Specialized video layouts (split-screen, camera insets, punch-ins), TransNetV2 shot detection, GPU acceleration.

### 4.2 Legal & Licensing Verification
- **License File:** `LICENSE` (MIT License, Copyright 2024 OpenShorts).
- **NOTICE File:** `NOTICE` (Preserves MIT core notice).
- **Fonts:** Bundled OFL fonts (`Anton`, `ArchivoBlack`, `Montserrat`, `NotoSerif`).
- **License Verdict:** **100% Permissive MIT. Fully clean for reuse.**

### 4.3 Dependencies & Requirements
- **Core Dependencies:** `scenedetect`, `transnetv2-pytorch`, `ultralytics`, `torch`, `faster-whisper`, `mediapipe`, `Pillow`, `fastapi`.
- **Hardware Acceleration:** Supports CUDA, Apple Silicon MPS, and CPU fallback.

### 4.4 Architecture & Key Modules
```
openshorts/
├── active_speaker.py    # MediaPipe / YOLO audio-visual lip sync
├── camera_inset.py      # Stream/OBS webcam inset isolation & layout
├── clip_selection.py    # Multimodal candidate generation
├── editor.py            # Video composition & cut assembler
├── ffmpeg_utils.py      # Hardware-accelerated filtergraph builders
├── gpu_render.py        # NVENC / VAAPI / VideoToolbox GPU pipeline
├── hooks.py             # Hook placement & title overlay generator
├── punch_in.py          # Dynamic scale punch-ins (10-15% focal pushes)
├── recut.py             # Re-segmentation & audio alignment
├── reframe_v2.py        # 43KB Two-stage low-res analysis + native FFmpeg render
├── screencast_layout.py # Screencast + facecam layout engine
├── split_layout.py      # Dual-speaker vertical stacked layout (1080x960 each)
├── subtitles.py         # Subtitle styling, emojis, and box decorations
└── thumbnail.py         # Automated thumbnail frame selector
```

### 4.5 Advanced Video Layouts & Auto-Reframing
- **Reframe Engine v2 (`reframe_v2.py`):**
  - **Stage 1 (Analysis):** Downscales video to <=640px, runs face detection and SmoothedCameraman state machine.
  - **Stage 2 (Native FFmpeg Render):** Emits dynamic crop coordinates via FFmpeg `sendcmd` filter, eliminating slow raw-frame piping.
- **Split Layout (`split_layout.py`):**
  - Detects two distinct speakers in wide conversation shots.
  - Crops both speakers simultaneously and stacks them vertically (top: speaker A, bottom: speaker B, 1080x960 each).
- **Camera Inset (`camera_inset.py`):**
  - Detects small webcam overlay rectangles in gaming or screen recordings.
  - Separates gameplay from creator face and comps gameplay on top, creator below.
- **Punch-In Zoom (`punch_in.py`):**
  - Automatically executes 10-15% subtle zoom-ins on emotional or emphatic speech beats, avoiding visual monotony.

### 4.6 Reusable Components & Assessment
- **Top Reusable Assets:**
  - `split_layout.py` & `camera_inset.py` for advanced creator/gamer formats.
  - `reframe_v2.py` two-phase FFmpeg `sendcmd` rendering architecture.
  - `punch_in.py` dynamic zoom algorithm.
  - Comprehensive FFmpeg filtergraph construction helpers.

---

## 5. In-Depth Audit: AutoClip

### 5.1 Project Overview & Repository Identity
- **Repository URL:** `https://github.com/zhouxiaoka/autoclip.git`
- **Target Audience:** Cross-platform video automation, content clipping with structured LLM workflows.
- **Architecture:** FastAPI backend + SQLite/PostgreSQL database + Celery task queue + React/Tauri desktop frontend.

### 5.2 Legal & Licensing Verification
- **License File:** `LICENSE` (MIT License, Copyright 2024 AutoClip Team).
- **pyproject.toml:** Confirms `license = { text = "MIT" }`.
- **License Verdict:** **100% Permissive MIT. Fully clean for reuse.**

### 5.3 Dependencies & Requirements
- **Backend:** `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `pydantic`, `celery`, `redis`, `yt-dlp`.
- **Frontend:** React, TypeScript, Tailwind CSS, Lucide, Tauri v2.

### 5.4 Architecture & Key Modules
```
autoclip/
├── backend/
│   ├── api/v1/          # Endpoints: projects, clips, processing, studio
│   ├── core/            # Config, database, error handling, LLM manager
│   ├── models/          # SQLAlchemy: Project, Clip, Task, Collection
│   ├── pipeline/        # 6-step structured pipeline
│   │   ├── step1_outline.py     # Structural outline extraction
│   │   ├── step2_timeline.py    # Timestamp alignment
│   │   ├── step3_scoring.py     # Quality & viral topic scoring
│   │   ├── step4_title.py       # Hook & title generation
│   │   ├── step5_clustering.py # Topic deduplication & merge
│   │   └── step6_video.py       # Final render assembly
│   └── services/        # reframer, subtitle_render, whisper_service
└── frontend/src/
    ├── features/studio/ # StudioEditor, StudioResults, TemplatePicker
    └── stores/          # Zustand / state management
```

### 5.5 Strengths & Reusable Components
- **Data Models:** Robust SQLAlchemy schemas for projects, candidate clips, rendering tasks, and export presets.
- **Error Recovery:** Resumable processing checkpoints, orphan process cleanup, and pipeline failure logging.
- **Studio UI Features:** `StudioEditor.tsx` and `TemplatePicker.tsx` provide clean React patterns for clip curation.

---

## 6. In-Depth Audit: Clips Studio (Clips Kitty)

### 6.1 Project Overview & Repository Identity
- **Repository URL:** `https://github.com/ColinGPT9/clips-studio.git`
- **Target Audience:** Automated creator suite, long-form content repurporsing.
- **Architectural Scope:** Extensive Python backend with multimodal hype detection, twitch chat analysis, and social publishing.

### 6.2 Legal & Licensing Verification (CRITICAL FINDING)
- **License File:** `LICENSE` (**GNU AFFERO GENERAL PUBLIC LICENSE Version 3 - AGPL-3.0**).
- **Notice File:** `NOTICE` ("Copyright (C) 2026 ColinGPT9... under the terms of the GNU Affero General Public License").
- **Legal Risk:**
  > [!CAUTION]
  > AGPL-3.0 is a strong copyleft license with a network-trigger clause. Incorporating or statically linking Clips Studio source code into our project would obligate the entire AI Clipping Studio to be licensed under AGPL-3.0, restricting licensing flexibility and commercial distribution.
- **License Verdict:** **DO NOT COPY OR DIRECTLY VENDOR. Retain for architectural study only.**

### 6.3 Technical Discoveries (For Clean-Room Implementation)
- **Multimodal Fusion Formula:**
  - `final_score = w_text * text + w_visual * visual + w_reaction * reaction + w_audio * audio + w_engagement * engagement`
  - Two-pool candidate mining: Transcript candidates + Audio/Visual signal peaks.
- **Hardware Agnostic Design:** Clean detection of Apple Silicon, CUDA, and CPU threads.

---

## 7. In-Depth Audit: SupoClip

### 7.1 Project Overview & Repository Identity
- **Repository URL:** `https://github.com/FujiwaraChoki/supoclip.git`
- **Target Audience:** SaaS and self-hosted automated short-form video generation.
- **Tech Stack:** FastAPI, Next.js 15, Prisma, PostgreSQL, Docker.

### 7.2 Legal & Licensing Verification (CRITICAL FINDING)
- **License File:** `LICENSE` (**SupoClip Noncommercial Source License Version 1.0, Licensor: Shiori LLC**).
- **Core Clause:**
  > "Subject to these terms, the Licensor grants you a worldwide, royalty-free, nonexclusive license to use, run, self-host, copy, modify, and share the Software for noncommercial purposes."
- **Legal Risk:**
  > [!CAUTION]
  > SupoClip is distributed under a proprietary, non-OSI-approved Noncommercial license. Copying or including any code, templates, or assets from SupoClip would legally restrict our entire application to noncommercial use only, violating our open and professional mandate.
- **License Verdict:** **DO NOT COPY OR DIRECTLY VENDOR. Zero code reuse permitted.**

### 7.3 Technical Verification
- All technical features present in SupoClip (FastAPI API, active speaker framing, subtitle rendering) are already implemented in permissive MIT repositories (Cutawan, Chopify, AutoClip, OpenShorts). No proprietary SupoClip code is required.

---

## 8. Summary of Reusable Assets & Clean Boundary Strategy

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PERMITTED CODE REUSE (MIT / OFL)                     │
├─────────────────────┬─────────────────────┬────────────────────────────┤
│ Cutawan (MIT)       │ Desktop App Shell   │ Electron + Vite + React 19 │
│                     │ UI & Waveform       │ TimelineEditor, Waveform   │
│                     │ Native ONNX         │ YuNet, Silero VAD, ASD     │
├─────────────────────┼─────────────────────┼────────────────────────────┤
│ Chopify (MIT)       │ Audio/Visual Brain  │ score_clips, evidence,     │
│                     │                     │ visual (NumPy/FFT)         │
│                     │ AI Tightening       │ tighten.py (filler/silence)│
│                     │ Captions            │ CapCut ASS Word Karaoke    │
├─────────────────────┼─────────────────────┼────────────────────────────┤
│ OpenShorts (MIT)    │ Creative Layouts    │ split_layout, camera_inset │
│                     │ Video Polish        │ punch_in (Dynamic Zoom)    │
│                     │ Native FFmpeg       │ reframe_v2 (sendcmd)       │
├─────────────────────┼─────────────────────┼────────────────────────────┤
│ AutoClip (MIT)      │ Project & Task DB   │ SQLite / Pydantic schemas  │
│                     │ LLM Outline/Scoring │ Topic outline & retry gate │
└─────────────────────┴─────────────────────┴────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│             EXCLUDED CODE / CLEAN-ROOM STUDY ONLY (NO COPY)            │
├─────────────────────┬─────────────────────┬────────────────────────────┤
│ Clips Studio        │ GNU AGPL-3.0        │ Strong copyleft infection  │
├─────────────────────┼─────────────────────┼────────────────────────────┤
│ SupoClip            │ Noncommercial 1.0   │ Proprietary commercial ban │
└─────────────────────┴─────────────────────┴────────────────────────────┘
```
