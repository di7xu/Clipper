"""Automated tests for Audio Extraction and Transcription Engine."""
from pathlib import Path
import subprocess
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import config
from transcription.engine import TranscribeEngine, TranscribeError


@pytest.fixture(scope="session")
def test_audio_file(tmp_path_factory):
    """Generate a 2-second audio file using FFmpeg."""
    temp_dir = tmp_path_factory.mktemp("audio_test")
    wav_path = temp_dir / "sample_sine.wav"

    cmd = [
        str(config.ffmpeg_path),
        "-y",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
        "-ar", "44100",
        "-ac", "2",
        str(wav_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return str(wav_path)


def test_extract_audio(test_audio_file, tmp_path):
    engine = TranscribeEngine()
    out_wav = tmp_path / "extracted_16k_mono.wav"
    extracted = engine.extract_audio(Path(test_audio_file), out_wav)

    assert extracted.is_file()
    assert extracted.stat().st_size > 0

    # Probe extracted file to ensure it is 16kHz mono
    cmd = [
        str(config.ffprobe_path),
        "-v", "error",
        "-show_entries", "stream=sample_rate,channels",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(extracted)
    ]
    out = subprocess.check_output(cmd, text=True).strip().splitlines()
    assert "16000" in out  # 16kHz sample rate
    assert "1" in out      # 1 channel (mono)


def test_whisper_model_initialization():
    engine = TranscribeEngine()
    # Test loading tiny model on CPU/GPU
    model = engine.get_or_load_model("tiny")
    assert model is not None
