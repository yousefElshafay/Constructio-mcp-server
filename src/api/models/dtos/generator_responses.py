from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .common import Generator, UploadInstruction


class GeneratorListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[Generator]


class GeneratorCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generator: Generator
    upload: UploadInstruction
