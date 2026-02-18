from __future__ import annotations

from typing import Any, Protocol


class GeneratorMetadataPort(Protocol):
    def list_generators(
        self,
        *,
        language: str | None = None,
        version: str | None = None,
        stack: str | None = None,
        tag: list[str] | None = None,
    ) -> list[dict[str, Any]]: ...

    def get_generator(self, generator_id: str) -> dict[str, Any] | None: ...

    def create_generator(self, body: dict[str, Any]) -> dict[str, Any]: ...

    def delete_generator(self, generator_id: str) -> bool: ...


class UploadStoragePort(Protocol):
    def build_upload_instruction(self, generator: dict[str, Any]) -> dict[str, Any]: ...
