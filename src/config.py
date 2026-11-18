"""AI VIDEO PROCESSING ENVIRONMENT: System Configuration & Binary Discovery.

Provides cross-platform path resolution, hardware acceleration detection,
and binary verification for FFmpeg, FFprobe, yt-dlp, and AI model weights.
Consolidated from Cutawan, OpenShorts, AutoClip, and Chopify.
"""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Dict, List, Optional


@dataclass
class HardwareCapabilities:
    os_name: str
    architecture: str
    cpu_count: int
    has_nvidia_gpu: bool = False
    cuda_available: bool = False
    available_video_encoders: List[str] = field(default_factory=list)
    preferred_encoder: str = "libx264"
    ffmpeg_version: str = "unknown"
    ffprobe_version: str = "unknown"


class SystemConfig:
    """Central configuration manager for AI Video Processing Environment."""

    def __init__(self, workspace_root: Optional[Path] = None):
        if workspace_root is None:
            # Anchor to repository root directory
            self.root_dir = Path(__file__).resolve().parent.parent
        else:
            self.root_dir = Path(workspace_root).resolve()

        self.src_dir = self.root_dir / "src"
        self.resources_dir = self.root_dir / "resources"
        self.fonts_dir = self.resources_dir / "fonts"
        self.models_dir = self.resources_dir / "models"
        self.projects_dir = self.root_dir / "workspace_projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = self.root_dir / "workspace_temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # AI Models
        self.yunet_model = self.models_dir / "face-detection-yunet.onnx"
        self.silero_vad_model = self.models_dir / "silero-vad.onnx"

        # Discover multimedia binaries
        self.ffmpeg_path = self._discover_binary("ffmpeg")
        self.ffprobe_path = self._discover_binary("ffprobe")
        self.ytdlp_path = self._discover_binary("yt-dlp")

        # Hardware inspection
        self.hardware = self._inspect_hardware()

    def _discover_binary(self, binary_name: str) -> Optional[Path]:
        """Locate binary executable across standard Windows/Linux locations."""
        exe_name = f"{binary_name}.exe" if sys.platform == "win32" else binary_name

        # Priority 1: Check known local Python bin directory
        python_bin = Path(r"C:\MyProject\Mycreate\PYTHON FILE\bin") / exe_name
        if python_bin.is_file():
            return python_bin

        # Priority 2: Check workspace resources or bundled bin
        bundled = self.resources_dir / "bin" / exe_name
        if bundled.is_file():
            return bundled

        # Priority 3: Check system PATH
        path_match = shutil.which(binary_name)
        if path_match:
            return Path(path_match)

        return None

    def _verify_encoder(self, encoder: str) -> bool:
        """Run a lightweight 0.04s dry-run to verify hardware encoder driver availability."""
        if not self.ffmpeg_path:
            return False
        try:
            res = subprocess.run(
                [
                    str(self.ffmpeg_path),
                    "-nostdin",
                    "-v", "error",
                    "-f", "lavfi", "-i", "testsrc=duration=0.04:size=320x240:rate=25",
                    "-c:v", encoder,
                    "-f", "null", "-"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
                check=False
            )
            return res.returncode == 0
        except Exception:
            return False

    def _inspect_hardware(self) -> HardwareCapabilities:
        """Probe CPU, GPU, OS, and encoder support."""
        caps = HardwareCapabilities(
            os_name=platform.system(),
            architecture=platform.machine(),
            cpu_count=os.cpu_count() or 4
        )

        if self.ffmpeg_path and self.ffmpeg_path.is_file():
            try:
                proc = subprocess.run(
                    [str(self.ffmpeg_path), "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5,
                    check=False
                )
                first_line = proc.stdout.splitlines()[0] if proc.stdout else "FFmpeg present"
                caps.ffmpeg_version = first_line.strip()
            except Exception:
                caps.ffmpeg_version = "FFmpeg found"

            # Probe encoders
            try:
                enc_proc = subprocess.run(
                    [str(self.ffmpeg_path), "-encoders"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5,
                    check=False
                )
                output = enc_proc.stdout
                encoders = []
                for enc in ["h264_nvenc", "hevc_nvenc", "h264_qsv", "hevc_qsv", "h264_videotoolbox", "h264_vaapi", "libx264"]:
                    if enc in output:
                        encoders.append(enc)

                verified_encoders = []
                for enc in encoders:
                    if self._verify_encoder(enc):
                        verified_encoders.append(enc)

                if "libx264" not in verified_encoders:
                    verified_encoders.append("libx264")

                caps.available_video_encoders = verified_encoders

                # Preferred encoder order: NVENC > QSV > VideoToolbox > libx264
                if "h264_nvenc" in verified_encoders:
                    caps.has_nvidia_gpu = True
                    caps.preferred_encoder = "h264_nvenc"
                elif "h264_videotoolbox" in verified_encoders:
                    caps.preferred_encoder = "h264_videotoolbox"
                elif "h264_qsv" in verified_encoders:
                    caps.preferred_encoder = "h264_qsv"
                else:
                    caps.preferred_encoder = "libx264"
            except Exception:
                caps.available_video_encoders = ["libx264"]
                caps.preferred_encoder = "libx264"

        return caps

    def to_dict(self) -> Dict:
        return {
            "rootDir": str(self.root_dir),
            "ffmpeg": str(self.ffmpeg_path) if self.ffmpeg_path else None,
            "ffprobe": str(self.ffprobe_path) if self.ffprobe_path else None,
            "ytdlp": str(self.ytdlp_path) if self.ytdlp_path else None,
            "models": {
                "yunet": str(self.yunet_model) if self.yunet_model.is_file() else None,
                "sileroVad": str(self.silero_vad_model) if self.silero_vad_model.is_file() else None,
            },
            "hardware": {
                "os": self.hardware.os_name,
                "arch": self.hardware.architecture,
                "cpuCount": self.hardware.cpu_count,
                "preferredEncoder": self.hardware.preferred_encoder,
                "availableEncoders": self.hardware.available_video_encoders,
                "ffmpegVersion": self.hardware.ffmpeg_version,
            }
        }


# Global singleton instance
config = SystemConfig()
