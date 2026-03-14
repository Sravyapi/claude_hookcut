"""Tests for face detection and speaker mapping."""
import pytest
from unittest.mock import patch, MagicMock

from app.utils.face_mapping import (
    _cluster_by_gaps,
    FaceRegion,
)


class TestClusterByGaps:
    def test_empty(self):
        assert _cluster_by_gaps([], 2, 1920) == []

    def test_single_cluster(self):
        data = [(100, (90, 50, 20, 20)), (110, (100, 50, 20, 20)), (120, (110, 50, 20, 20))]
        result = _cluster_by_gaps(data, 1, 1920)
        assert len(result) == 1
        assert len(result[0]) == 3

    def test_two_clusters(self):
        data = [
            (100, (90, 50, 20, 20)),
            (110, (100, 50, 20, 20)),
            (900, (890, 50, 20, 20)),
            (910, (900, 50, 20, 20)),
        ]
        result = _cluster_by_gaps(data, 2, 1920)
        assert len(result) == 2
        assert all(d[0] <= 200 for d in result[0])
        assert all(d[0] >= 800 for d in result[1])

    def test_three_clusters(self):
        data = [
            (100, (90, 50, 20, 20)),
            (500, (490, 50, 20, 20)),
            (900, (890, 50, 20, 20)),
        ]
        result = _cluster_by_gaps(data, 3, 1920)
        assert len(result) == 3

    def test_fewer_gaps_than_target(self):
        """When only 1 detection, requesting 2 clusters returns 1."""
        data = [(100, (90, 50, 20, 20))]
        result = _cluster_by_gaps(data, 2, 1920)
        assert len(result) == 1


class TestDetectSpeakerFaces:
    def test_no_opencv_returns_empty(self):
        """Returns empty list when cv2 import fails inside function."""
        import app.utils.face_mapping as fm

        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        def mock_import(name, *args, **kwargs):
            if name == "cv2":
                raise ImportError("no cv2")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = fm.detect_speaker_faces("/fake/path.mp4", 2)
            assert result == []
