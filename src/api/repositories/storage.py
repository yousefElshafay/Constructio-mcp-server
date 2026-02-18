from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

try:
    import google.cloud.storage as storage
except ImportError:
    storage = None  # type: ignore

from interfaces.repositories import UploadStoragePort
from shared.time import to_iso


@dataclass(slots=True)
class FakeSignedUploadAdapter(UploadStoragePort):
    """Local adapter used until GCS signed URL generation is wired."""

    base_url: str = "https://example.com/upload"
    expires_at: str = "2026-02-16T00:10:00Z"

    async def build_upload_instruction(self, generator: Generator) -> dict[str, Any]:
        artifact = generator.artifact.model_dump() if generator.artifact else {}
        return {
            "upload_url": f"{self.base_url}/{generator.id}/generator.zip",
            "expires_at": self.expires_at,
            "method": "PUT",
            "headers": {},
            "artifact": artifact,
        }

    async def get_download_url(self, generator: Generator) -> str | None:
        return f"{self.base_url}/{generator.id}/download"


@dataclass(slots=True)
class GCSSignedUploadAdapter(UploadStoragePort):
    project_id: str
    bucket_name: str
    expiry_seconds: int = 600
    _client: Any = field(init=False, repr=False)
    _bucket: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if storage is None:
            raise ImportError("google-cloud-storage is not installed.")

        # Client init is sync but fast (lazily connects usually)
        self._client = storage.Client(project=self.project_id)
        self._bucket = self._client.bucket(self.bucket_name)

    async def build_upload_instruction(self, generator: Generator) -> dict[str, Any]:
        # Prepare artifact metadata
        if generator.artifact:
            artifact_data = generator.artifact.model_dump()
        else:
            artifact_data = {}

        artifact_data["bucket"] = self.bucket_name
        artifact_object = (
            artifact_data.get("object")
            or f"{generator.id}/generator.zip"
        )
        artifact_data["object"] = artifact_object
        content_type = artifact_data.get("content_type") or "application/zip"
        artifact_data["content_type"] = content_type

        # Run blocking GCS call in a thread
        loop = asyncio.get_running_loop()
        upload_url, expires_at = await loop.run_in_executor(
            None,
            self._generate_signed_url_sync,
            artifact_object,
            content_type,
            "PUT",
        )

        return {
            "upload_url": upload_url,
            "expires_at": to_iso(expires_at),
            "method": "PUT",
            "headers": {"Content-Type": content_type},
            "artifact": artifact_data,
        }

    async def get_download_url(self, generator: Generator) -> str | None:
        if not generator.artifact or not generator.artifact.object:
            return None

        # Check if object exists (blocking call, run in thread)
        loop = asyncio.get_running_loop()
        blob = self._bucket.blob(generator.artifact.object)
        exists = await loop.run_in_executor(None, blob.exists)
        
        if not exists:
            return None

        # Generate signed URL for GET (blocking call, run in thread)
        download_url, _ = await loop.run_in_executor(
            None,
            self._generate_signed_url_sync,
            generator.artifact.object,
            None, # No content-type for GET
            "GET",
        )
        return download_url

    def _generate_signed_url_sync(
        self, blob_name: str, content_type: str | None, method: str = "PUT"
    ) -> tuple[str, datetime]:
        blob = self._bucket.blob(blob_name)
        expires_at = datetime.now(UTC) + timedelta(seconds=self.expiry_seconds)

        args = {
            "version": "v4",
            "expiration": expires_at,
            "method": method,
        }
        if content_type:
            args["content_type"] = content_type

        url = blob.generate_signed_url(**args)
        return url, expires_at
