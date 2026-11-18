# THIRD-PARTY NOTICES AND ATTRIBUTIONS

AI CLIPPING STUDIO incorporates algorithms, design patterns, and components inspired by or adapted from the open-source community under permissive licenses.

## Summary of Open-Source Components and Attributions

### 1. Cutawan
- **Origin:** JeremySNR / Cutawan Contributors
- **License:** MIT License
- **Reused Concepts & Assets:**
  - Desktop application scaffolding (Electron, Vite, React, Tailwind CSS)
  - Interactive multi-track timeline and canvas video preview architecture
  - ONNX runtime worker integration and model configurations (YuNet, Silero VAD)
  - Hardware-accelerated FFmpeg encoder detection patterns

### 2. Chopify
- **Origin:** Mehbul Islam
- **License:** MIT License
- **Reused Concepts & Assets:**
  - Deterministic audio spectral flux and RMS energy scoring (`evidence.py`)
  - Low-resolution frame difference and scene cut heuristics (`visual.py`)
  - Lexical cue discovery and story arc scoring engine (`score_clips.py`)
  - Subtitle-preserving conversational filler and silence removal algorithm (`tighten.py`)
  - FFmpeg Advanced SubStation Alpha (.ass) word-by-word karaoke subtitle styling

### 3. OpenShorts
- **Origin:** OpenShorts Team
- **License:** MIT License
- **Reused Concepts & Assets:**
  - Dual-speaker stacked vertical layout math (`split_layout.py`)
  - Screen recording / OBS webcam inset isolation (`camera_inset.py`)
  - Two-stage low-resolution analysis with native FFmpeg `sendcmd` cropping (`reframe_v2.py`)
  - Dynamic punch-in zoom beats for pacing (`punch_in.py`)

### 4. AutoClip
- **Origin:** AutoClip Team
- **License:** MIT License
- **Reused Concepts & Assets:**
  - Structured data schemas for video projects, candidate clips, and rendering tasks
  - Resumable pipeline checkpoints and job state management
  - Multi-stage topic extraction and deduplication concepts

---

## Bundled Typography (SIL Open Font License 1.1)

The following open-source fonts are bundled for subtitle styling:
- **Anton Regular** - Designed by Vernon Adams (SIL Open Font License 1.1)
- **Poppins (Bold, Medium)** - Designed by Indian Type Foundry (SIL Open Font License 1.1)
- **Archivo Black** - Designed by Omnibus-Type (SIL Open Font License 1.1)
- **Montserrat** - Designed by Julieta Ulanovsky (SIL Open Font License 1.1)

All bundled fonts are distributed under the terms of the SIL Open Font License, Version 1.1.

---

## Bundled AI Models & Open Weights

- **YuNet Face Detector (`face-detection-yunet.onnx`):** Developed by OpenCV / Shiqi Yu (MIT / Apache 2.0).
- **Silero VAD (`silero-vad.onnx`):** Developed by Silero Team (MIT License).
- **Faster-Whisper:** Developed by SYSTRAN / Guillaume Klein based on OpenAI Whisper (MIT License).

---

## Explicitly Excluded Repositories

The following source repositories were analyzed during the initial audit phase but are strictly excluded from code inclusion to maintain legal compliance:
- **Clips Studio (GNU AGPL-3.0):** Excluded to prevent copyleft viral licensing obligations.
- **SupoClip (Noncommercial Source License 1.0):** Excluded to prevent proprietary noncommercial distribution restrictions.
