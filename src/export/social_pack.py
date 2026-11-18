"""AI CLIPPING STUDIO: Social Media Metadata & Hashtag Generator."""
import json
from pathlib import Path
import re
from typing import Any, Dict, List


def generate_social_metadata(
    clip: Dict[str, Any],
    platform_preset: str = "youtube_shorts"
) -> Dict[str, Any]:
    """Generate platform-targeted title, hook text, description, and hashtags."""
    title = clip.get("title") or clip.get("hook") or "Must Watch Clip"
    transcript = clip.get("transcript", "")

    # Extract keywords for hashtags
    words = [re.sub(r"[^\w]", "", w).lower() for w in transcript.split()]
    common_stops = {"the", "a", "an", "is", "and", "or", "to", "in", "of", "that", "this", "it", "for", "with", "we", "you", "are"}
    meaningful = [w for w in words if len(w) > 4 and w not in common_stops]

    top_keywords = list(dict.fromkeys(meaningful))[:5]
    hashtags = [f"#{kw}" for kw in top_keywords]

    # Add platform standard viral tags
    if platform_preset == "youtube_shorts":
        hashtags.extend(["#Shorts", "#Viral", "#PodcastHighlights", "#MustWatch"])
    elif platform_preset == "tiktok":
        hashtags.extend(["#fyp", "#viral", "#foryou", "#trending"])
    elif platform_preset == "instagram_reels":
        hashtags.extend(["#reels", "#reelsinstagram", "#explorepage", "#creator"])

    description = (
        f"{title}\n\n"
        f"Key Takeaway: {transcript[:180]}...\n\n"
        f"Produced with AI Clipping Studio.\n\n"
        f"{' '.join(hashtags)}"
    )

    return {
        "title": title,
        "hook": clip.get("hook", title),
        "description": description,
        "hashtags": hashtags,
        "overallScore": clip.get("overallScore", 8.0),
        "platform": platform_preset
    }


def write_meta_package(
    meta_dict: Dict[str, Any],
    video_output_path: str
) -> Path:
    """Save metadata alongside rendered MP4 as <video_name>.meta.json."""
    meta_path = Path(video_output_path).with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta_path
