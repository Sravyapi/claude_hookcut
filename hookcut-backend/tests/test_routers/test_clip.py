"""Tests for the clip router endpoints."""

import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import make_user, TEST_USER_ID


class TestGenerateClipsEndpoint:
    """POST /api/clips/generate tests."""

    def test_requires_auth(self, unauthed_client):
        response = unauthed_client.post(
            "/api/clips/generate",
            json={
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "clips": [{"start_time": 0, "end_time": 30}],
            },
        )
        assert response.status_code in (401, 403)

    def test_validation_error_empty_clips(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        response = client.post(
            "/api/clips/generate",
            json={
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "clips": [],
            },
        )
        assert response.status_code == 422

    def test_validation_error_too_many_clips(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        response = client.post(
            "/api/clips/generate",
            json={
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "clips": [{"start_time": i * 10, "end_time": i * 10 + 5} for i in range(11)],
            },
        )
        assert response.status_code == 422

    def test_validation_error_short_clip(self, client, db):
        make_user(db, user_id=TEST_USER_ID)
        response = client.post(
            "/api/clips/generate",
            json={
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "clips": [{"start_time": 0, "end_time": 2}],
            },
        )
        assert response.status_code == 422

    @patch("app.services.clip_service.generate_short")
    @patch("app.services.clip_service.validate_youtube_url", return_value=(True, "dQw4w9WgXcQ", None))
    def test_success(self, mock_validate, mock_task, client, db):
        mock_task.delay.return_value = MagicMock(id="task-1")
        make_user(db, user_id=TEST_USER_ID, plan_tier="pro")

        response = client.post(
            "/api/clips/generate",
            json={
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "clips": [{"start_time": 10, "end_time": 40}],
                "aspect_ratio": "1:1",
                "caption_style": "bold",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["task_ids"]) == 1
        assert data["is_free_reclip"] is False
