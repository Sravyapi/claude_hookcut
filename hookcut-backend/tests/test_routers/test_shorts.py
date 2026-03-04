"""Tests for shorts router — get, download, discard."""
from unittest.mock import patch, MagicMock
from tests.conftest import TEST_USER_ID, make_user, make_session, make_hook, make_short


class TestGetShort:
    def test_get_queued_short(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="queued")

        resp = client.get(f"/api/shorts/{short.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == short.id
        assert data["status"] == "queued"
        assert data["is_watermarked"] is True

    def test_get_ready_short(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")
        short.title = "Test Short"
        short.duration_seconds = 28.0
        short.file_size_bytes = 5000000
        db.commit()

        resp = client.get(f"/api/shorts/{short.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test Short"
        assert data["duration_seconds"] == 28.0

    def test_get_nonexistent_short(self, client):
        resp = client.get("/api/shorts/nonexistent-id")
        assert resp.status_code == 404


class TestDownloadShort:
    @patch("app.services.shorts_service.StorageService")
    def test_download_ready_short(self, mock_storage_cls, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")
        short.video_file_key = "shorts/test/video.mp4"
        db.commit()

        mock_storage = mock_storage_cls.return_value
        mock_storage.get_download_url.return_value = "https://storage.example.com/video.mp4"

        resp = client.post(f"/api/shorts/{short.id}/download")
        assert resp.status_code == 200
        data = resp.json()
        assert "download_url" in data
        assert "expires_at" in data

    def test_download_not_ready(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="processing")

        resp = client.post(f"/api/shorts/{short.id}/download")
        assert resp.status_code == 400

    def test_download_no_video_file(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")
        # No video_file_key set

        resp = client.post(f"/api/shorts/{short.id}/download")
        assert resp.status_code == 400

    def test_download_nonexistent(self, client):
        resp = client.post("/api/shorts/nonexistent-id/download")
        assert resp.status_code == 404


class TestDiscardShort:
    def test_discard_short(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        session = make_session(db, TEST_USER_ID)
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id)

        resp = client.post(f"/api/shorts/{short.id}/discard")
        assert resp.status_code == 200
        assert resp.json()["status"] == "discarded"

    def test_discard_nonexistent(self, client):
        resp = client.post("/api/shorts/nonexistent-id/discard")
        assert resp.status_code == 404
