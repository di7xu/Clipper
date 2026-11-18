"""AI CLIPPING STUDIO: AI Tightening & Subtitle Retiming.

Removes conversational filler words ('um', 'uh', 'you know') and long silences
from video clips, mathematically re-timing subtitle timestamps to maintain zero-drift sync.
"""
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from config import config

FILLER_TOKENS = {"um", "uh", "uhh", "umm", "erm", "er", "hmm", "mmm", "mm", "ah", "eh"}
FILLER_SEQS = {("you", "know"), ("i", "mean"), ("kind", "of"), ("sort", "of")}
DEFAULT_GAP = 0.6    # silence longer than this (seconds) gets cut
GUARD = 0.15         # keep this buffer around words (seconds)
MIN_KEEP = 0.30      # never create a keep-range shorter than this (seconds)


def clean_token(token: str) -> str:
    """Strip punctuation and normalize to lowercase."""
    return re.sub(r"[^\w]", "", token or "").lower()


def plan_cuts(
    words: List[Dict[str, Any]],
    clip_start: float,
    clip_end: float,
    gap: float = DEFAULT_GAP,
    fillers: bool = True,
    silence: bool = True
) -> Dict[str, Any]:
    """Calculate keep-ranges and retime all words to match the shortened timeline."""
    clip_duration = clip_end - clip_start
    if clip_duration <= 0 or not words:
        return {
            "keepRanges": [(0.0, max(0.1, clip_duration))],
            "retimedWords": words,
            "savedDuration": 0.0,
            "newDuration": clip_duration
        }

    # Filter words belonging to this clip
    in_clip = []
    for w in words:
        ws = float(w["start"])
        we = float(w["end"])
        if ws >= clip_start - 0.05 and we <= clip_end + 0.05:
            in_clip.append({
                "word": str(w["word"]),
                "start": max(0.0, ws - clip_start),
                "end": min(clip_duration, we - clip_start),
                "clean": clean_token(w["word"])
            })

    # 1. Identify filler word intervals
    cut_intervals: List[Tuple[float, float]] = []
    if fillers:
        i = 0
        while i < len(in_clip):
            tok = in_clip[i]["clean"]
            matched = False

            # Check 2-word filler sequences ("you know", "i mean")
            if i + 1 < len(in_clip):
                pair = (tok, in_clip[i + 1]["clean"])
                if pair in FILLER_SEQS:
                    cut_intervals.append((in_clip[i]["start"], in_clip[i + 1]["end"]))
                    i += 2
                    matched = True

            if not matched and tok in FILLER_TOKENS:
                cut_intervals.append((in_clip[i]["start"], in_clip[i]["end"]))
                i += 1
            elif not matched:
                i += 1

    # 2. Identify silence gaps > gap threshold
    if silence and len(in_clip) > 1:
        # Check start silence
        if in_clip[0]["start"] > gap:
            cut_intervals.append((0.0, in_clip[0]["start"] - GUARD))

        # Check between-word silences
        for j in range(len(in_clip) - 1):
            w_curr_end = in_clip[j]["end"]
            w_next_start = in_clip[j + 1]["start"]
            silence_dur = w_next_start - w_curr_end
            if silence_dur > gap:
                cut_intervals.append((w_curr_end + GUARD, w_next_start - GUARD))

        # Check trailing silence
        trailing_silence = clip_duration - in_clip[-1]["end"]
        if trailing_silence > gap:
            cut_intervals.append((in_clip[-1]["end"] + GUARD, clip_duration))

    # If no cuts were identified, keep whole duration
    if not cut_intervals:
        return {
            "keepRanges": [(0.0, round(clip_duration, 3))],
            "retimedWords": [{"word": w["word"], "start": round(w["start"], 3), "end": round(w["end"], 3)} for w in in_clip],
            "savedDuration": 0.0,
            "newDuration": round(clip_duration, 3)
        }

    # Merge overlapping cut intervals
    cut_intervals.sort()
    merged_cuts = []
    for start, end in cut_intervals:
        if not merged_cuts:
            merged_cuts.append([start, end])
        else:
            if start <= merged_cuts[-1][1]:
                merged_cuts[-1][1] = max(merged_cuts[-1][1], end)
            else:
                merged_cuts.append([start, end])

    # Invert cut intervals into keep intervals
    keep_ranges: List[Tuple[float, float]] = []
    cursor = 0.0
    for c_start, c_end in merged_cuts:
        if c_start > cursor + MIN_KEEP:
            keep_ranges.append((round(cursor, 3), round(c_start, 3)))
        cursor = max(cursor, c_end)

    if cursor + MIN_KEEP < clip_duration:
        keep_ranges.append((round(cursor, 3), round(clip_duration, 3)))

    if not keep_ranges:
        keep_ranges = [(0.0, round(clip_duration, 3))]

    # 3. Retime words according to keep ranges
    retimed_words: List[Dict[str, Any]] = []
    for w in in_clip:
        # Check if word falls within any cut interval
        ws = w["start"]
        we = w["end"]
        in_cut = any(cs <= ws and we <= ce for cs, ce in merged_cuts)
        if in_cut:
            continue

        # Map original time to tightened time
        new_start = _map_time_to_tightened(ws, keep_ranges)
        new_end = _map_time_to_tightened(we, keep_ranges)

        if new_end > new_start:
            retimed_words.append({
                "word": w["word"],
                "start": round(new_start, 3),
                "end": round(new_end, 3)
            })

    new_duration = sum(k_end - k_start for k_start, k_end in keep_ranges)
    saved_duration = clip_duration - new_duration

    return {
        "keepRanges": keep_ranges,
        "retimedWords": retimed_words,
        "savedDuration": round(saved_duration, 3),
        "newDuration": round(new_duration, 3)
    }


def _map_time_to_tightened(t: float, keep_ranges: List[Tuple[float, float]]) -> float:
    """Calculate where an absolute timestamp maps on the shortened timeline."""
    elapsed = 0.0
    for k_start, k_end in keep_ranges:
        if t < k_start:
            return elapsed
        if k_start <= t <= k_end:
            return elapsed + (t - k_start)
        elapsed += (k_end - k_start)
    return elapsed
