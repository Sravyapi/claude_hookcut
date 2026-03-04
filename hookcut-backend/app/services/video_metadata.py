import subprocess
import json
import logging
from dataclasses import dataclass
from typing import Optional

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
        """Fetch video metadata via yt-dlp without downloading the video."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--no-playlist",
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
