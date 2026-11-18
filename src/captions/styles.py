"""AI CLIPPING STUDIO: Caption Presets & ASS Style Definitions.

Defines typography, color palettes, and animation parameters for short-form video captions.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class CaptionStyleConfig:
    id: str
    name: str
    font_family: str
    font_size: int = 80          # Scaled for 1080p base height
    primary_color: str = "&H00FFFFFF"    # White in ASS &HAABBGGRR
    highlight_color: str = "&H0000FFFF"  # Electric Yellow
    outline_color: str = "&H00000000"    # Black outline
    outline_width: float = 4.0
    shadow_color: str = "&H80000000"     # Semi-transparent black shadow
    shadow_distance: float = 3.0
    margin_v: int = 280                  # Bottom margin
    alignment: int = 2                   # 2 = Bottom Center (Numpad)
    bold: int = 1
    uppercase: bool = True
    karaoke_effect: bool = True


# Predefined high-conversion short-form caption presets
PRESET_STYLES: Dict[str, CaptionStyleConfig] = {
    "viral_yellow": CaptionStyleConfig(
        id="viral_yellow",
        name="Viral Yellow",
        font_family="Anton",
        font_size=88,
        primary_color="&H00FFFFFF",
        highlight_color="&H0000E6FF",  # High-energy vibrant yellow
        outline_color="&H00000000",
        outline_width=5.0,
        margin_v=300,
        uppercase=True,
        karaoke_effect=True
    ),
    "clean_cyan": CaptionStyleConfig(
        id="clean_cyan",
        name="Clean Cyan",
        font_family="Poppins",
        font_size=76,
        primary_color="&H00FFFFFF",
        highlight_color="&H00FFFF00",  # Neon Cyan
        outline_color="&H00111111",
        outline_width=4.0,
        margin_v=280,
        uppercase=False,
        karaoke_effect=True
    ),
    "bold_coral": CaptionStyleConfig(
        id="bold_coral",
        name="Bold Coral",
        font_family="Archivo Black",
        font_size=82,
        primary_color="&H00FFFFFF",
        highlight_color="&H004E36FF",  # Hot Coral / Orange
        outline_color="&H00000000",
        outline_width=5.5,
        margin_v=320,
        uppercase=True,
        karaoke_effect=True
    ),
    "minimal_white": CaptionStyleConfig(
        id="minimal_white",
        name="Minimal White",
        font_family="Montserrat",
        font_size=70,
        primary_color="&H00F5F5F5",
        highlight_color="&H0000D4FF",
        outline_color="&H00000000",
        outline_width=3.5,
        margin_v=240,
        uppercase=False,
        karaoke_effect=False
    )
}


def hex_to_ass_color(hex_str: str, alpha: int = 0) -> str:
    """Convert #RRGGBB hex string to ASS &HAABBGGRR format."""
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 6:
        r, g, b = clean[0:2], clean[2:4], clean[4:6]
        return f"&H{alpha:02X}{b.upper()}{g.upper()}{r.upper()}"
    return "&H00FFFFFF"
