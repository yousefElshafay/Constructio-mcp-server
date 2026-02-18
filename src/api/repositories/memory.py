from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from models.dtos import Generator
from shared.time import now_iso
from interfaces.repositories import GeneratorMetadataPort


@dataclass(slots=True)
class InMemoryMetadataAdapter(GeneratorMetadataPort):
    """Local adapter used for development and testing."""

    _items_by_id: dict[str, Generator] = field(init=False)

    def __post_init__(self) -> None:
        seed_items = [
            {
                "id": "gen_01HTZ7Y4M7Z7W2B8Q6P2",
                "name": "fastapi-crud",
                "description": "Generates CRUD scaffolding for FastAPI services.",
                "language": "python",
                "stack": "fastapi",
                "version": "1.4.0",
                "tags": ["api", "crud", "backend"],
                "entrypoint": "generate.py",
                "upload_status": "ready",
                "artifact": {
                    "bucket": "constructio-generators",
                    "object": "fastapi-crud/1.4.0/generator.zip",
                    "content_type": "application/zip",
                },
                "created_at": "2026-02-10T12:00:00Z",
                "updated_at": "2026-02-14T16:30:00Z",
            },
            {
                "id": "gen_01HTZZAFW5Q2Y8G6M1D9",
                "name": "nestjs-module",
                "description": "Creates baseline NestJS modules with tests.",
                "language": "typescript",
                "stack": "nestjs",
                "version": "0.9.1",
                "tags": ["backend", "module", "typescript"],
                "entrypoint": "bin/generate",
                "upload_status": "uploaded",
                "artifact": {
                    "bucket": "constructio-generators",
                    "object": "nestjs-module/0.9.1/generator.zip",
                    "content_type": "application/zip",
                },
                "created_at": "2026-02-09T08:45:00Z",
                "updated_at": "2026-02-15T10:10:00Z",
            },
            {
                "id": "gen_01HU04G8MK2BBYMS0QW3",
                "name": "laravel-crud-module",
                "description": "Scaffolds a Laravel CRUD module with migrations.",
                "language": "php",
                "stack": "laravel",
                "version": "2.0.0",
                "tags": ["php", "laravel", "crud"],
                "entrypoint": "bin/generate",
                "upload_status": "pending",
                "artifact": {
                    "bucket": "constructio-generators",
                    "object": "laravel-crud-module/2.0.0/generator.zip",
                    "content_type": "application/zip",
                },
                "created_at": "2026-02-12T09:20:00Z",
                "updated_at": "2026-02-12T09:20:00Z",
            },
        ]
        self._items_by_id = {
            item["id"]: Generator.model_validate(item) for item in seed_items
        }

    async def list_generators(
        self,
        *,
        language: str | None = None,
        version: str | None = None,
        stack: str | None = None,
        tag: list[str] | None = None,
    ) -> list[Generator]:
        items = list(self._items_by_id.values())

        if language:
            items = [item for item in items if item.language == language]
        if version:
            items = [item for item in items if item.version == version]
        if stack:
            items = [item for item in items if item.stack == stack]
        if tag:
            required_tags = {value.casefold() for value in tag}
            items = [
                item
                for item in items
                if required_tags.issubset(
                    {value.casefold() for value in (item.tags or [])}
                )
            ]

        items.sort(key=lambda item: str(item.updated_at), reverse=True)
        return [deepcopy(item) for item in items]

    async def get_generator(self, generator_id: str) -> Generator | None:
        item = self._items_by_id.get(generator_id)
        return deepcopy(item) if item else None

    async def create_generator(self, body: dict[str, Any]) -> Generator:
        now = now_iso()
        generator_id = f"gen_{uuid4().hex[:12]}"
        artifact = {
            "bucket": "constructio-generators",
            "object": f"{generator_id}/generator.zip",
            "content_type": body.get("upload", {}).get(
                "content_type", "application/zip"
            ),
        }
        item_data = {
            "id": generator_id,
            "name": body["name"],
            "description": body.get("description"),
            "language": body["language"],
            "stack": body.get("stack"),
            "version": body.get("version"),
            "tags": body.get("tags", []),
            "entrypoint": body.get("entrypoint"),
            "upload_status": "pending",
            "artifact": artifact,
            "created_at": now,
            "updated_at": now,
        }
        generator = Generator.model_validate(item_data)
        self._items_by_id[generator_id] = generator
        return deepcopy(generator)

    async def delete_generator(self, generator_id: str) -> bool:
        return self._items_by_id.pop(generator_id, None) is not None
