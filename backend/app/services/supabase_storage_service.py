"""
supabase_storage_service.py
Uploads audio/video reference files to Supabase Storage and returns a permanent public URL.

This public URL is used in two ways:
  1. Passed to CometAPI Seedance as `input_reference` for beat-sync/lip-sync
  2. Passed to ffmpeg assembly for mixing into the final video

Bucket: settings.SUPABASE_AUDIO_BUCKET (default: "production-audio")
Bucket policy: Public read (set once at bucket creation)
"""

import logging
import mimetypes
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseStorageService:

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy-initialise the Supabase client."""
        if self._client is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in env/.env "
                    "to use audio file hosting."
                )
            from supabase import create_client
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY,
            )
        return self._client

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    async def upload_audio(
        self,
        file_bytes: bytes,
        filename: str,
        job_id: str,
    ) -> dict:
        """
        Upload an audio/video file to Supabase Storage.

        Args:
            file_bytes: Raw file content.
            filename:   Original filename (e.g. 'music.mp3', 'beat.mp4').
            job_id:     Production job ID — used as a path prefix.

        Returns:
            {"public_url": str} on success
            {"error": str}      on failure
        """
        try:
            client = self._get_client()
            bucket = settings.SUPABASE_AUDIO_BUCKET

            # Ensure bucket exists (idempotent)
            self._ensure_bucket(client, bucket)

            # Build storage path:  production-audio/job_id/filename
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            storage_path = f"{job_id}/{filename}"

            # Upload — upsert=True overwrites if re-uploaded
            client.storage.from_(bucket).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )

            public_url = self._public_url(bucket, storage_path)
            logger.info(f"Uploaded {filename} → {public_url}")
            return {"public_url": public_url}

        except ValueError as e:
            # Missing credentials — not a Supabase API error
            logger.error(f"Supabase config error: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Supabase upload failed: {e}")
            return {"error": str(e)}

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        folder: str,
        bucket: Optional[str] = None,
    ) -> dict:
        """
        Generic file upload to Supabase Storage.
        Used for reference sheets, image boards, and other media.

        Args:
            file_bytes: Raw file content.
            filename:   Original filename.
            folder:     Folder prefix (e.g. 'bibles/abc123', 'intake/def456').
            bucket:     Override bucket (defaults to SUPABASE_AUDIO_BUCKET).

        Returns:
            {"public_url": str} on success, {"error": str} on failure.
        """
        try:
            client = self._get_client()
            target_bucket = bucket or settings.SUPABASE_AUDIO_BUCKET

            self._ensure_bucket(client, target_bucket)

            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            storage_path = f"{folder}/{filename}"

            client.storage.from_(target_bucket).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )

            public_url = self._public_url(target_bucket, storage_path)
            logger.info(f"Uploaded {filename} → {public_url}")
            return {"public_url": public_url}

        except Exception as e:
            logger.error(f"Supabase file upload failed: {e}")
            return {"error": str(e)}

    def _public_url(self, bucket: str, path: str) -> str:
        """Construct the public URL from project URL + bucket + path."""
        base = settings.SUPABASE_URL.rstrip("/")
        return f"{base}/storage/v1/object/public/{bucket}/{path}"

    def _ensure_bucket(self, client, bucket: str):
        """Create the bucket with public read access if it doesn't already exist."""
        try:
            existing = [b.name for b in client.storage.list_buckets()]
            if bucket not in existing:
                client.storage.create_bucket(bucket, options={"public": True})
                logger.info(f"Created Supabase bucket: {bucket}")
        except Exception as e:
            # If it already exists the call will raise — that's fine
            logger.debug(f"Bucket check/create: {e}")


supabase_storage = SupabaseStorageService()
