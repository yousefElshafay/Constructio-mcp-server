from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import Language, UploadRequest


class ListGeneratorsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: Language | None = None
    version: str | None = Field(default=None, max_length=32)
    stack: str | None = Field(default=None, max_length=64)
    tag: list[str] | None = None

    @field_validator("tag", mode="before")
    @classmethod
    def normalize_tag(cls, value: Any) -> Any:
        if value is None:
            return value
        if isinstance(value, str):
            return [value]
        return value


class GeneratorCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=3, max_length=80, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    description: str | None = Field(default=None, max_length=2000)
    language: Language
    stack: str | None = Field(default=None, max_length=64)
    version: str | None = Field(default=None, max_length=32)
    tags: list[str] | None = Field(default=None, max_length=30)
    entrypoint: str | None = Field(default=None, max_length=200)
    upload: UploadRequest
