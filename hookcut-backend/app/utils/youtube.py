import re
from typing import Optional


YOUTUBE_PATTERNS = [
    # Standard watch URL
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?(?:.*&)?v=([a-zA-Z0-9_-]{11})",
    # Short URL
    r"(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})",
    # Shorts URL
    r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    # Embed URL
    r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    # Mobile URL
    r"(?:https?://)?m\.youtube\.com/watch\?(?:.*&)?v=([a-zA-Z0-9_-]{11})",
]


def extract_video_id(url: str) -> Optional[str]:
    url = url.strip()
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def validate_youtube_url(url: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Returns (is_valid, video_id, error_message)."""
    if not url or not isinstance(url, str):
        return False, None, "URL is required"

    url = url.strip()
    if not url.startswith(("http://", "https://", "youtu.be/", "youtube.com/")):
        return False, None, "URL must be a valid YouTube link"

    video_id = extract_video_id(url)
    if not video_id:
        return (
            False,
            None,
            "Could not extract video ID. Supported formats: "
            "youtube.com/watch?v=ID, youtu.be/ID, youtube.com/shorts/ID, youtube.com/embed/ID",
        )

    return True, video_id, None
