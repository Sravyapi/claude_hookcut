import subprocess
import json
import re
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    video_id: str
    title: str
    duration_seconds: float
    is_live: bool
    age_limit: int
    availability: Optional[str]


class VideoMetadataService:
    def fetch(self, video_id: str) -> Optional[VideoMetadata]:
        """Fetch video metadata. Tries YouTube Data API v3 first, falls back to yt-dlp."""
        settings = get_settings()

        if settings.YOUTUBE_API_KEY:
            result = self._fetch_via_api(video_id, settings.YOUTUBE_API_KEY)
            if result:
                return result
            logger.info(f"YouTube API failed for {video_id}, falling back to yt-dlp")

        return self._fetch_via_ytdlp(video_id)

    def _fetch_via_api(self, video_id: str, api_key: str) -> Optional[VideoMetadata]:
        """Fetch metadata via YouTube Data API v3 (reliable from any server)."""
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "id": video_id,
            "part": "snippet,contentDetails,status,liveStreamingDetails",
            "key": api_key,
        }
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            items = data.get("items", [])
            if not items:
                logger.warning(f"YouTube API: video {video_id} not found")
                return None

            item = items[0]
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            status = item.get("status", {})
            live = item.get("liveStreamingDetails")

            duration_str = content.get("duration", "PT0S")
            duration_seconds = self._parse_iso8601_duration(duration_str)

            is_live = live is not None and "actualEndTime" not in (live or {})

            privacy = status.get("privacyStatus", "public")
            availability = privacy if privacy != "public" else "public"

            age_restricted = content.get("contentRating", {}).get("ytRating") == "ytAgeRestricted"

            return VideoMetadata(
                video_id=video_id,
                title=snippet.get("title", ""),
                duration_seconds=duration_seconds,
                is_live=is_live,
                age_limit=18 if age_restricted else 0,
                availability=availability,
            )
        except httpx.HTTPStatusError as e:
            logger.warning(f"YouTube API HTTP error for {video_id}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.warning(f"YouTube API error for {video_id}: {e}")
            return None

    @staticmethod
    def _parse_iso8601_duration(duration: str) -> float:
        """Parse ISO 8601 duration (PT1H2M3S) to seconds."""
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        if not match:
            return 0.0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return float(hours * 3600 + minutes * 60 + seconds)

    def _fetch_via_ytdlp(self, video_id: str) -> Optional[VideoMetadata]:
        """Fetch video metadata via yt-dlp (fallback, may fail on server IPs)."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--no-playlist",
            "--no-warnings",
            "--geo-bypass",
            "--extractor-args", "youtube:player_client=android_creator",
            url,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.warning(f"yt-dlp metadata failed for {video_id}: {result.stderr[:300]}")
                return None

            data = json.loads(result.stdout)

            return VideoMetadata(
                video_id=video_id,
                title=data.get("title", ""),
                duration_seconds=float(data.get("duration", 0)),
                is_live=data.get("is_live", False),
                age_limit=data.get("age_limit", 0),
                availability=data.get("availability"),
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"yt-dlp metadata timed out for {video_id}")
            return None
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"yt-dlp metadata parse error for {video_id}: {e}")
            return None
        except Exception as e:
            logger.warning(f"yt-dlp metadata unexpected error for {video_id}: {e}")
            return None

    def validate_accessibility(self, metadata: VideoMetadata) -> tuple[bool, Optional[str]]:
        """Check if video is accessible for processing. Returns (is_ok, error_message)."""
        if metadata.is_live:
            return False, "Live videos are not supported"
        if metadata.age_limit and metadata.age_limit >= 18:
            return False, "Age-restricted videos are not accessible"
        if metadata.availability and metadata.availability != "public":
            return False, "Video not accessible (may be private or region-restricted)"
        if metadata.duration_seconds <= 0:
            return False, "Could not determine video duration"
        return True, None
