from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from models.dtos import Generator
from shared.time import now_iso
from interfaces.repositories import GeneratorMetadataPort
from repositories.base import FirestoreRepository


class FirestoreMetadataAdapter(FirestoreRepository[Generator], GeneratorMetadataPort):
    def __init__(self, project_id: str, database_id: str, collection_name: str):
        super().__init__(
            project_id=project_id,
            database_id=database_id,
            collection_name=collection_name,
            model_type=Generator,
        )

    async def list_generators(
        self,
        *,
        language: str | None = None,
        version: str | None = None,
        stack: str | None = None,
        tag: list[str] | None = None,
    ) -> list[Generator]:
        filters = []
        if language:
            filters.append(("language", "==", language))
        if version:
            filters.append(("version", "==", version))
        if stack:
            filters.append(("stack", "==", stack))

        items = await self.list_all(filters=filters)

        if tag:
            required_tags = {t.casefold() for t in tag}
            items = [
                item
                for item in items
                if required_tags.issubset({val.casefold() for val in (item.tags or [])})
            ]

        items.sort(key=lambda x: x.updated_at, reverse=True)
        return items

    async def get_generator(self, generator_id: str) -> Generator | None:
        return await self.get(generator_id)

    async def create_generator(self, body: dict[str, Any]) -> Generator:
        now = now_iso()
        generator_id = f"gen_{uuid4().hex[:12]}"

        artifact = {
            "bucket": body.get("upload", {}).get("bucket") or "",
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
        return await self.save(generator_id, generator)

    async def delete_generator(self, generator_id: str) -> bool:
        return await self.delete(generator_id)
