"""AI CLIPPING STUDIO: Social Media Platform Export Presets."""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PlatformExportPreset:
    id: str
    name: str
    aspect_ratio: str
    width: int
    height: int
    fps: int
    video_bitrate: str
    audio_bitrate: str
    max_duration_seconds: int
    default_caption_style: str
    platform_name: str


EXPORT_PRESETS: Dict[str, PlatformExportPreset] = {
    "youtube_shorts": PlatformExportPreset(
        id="youtube_shorts",
        name="YouTube Shorts (9:16)",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        fps=30,
        video_bitrate="10M",
        audio_bitrate="192k",
        max_duration_seconds=60,
        default_caption_style="viral_yellow",
        platform_name="YouTube Shorts"
    ),
    "tiktok": PlatformExportPreset(
        id="tiktok",
        name="TikTok Video (9:16)",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        fps=30,
        video_bitrate="8M",
        audio_bitrate="192k",
        max_duration_seconds=60,
        default_caption_style="clean_cyan",
        platform_name="TikTok"
    ),
    "instagram_reels": PlatformExportPreset(
        id="instagram_reels",
        name="Instagram Reels (9:16)",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        fps=30,
        video_bitrate="8M",
        audio_bitrate="192k",
        max_duration_seconds=90,
        default_caption_style="bold_coral",
        platform_name="Instagram Reels"
    ),
    "square_feed": PlatformExportPreset(
        id="square_feed",
        name="Square Post (1:1)",
        aspect_ratio="1:1",
        width=1080,
        height=1080,
        fps=30,
        video_bitrate="6M",
        audio_bitrate="192k",
        max_duration_seconds=60,
        default_caption_style="minimal_white",
        platform_name="Square Feed"
    ),
    "landscape_highlights": PlatformExportPreset(
        id="landscape_highlights",
        name="Landscape Highlights (16:9)",
        aspect_ratio="16:9",
        width=1920,
        height=1080,
        fps=30,
        video_bitrate="12M",
        audio_bitrate="256k",
        max_duration_seconds=300,
        default_caption_style="clean_cyan",
        platform_name="Landscape Video"
    )
}
