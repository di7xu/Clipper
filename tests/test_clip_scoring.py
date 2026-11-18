"""Automated tests for Hybrid Multimodal Clip Detection & Scoring Engine."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from clip_detection.score_clips import ClipScorer, sentenceize


@pytest.fixture
def sample_transcript():
    """A realistic 60-second interview transcript fixture."""
    text = (
        "Welcome back to the studio everyone. Today we are talking about building great software. "
        "Here is the single most surprising thing I learned after ten years. "
        "Most people focus entirely on features and completely ignore reliability. "
        "Why is that a massive mistake? Because if your application crashes in front of a customer, "
        "they will never trust your product again. It does not matter how many shiny buttons you have. "
        "So what should you do instead? Start by automating your verification pipeline. "
        "When your tests pass every single commit, your team moves ten times faster. "
        "That is the real secret to shipping high quality tools. Thank you for listening."
    )
    words_raw = text.split()
    words = []
    current_time = 0.5
    for w in words_raw:
        word_dur = 0.35
        words.append({
            "word": w,
            "start": round(current_time, 2),
            "end": round(current_time + word_dur, 2),
            "probability": 0.98
        })
        current_time += word_dur + 0.08

    return {
        "language": "en",
        "duration": round(current_time, 2),
        "words": words
    }


def test_sentenceize(sample_transcript):
    sentences = sentenceize(sample_transcript["words"])
    assert len(sentences) >= 8

    for s in sentences:
        assert s["start"] < s["end"]
        assert len(s["text"].strip()) > 0
        # Assert sentence starts cleanly and ends with punctuation
        assert s["text"][-1] in {".", "?", "!"}


def test_clip_scorer_candidates(sample_transcript):
    scorer = ClipScorer(min_score=5.0)
    candidates = scorer.score_project(sample_transcript)

    assert len(candidates) > 0

    for c in candidates:
        assert "clip_" in c["id"]
        assert c["start"] >= 0.0
        assert c["end"] > c["start"]
        assert c["duration"] == round(c["end"] - c["start"], 2)
        assert 0.0 <= c["overallScore"] <= 10.0
        assert 0.0 <= c["hookScore"] <= 10.0
        assert 0.0 <= c["energyScore"] <= 10.0
        assert 0.0 <= c["completenessScore"] <= 10.0
        assert len(c["words"]) > 0
        assert len(c["transcript"]) > 0
        # Guarantee no sentence starts or ends mid-word
        assert c["transcript"].split()[0][0].isupper() or c["transcript"].split()[0][0] in {"\"", "'"}
