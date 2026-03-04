import os
import shutil
import logging
from pathlib import Path
from app.config import get_settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    V0: local filesystem storage.
    V1: Cloudflare R2 (S3-compatible).
    """

    def __init__(self):
        settings = get_settings()
        if settings.FEATURE_R2_STORAGE:
            import boto3
            self.s3 = boto3.client(
                "s3",
                endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                region_name="auto",
            )
            self.bucket = settings.R2_BUCKET_NAME
            self.public_url = settings.R2_PUBLIC_URL
        else:
            self.s3 = None
            self.local_dir = os.path.join(os.getcwd(), "storage")
            os.makedirs(self.local_dir, exist_ok=True)

    def _safe_local_path(self, key: str) -> str:
        """Resolve local path for key and verify it is within the storage directory."""
        base = Path(self.local_dir).resolve()
        dest = (base / key.replace("/", os.sep)).resolve()
        if not str(dest).startswith(str(base) + os.sep) and dest != base:
            raise ValueError(f"Invalid storage key: path traversal detected in '{key}'")
        return str(dest)

    def upload(self, local_path: str, key: str) -> str:
        """Upload file, return access URL or local path."""
        if self.s3:
            content_type = "video/mp4" if key.endswith(".mp4") else "image/jpeg"
            self.s3.upload_file(
                local_path, self.bucket, key,
                ExtraArgs={"ContentType": content_type},
            )
            return f"{self.public_url}/{key}"
        else:
            dest = self._safe_local_path(key)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(local_path, dest)
            return dest

    def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a download URL (presigned for R2, HTTP URL for local V0)."""
        if self.s3:
            return self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        else:
            return f"http://127.0.0.1:8000/api/storage/{key}"

    def delete(self, key: str):
        """Delete a file from storage."""
        if self.s3:
            self.s3.delete_object(Bucket=self.bucket, Key=key)
        else:
            path = self._safe_local_path(key)
            if os.path.exists(path):
                os.remove(path)
                logger.debug(f"Deleted local file: {path}")
