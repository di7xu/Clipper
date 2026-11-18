"""AI CLIPPING STUDIO: High-Performance Speech-to-Text & VAD Engine.

Leverages faster-whisper with CTranslate2 and Silero VAD pre-filtering,
extracting word-level millisecond timestamps and token probabilities.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Optional

from config import config


class TranscribeError(Exception):
    """Raised when audio extraction or transcription fails."""
    pass


class TranscribeEngine:
    """Orchestrates audio extraction, faster-whisper transcription, and VAD segmentation."""

    def __init__(self, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.progress_callback = progress_callback
        self._model_cache: Dict[str, Any] = {}

    def extract_audio(self, media_path: Path, output_wav: Path) -> Path:
        """Extract 16kHz mono PCM WAV from input video/audio using FFmpeg."""
        if not config.ffmpeg_path or not config.ffmpeg_path.is_file():
            raise TranscribeError(f"FFmpeg binary not found at: {config.ffmpeg_path}")

        output_wav.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(config.ffmpeg_path),
            "-y",
            "-i", str(media_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_wav)
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            if res.returncode != 0:
                raise TranscribeError(f"FFmpeg audio extraction failed: {res.stderr.strip()}")
        except Exception as e:
            raise TranscribeError(f"Error during audio extraction: {e}")

        if not output_wav.is_file() or output_wav.stat().st_size == 0:
            raise TranscribeError("Extracted audio WAV is empty or missing")

        return output_wav

    def get_or_load_model(self, model_size: str = "base"):
        """Load and cache faster-whisper model with automatic device/precision selection."""
        import faster_whisper

        if model_size in self._model_cache:
            return self._model_cache[model_size]

        device = "cuda" if config.hardware.has_nvidia_gpu and self._verify_cuda() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        try:
            model = faster_whisper.WhisperModel(
                model_size_or_path=model_size,
                device=device,
                compute_type=compute_type,
                cpu_threads=max(1, (os.cpu_count() or 4) // 2)
            )
            self._model_cache[model_size] = model
            return model
        except Exception as e:
            # Fallback to CPU int8 if CUDA fails
            if device == "cuda":
                print(f"[Whisper] CUDA initialization failed ({e}), falling back to CPU int8...")
                model = faster_whisper.WhisperModel(
                    model_size_or_path=model_size,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=max(1, (os.cpu_count() or 4) // 2)
                )
                self._model_cache[model_size] = model
                return model
            raise

    def _verify_cuda(self) -> bool:
        """Verify if CUDA runtime libraries are discoverable."""
        try:
            import ctranslate2
            return "cuda" in ctranslate2.get_supported_compute_types("cuda")
        except Exception:
            return False

    def transcribe(
        self,
        media_path: str,
        output_json: Optional[str] = None,
        model_size: str = "base",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract audio and transcribe with word-level timestamps and Silero VAD filtering."""
        input_file = Path(media_path).resolve()
        if not input_file.is_file():
            raise TranscribeError(f"Input file not found: {media_path}")

        # Check if cached transcript already exists
        if output_json and os.path.exists(output_json):
            try:
                with open(output_json, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                    if "words" in cached and "segments" in cached:
                        print(f"[Whisper] Loaded cached transcript from: {output_json}")
                        return cached
            except Exception:
                pass

        # Step 1: Audio Extraction
        self._emit_progress(10, "Extracting 16kHz mono audio stream...")
        temp_wav = config.temp_dir / f"temp_audio_{int(time.time())}.wav"
        try:
            self.extract_audio(input_file, temp_wav)
            self._emit_progress(30, f"Loading Whisper model ({model_size})...")

            # Step 2: Load Model
            model = self.get_or_load_model(model_size)

            # Step 3: Run Transcription with Word Timestamps & Silero VAD
            self._emit_progress(50, "Transcribing speech and extracting word boundaries...")
            import wave
            import numpy as np

            with wave.open(str(temp_wav), "rb") as wf:
                num_frames = wf.getnframes()
                raw_data = wf.readframes(num_frames)
                audio_array = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

            segments_gen, info = model.transcribe(
                audio_array,
                beam_size=5,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400),
                language=language
            )

            all_segments: List[Dict[str, Any]] = []
            all_words: List[Dict[str, Any]] = []

            for seg_idx, segment in enumerate(segments_gen):
                seg_words: List[Dict[str, Any]] = []
                if segment.words:
                    for w in segment.words:
                        cleaned = w.word.strip()
                        if cleaned:
                            word_dict = {
                                "word": cleaned,
                                "start": round(w.start, 3),
                                "end": round(w.end, 3),
                                "probability": round(w.probability, 3)
                            }
                            seg_words.append(word_dict)
                            all_words.append(word_dict)

                all_segments.append({
                    "id": seg_idx,
                    "start": round(segment.start, 3),
                    "end": round(segment.end, 3),
                    "text": segment.text.strip(),
                    "words": seg_words
                })

            result = {
                "language": info.language,
                "language_probability": round(info.language_probability, 3),
                "duration": round(info.duration, 3),
                "segments": all_segments,
                "words": all_words
            }

            self._emit_progress(100, "Transcription completed successfully.")

            # Save transcript locally if output_json is provided
            if output_json:
                out_path = Path(output_json)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

            return result

        finally:
            # Cleanup temporary wav
            if temp_wav.is_file():
                try:
                    temp_wav.unlink()
                except Exception:
                    pass

    def _emit_progress(self, percent: int, message: str):
        if self.progress_callback:
            self.progress_callback({"percent": percent, "message": message})


if __name__ == "__main__":
    if len(sys.argv) > 1:
        engine = TranscribeEngine(progress_callback=lambda p: print(f"Progress: {p['percent']}% - {p['message']}"))
        res = engine.transcribe(sys.argv[1], model_size="tiny")
        print(f"Detected language: {res['language']}, Total words: {len(res['words'])}")
    else:
        print("Usage: python src/transcription/engine.py <media_path>")
