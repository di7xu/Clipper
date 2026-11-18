"""Unit tests for acoustic energy profiling and excitement detection."""
import numpy as np
import pytest
from audio.features import _rolling_median


def test_rolling_median():
    arr = np.array([1.0, 2.0, 10.0, 2.0, 1.0], dtype=np.float32)
    med = _rolling_median(arr, window_size=3)
    assert len(med) == 5
    assert med[2] == 2.0  # Median of [2.0, 10.0, 2.0] is 2.0
