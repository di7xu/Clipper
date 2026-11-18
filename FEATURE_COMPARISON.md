# FEATURE COMPARISON MATRIX & BENCHMARK AUDIT
**Document Version:** 1.0  
**Application:** AI CLIPPING STUDIO  
**Scope:** Systematic feature verification across Cutawan, Chopify, OpenShorts, AutoClip, Clips Studio, and SupoClip.

---

## 1. Feature Comparison Matrix

The table below rates each feature's source code implementation on a scale of **0 to 5** (0 = Absent or marketing claim only, 1 = Minimal stub, 3 = Functional but limited, 5 = Production-grade, verified in source code).

| Capability Area | Specific Feature | Cutawan | Chopify | OpenShorts | AutoClip | Clips Studio | SupoClip | Winner / Selected Origin | Selection Rationale |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Video Ingest** | Format validation & ffprobe probe | 5 | 4 | 4 | 4 | 4 | 3 | **Cutawan** | High-performance async ffprobe extraction with stream sanitization and audio channel verification. |
| | Stream / URL Ingest (yt-dlp) | 4 | 4 | 4 | 4 | 5 | 3 | **Chopify / Cutawan** | Clean, sandboxed yt-dlp execution with proxy support and format selection (`bestvideo+bestaudio`). |
| **Transcription** | Word-level timestamps & Whisper | 5 | 5 | 4 | 4 | 4 | 4 | **Cutawan + Chopify** | Both utilize local `faster-whisper` emitting JSON word-level boundaries and token probabilities. |
| | Millisecond VAD & Speech Segmentation | 5 | 4 | 3 | 3 | 4 | 3 | **Cutawan** | Native ONNX Silero VAD runs off-thread with millisecond boundary detection. |
| | Offline / Zero-Cost Processing | 5 | 5 | 4 | 3 | 4 | 3 | **Chopify / Cutawan** | Runs 100% locally on CPU or GPU without requiring external API tokens. |
| **Clip Detection** | Lexical & Transcript Heuristics | 4 | 5 | 4 | 4 | 4 | 3 | **Chopify (`score_clips.py`)**| 1,753 lines of deterministic lexical analysis (hooks, humor, insights, energy, arc completion). |
| | Audio Spectral Flux & RMS Energy | 4 | 5 | 3 | 2 | 4 | 2 | **Chopify (`evidence.py`)** | Dedicated 16kHz mono FFT analysis caching `audio_features.npz` with zero network overhead. |
| | Visual Motion & Cut Detection | 4 | 5 | 4 | 2 | 4 | 2 | **Chopify (`visual.py`)** | 2 fps 160x90 frame-difference motion tracking and scene baseline analysis. |
| | Multi-step Topic Outline & Clustering | 2 | 2 | 3 | 5 | 3 | 3 | **AutoClip (`step1-step5`)**| Structured LLM decomposition: outline -> candidate timeline -> scoring -> deduplication. |
| | Local LLM Reranking (Ollama) | 3 | 5 | 2 | 4 | 4 | 3 | **Chopify (`semantic.py`)** | Seamless local Ollama integration that adjusts score without breaking clip boundaries. |
| **Reframing & Layouts** | Dynamic YuNet Face Tracking | 5 | 4 | 4 | 3 | 4 | 3 | **Cutawan / Chopify** | Native ONNX YuNet / OpenCV YuNet with exponential camera path smoothing. |
| | Stacked Dual-Speaker Split Layout | 2 | 1 | 5 | 2 | 3 | 3 | **OpenShorts (`split_layout`)**| Stacks two speakers in 9:16 frame (1080x960 each) for dialogue/podcasts without distortion. |
| | Camera Inset (Gaming/OBS isolation) | 1 | 1 | 5 | 1 | 3 | 2 | **OpenShorts (`camera_inset`)**| Isolates creator facecam from game/screen content; stacks game top, face bottom. |
| | Dynamic Punch-In Zoom | 2 | 1 | 5 | 2 | 3 | 2 | **OpenShorts (`punch_in`)** | 10-15% focal punch-ins on emotional beats, preventing unedited static shot fatigue. |
| **Captions** | CapCut-style Animated Karaoke (.ass) | 5 | 5 | 4 | 3 | 4 | 3 | **Chopify + Cutawan** | Word-by-word highlight animations compiled directly into FFmpeg-compatible ASS subtitles. |
| | Custom OFL Typography | 5 | 4 | 4 | 3 | 3 | 3 | **Cutawan + OpenShorts**| Bundled OFL fonts: Poppins, Anton, ArchivoBlack, Montserrat with strict font registrations. |
| | Subtitle Timing After Edits | 4 | 5 | 3 | 2 | 3 | 2 | **Chopify (`tighten.py`)** | Automatically recalibrates all word timings when audio pauses or fillers are eliminated. |
| **Editing & Tighten** | Filler Word Removal (`um`, `uh`) | 3 | 5 | 2 | 1 | 3 | 2 | **Chopify (`tighten.py`)** | Prunes conversational filler tokens without disturbing natural speech cadence. |
| | Automatic Silence Pruning | 4 | 5 | 3 | 2 | 3 | 2 | **Chopify (`tighten.py`)** | Trims pauses > 0.6s while preserving a protective 150ms speech buffer. |
| | Interactive React Timeline & Waveform| 5 | 1 | 1 | 3 | 1 | 2 | **Cutawan (`TimelineEditor`)** | Full interactive multi-track timeline with draggable playhead, audio waveform, and cuts. |
| **Social Content** | Ready-to-Post Titles & Descriptions | 3 | 5 | 3 | 5 | 4 | 3 | **Chopify + AutoClip** | Emits viral title options, platform descriptions, and targeted hashtags into metadata. |
| | Thumbnail Frame Extraction | 3 | 3 | 5 | 3 | 4 | 3 | **OpenShorts (`thumbnail.py`)**| Evaluates frame aesthetics, face presence, and clarity to select optimal cover shot. |
| **Render & Export** | Hardware Acceleration (NVENC/QSV) | 5 | 3 | 5 | 3 | 4 | 3 | **Cutawan + OpenShorts** | Comprehensive hardware encoder detection (`h264_nvenc`, `h264_qsv`, `videotoolbox`). |
| | Native FFmpeg sendcmd Crop Pipeline | 3 | 3 | 5 | 2 | 3 | 2 | **OpenShorts (`reframe_v2`)** | Analyzes low-res, renders natively in FFmpeg via `sendcmd`, bypassing slow raw pipes. |
| **Desktop UX** | Cross-Platform Desktop App | 5 | 1 | 1 | 4 | 1 | 1 | **Cutawan (Electron+Vite)** | Modern dark-mode UI, native window controls, responsive React 19 architecture. |
| **Licensing** | Commercial & Open Distribution Freedom| 5 (MIT)| 5 (MIT)| 5 (MIT)| 5 (MIT)| 1 (AGPL)| 0 (NC) | **Cutawan/Chopify/OpenShorts/AutoClip**| Permissive MIT core ensures total legal clarity and unencumbered commercial use. |

---

## 2. Strongest Implementations by Component

### Component A: Desktop Application Shell & UI Architecture
- **Undisputed Winner:** **Cutawan**
- **Justification:** Built on **Electron + Vite + React 19 + Tailwind CSS**, Cutawan delivers the only true production-grade desktop application among the six repos. It features:
  - An interactive multi-track timeline (`TimelineEditor.tsx`) with real-time waveform display.
  - In-place transcript correction synchronized with playback (`TranscriptEditor.tsx`).
  - Native windowing, dark UI, responsive settings, and typed IPC communication.

### Component B: AI Clip Scoring Engine ("The Brain")
- **Undisputed Winner:** **Chopify** (`score_clips.py`, `evidence.py`, `visual.py`)
- **Justification:** Chopify implements the deepest, most transparent, and fully local scoring brain:
  - **Deterministic Audio Evidence:** Mono 16kHz FFT spectral flux + RMS energy detection (`evidence.py`).
  - **Deterministic Visual Evidence:** 2 fps frame-difference motion, scene change, and face presence (`visual.py`).
  - **Lexical Emotion & Hook Scoring:** Evaluates hook cues, shock, humor, controversy, and actionable knowledge.
  - **Zero Cost / Zero Token Requirement:** Works completely offline without requiring paid API keys, with optional local Ollama re-ranking.

### Component C: Video Layouts & Auto-Reframing
- **Undisputed Winner:** **OpenShorts** (`split_layout.py`, `camera_inset.py`, `reframe_v2.py`, `punch_in.py`)
- **Justification:** While Cutawan and Chopify handle standard single-face 9:16 tracking, OpenShorts solves the complex real-world creator scenarios:
  - **Split Layout:** Stacks two conversation partners vertically for interviews/podcasts.
  - **Camera Inset:** Separates gameplay/screen recording from webcam overlays.
  - **Punch-In Zoom:** Automatically applies subtle 10-15% focal pushes on emphatic speech beats.
  - **Reframe v2:** Employs FFmpeg `sendcmd` dynamic cropping for 10x faster export than raw-frame piping.

### Component D: AI Editing, Tightening & Subtitles
- **Undisputed Winner:** **Chopify** (`tighten.py`, `render_clips.py`) + **Cutawan** (`captions.ts`)
- **Justification:**
  - `tighten.py` removes filler words (`um`, `uh`) and awkward silences while mathematically adjusting all subsequent subtitle timestamps.
  - Both repositories compile CapCut-style animated word-by-word karaoke ASS subtitles rendered natively in FFmpeg.

### Component E: Project Storage, Data Models & Pipeline Controls
- **Undisputed Winner:** **AutoClip** (`models/`, `pipeline/`)
- **Justification:** AutoClip provides robust data schemas for projects, candidate clips, rendering jobs, and fail-safe recovery checkpoints, preventing lost work on crashes.

---

## 3. The Unified "Best-of-All" Synthesis Plan

By strategically synthesizing the verified best modules under permissive MIT licenses, **AI CLIPPING STUDIO** achieves a product superior to any single repository:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   AI CLIPPING STUDIO UNIFIED ENGINE                    │
├────────────────────────────────────────────────────────────────────────┤
│  [Desktop UI & Timeline]      <-- Cutawan (Electron + React 19)        │
│  [Audio & Visual Evidence]    <-- Chopify (evidence.py, visual.py)     │
│  [Clip Scoring & Heuristics]  <-- Chopify (score_clips.py, Ollama)     │
│  [Advanced Layouts & Insets]  <-- OpenShorts (split, inset, punch-in)  │
│  [Native Fast Reframe Render] <-- OpenShorts (reframe_v2 sendcmd)      │
│  [AI Tighten & Retiming]      <-- Chopify (tighten.py)                 │
│  [Animated Smart Captions]    <-- Cutawan & Chopify (ASS Karaoke)      │
│  [Project & Task Data Model]  <-- AutoClip (SQLite / Pydantic schemas) │
│  [Hardware Encoder Engine]    <-- Cutawan & OpenShorts (NVENC/QSV)     │
└────────────────────────────────────────────────────────────────────────┘
```
