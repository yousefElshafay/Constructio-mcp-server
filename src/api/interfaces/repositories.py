from __future__ import annotations

from typing import Any, Protocol
from models.dtos import Generator


class GeneratorMetadataPort(Protocol):
    async def list_generators(
        self,
        *,
        language: str | None = None,
        version: str | None = None,
        stack: str | None = None,
        tag: list[str] | None = None,
    ) -> list[Generator]: ...

    async def get_generator(self, generator_id: str) -> Generator | None: ...

    async def create_generator(self, body: dict[str, Any]) -> Generator: ...

    async def delete_generator(self, generator_id: str) -> bool: ...


class UploadStoragePort(Protocol):
    async def build_upload_instruction(
        self, generator: Generator
    ) -> dict[str, Any]: ...

    async def get_download_url(self, generator: Generator) -> str | None: ...
