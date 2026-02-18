from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Language = Literal[
    "python", "typescript", "javascript", "php", "csharp", "java", "go", "rust", "other"
]


class ArtifactRef(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bucket: str | None = Field(default=None, max_length=120)
    object: str | None = Field(default=None, max_length=1024)
    content_type: str | None = Field(default="application/zip", max_length=100)
    size_bytes: int | None = Field(default=None, ge=0)
    sha256: str | None = Field(default=None, max_length=64)


UploadStatus = Literal["pending", "uploaded", "ready", "failed"]


class Generator(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    description: str | None = None
    language: str  # Simplified from Language enum to avoid validation complexity if not needed
    stack: str | None = None
    version: str | None = None
    tags: list[str] = []
    entrypoint: str | None = None
    upload_status: str
    artifact: ArtifactRef | None = None
    created_at: str | None = None
    updated_at: str | None = None
    download_url: str | None = None
    download_expires_at: str | None = None


class UploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_type: str = Field(default="application/zip", max_length=100)


class UploadInstruction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    upload_url: str
    expires_at: str
    method: str = "PUT"
    headers: dict[str, str] = {}


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    error: str
    message: str
    details: dict[str, Any] | None = None
