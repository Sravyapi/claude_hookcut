"""Tests for StorageService (local mode)."""
import os
import tempfile
import pytest
from unittest.mock import patch
from app.services.storage import StorageService


@pytest.fixture
def storage(tmp_path, monkeypatch):
    """Create a StorageService in local mode using a temp directory."""
    monkeypatch.setenv("FEATURE_R2_STORAGE", "false")
    # Patch get_settings to return local mode
    from app.config import Settings
    mock_settings = Settings(FEATURE_R2_STORAGE=False)
    with patch("app.services.storage.get_settings", return_value=mock_settings):
        svc = StorageService()
        svc.local_dir = str(tmp_path / "storage")
        os.makedirs(svc.local_dir, exist_ok=True)
        yield svc


class TestLocalStorage:
    def test_upload_creates_file(self, storage, tmp_path):
        # Create a source file
        src = tmp_path / "test.mp4"
        src.write_text("fake video content")

        result = storage.upload(str(src), "shorts/test/video.mp4")
        assert os.path.exists(result)
        assert "video.mp4" in result

    def test_get_download_url_returns_path(self, storage, tmp_path):
        src = tmp_path / "test2.mp4"
        src.write_text("content")
        storage.upload(str(src), "shorts/test2/video.mp4")

        url = storage.get_download_url("shorts/test2/video.mp4")
        assert url == "http://127.0.0.1:8000/api/storage/shorts/test2/video.mp4"

    def test_delete_removes_file(self, storage, tmp_path):
        src = tmp_path / "test3.mp4"
        src.write_text("content")
        path = storage.upload(str(src), "shorts/test3/video.mp4")
        assert os.path.exists(path)

        storage.delete("shorts/test3/video.mp4")
        assert not os.path.exists(path)

    def test_delete_nonexistent_no_error(self, storage):
        storage.delete("nonexistent/file.mp4")  # Should not raise

    def test_path_traversal_blocked(self, storage):
        with pytest.raises(ValueError, match="path traversal"):
            storage._safe_local_path("../../etc/passwd")

    def test_nested_directory_creation(self, storage, tmp_path):
        src = tmp_path / "deep.mp4"
        src.write_text("content")
        result = storage.upload(str(src), "a/b/c/d/video.mp4")
        assert os.path.exists(result)
