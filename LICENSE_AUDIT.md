# LICENSE AUDIT & COMPONENT REUSE STRATEGY
**Document Version:** 1.0  
**Application:** AI CLIPPING STUDIO  
**Date:** November 2026  
**Auditor:** Legal & Architectural Systems Review

---

## 1. Executive Summary & Legal Classification

A rigorous legal audit was conducted across all six source repositories, their dependencies, bundled AI models, and font assets. The repositories fall into three distinct legal categories:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Category 1: Permissive Open-Source (MIT / OFL)                       │
│ Status: APPROVED FOR CODE ADOPTION & INTEGRATION                    │
│ Repositories: Cutawan, Chopify, OpenShorts, AutoClip                │
│ Obligations: Retain copyright notices & include full license texts.  │
├──────────────────────────────────────────────────────────────────────┤
│ Category 2: Strong Copyleft (GNU AGPL-3.0)                           │
│ Status: RESTRICTED - CLEAN-ROOM STUDY ONLY (ZERO CODE VENDORING)     │
│ Repository: Clips Studio (ColinGPT9 / Clips Kitty)                   │
│ Risk: Network copyleft trigger forces entire app under AGPL-3.0.     │
├──────────────────────────────────────────────────────────────────────┤
│ Category 3: Proprietary Source-Available (Noncommercial 1.0)         │
│ Status: PROHIBITED - CLEAN-ROOM STUDY ONLY (ZERO CODE VENDORING)     │
│ Repository: SupoClip (Shiori LLC)                                    │
│ Risk: Commercial ban destroys software viability and distribution.   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. In-Depth License Analysis by Repository

### 2.1 Cutawan
- **License:** MIT License.
- **Copyright Holder:** Copyright (c) 2026 Cutawan Contributors.
- **Bundled Assets:**
  - `face-detection-yunet.onnx`: MIT License (`yunet-LICENSE`).
  - `silero-vad.onnx`: MIT License (`silero-vad-LICENSE`).
  - `Anton-Regular.ttf`: SIL Open Font License 1.1 (`OFL-Anton.txt`).
  - `Poppins-Bold.ttf`, `Poppins-Medium.ttf`: SIL Open Font License 1.1 (`OFL-Poppins.txt`).
- **Legal Assessment:** Clean, unencumbered permissive license. All bundled models and fonts carry permissive licenses. Code, types, and UI components can be legally integrated provided the copyright notice is preserved.

### 2.2 Chopify
- **License:** MIT License.
- **Copyright Holder:** Copyright (c) 2026 Mehbul Islam.
- **Dependencies:** `yt-dlp` (Unlicense), `faster-whisper` (MIT), `opencv-python` (Apache 2.0), `numpy` (BSD 3-Clause).
- **Legal Assessment:** 100% Permissive MIT. Zero external proprietary dependencies. Python modules (`score_clips.py`, `evidence.py`, `visual.py`, `tighten.py`, `render_clips.py`) can be legally adopted and adapted with appropriate attribution.

### 2.3 OpenShorts
- **License:** MIT License.
- **Copyright Holder:** Copyright (c) 2024 OpenShorts.
- **Notice File:** `NOTICE` file present and explicitly references MIT terms.
- **Bundled Fonts:** `Anton-Regular.ttf`, `ArchivoBlack-Regular.ttf`, `Montserrat-ExtraBold.ttf` (all SIL Open Font License 1.1).
- **Legal Assessment:** Permissive MIT. Python layout components (`split_layout.py`, `camera_inset.py`, `reframe_v2.py`, `punch_in.py`) are fully authorized for reuse under MIT conditions.

### 2.4 AutoClip
- **License:** MIT License.
- **Copyright Holder:** Copyright (c) 2024 AutoClip Team.
- **Packaging:** `pyproject.toml` and root `LICENSE` unambiguously declare MIT.
- **Legal Assessment:** Permissive MIT. Data models, Celery/SQLite task queue concepts, and pipeline control structures are authorized for reuse with attribution.

### 2.5 Clips Studio (Clips Kitty)
- **License:** **GNU Affero General Public License Version 3 (AGPL-3.0)**.
- **Copyright Holder:** Copyright (C) 2026 ColinGPT9.
- **Legal Implications:**
  - Section 13 of the AGPL-3.0 ("Remote Network Interaction") states that if a modified version of the software provides a service across a network, the complete corresponding source code must be made publicly available under AGPL-3.0.
  - Section 5 of AGPL-3.0 mandates that any aggregate work containing AGPL code must itself be licensed as a whole under AGPL-3.0.
  - **Decision:** To keep **AI CLIPPING STUDIO** cleanly and permissively licensed under the **MIT License**, **NO CODE, BINARIES, OR TEMPLATES FROM CLIPS STUDIO SHALL BE COPIED OR LINKED INTO THE REPOSITORY**. Its algorithmic ideas (such as multimodal weight equations) may be studied conceptually, but all implementations must stem from MIT repositories or be written independently from scratch.

### 2.6 SupoClip
- **License:** **SupoClip Noncommercial Source License Version 1.0**.
- **Licensor:** Shiori LLC.
- **Legal Clause:**
  > "Subject to these terms, the Licensor grants you a worldwide, royalty-free, nonexclusive license to use, run, self-host, copy, modify, and share the Software for noncommercial purposes."
- **Legal Implications:**
  - The license is **non-free and non-open-source** according to Open Source Initiative (OSI) and Free Software Foundation (FSF) definitions.
  - Any inclusion of SupoClip code would infect AI Clipping Studio with a commercial ban, legally exposing commercial users and creators to copyright infringement.
  - **Decision:** **STRICT PROHIBITION: ZERO CODE, ASSETS, OR FILES FROM SUPOCLIP SHALL BE COPIED, VENDORED, OR INCORPORATED.** All technical capabilities of SupoClip are already available under MIT in Cutawan, Chopify, OpenShorts, and AutoClip.

---

## 3. Font and Binary Licensing Audit

### 3.1 Bundled Typography
All bundled fonts are licensed under the **SIL Open Font License (OFL) Version 1.1**:
- **Anton Regular:** Copyright (c) 2011, Vernon Adams (`vernon@sansoxygen.com`).
- **Poppins (Bold, Medium):** Copyright (c) 2014-2015, Indian Type Foundry (`info@indiantypefoundry.com`).
- **Archivo Black:** Copyright (c) 2012, Omnibus-Type (`omnibus.type@gmail.com`).
- **Montserrat:** Copyright (c) 2011-2017, Julieta Ulanovsky.
- **OFL Compliance:** The OFL permits embedding, bundling, and distribution with software, provided the font names are not sold by themselves and copyright notices are preserved.

### 3.2 AI Model Weights
- **YuNet Face Detector (`face-detection-yunet.onnx`):** Developed by Shiqi Yu, Shenzhen Institute of Advanced Technology / OpenCV. Distributed under MIT / Apache 2.0.
- **Silero VAD (`silero-vad.onnx`):** Developed by Silero Team. Distributed under MIT License (`silero-vad-LICENSE`).
- **Whisper Models (via `faster-whisper`):** OpenAI Whisper model weights are released under the MIT License; `faster-whisper` and `ctranslate2` are MIT licensed.

### 3.3 Multimedia Binaries (FFmpeg)
- FFmpeg builds distributed or utilized natively are compiled with `--enable-gpl --enable-libx264` or `--enable-version3`.
- By invoking FFmpeg as an external, decoupled child process via standard command-line interfaces (`subprocess.run` / Node.js `child_process.spawn`), FFmpeg remains a separate program under copyright law, preserving the independent MIT licensing of the application code.

---

## 4. Compliance Checklist

- [x] All source code integrated into AI Clipping Studio is licensed under the MIT License.
- [x] No code from `clips-studio` (AGPL-3.0) is copied, merged, or statically linked.
- [x] No code from `supoclip` (Noncommercial 1.0) is copied, merged, or referenced.
- [x] All original author copyright notices are preserved in `THIRD_PARTY_NOTICES.md`.
- [x] All OFL font licenses are included alongside font binaries.
- [x] All ONNX model licenses are verified as permissive (MIT/Apache 2.0).
- [x] External command-line boundaries (FFmpeg, yt-dlp) are cleanly decoupled.
