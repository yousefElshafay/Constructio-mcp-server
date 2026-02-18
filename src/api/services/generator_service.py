from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from interfaces.repositories import GeneratorMetadataPort, UploadStoragePort
from logger import logger


@dataclass(slots=True)
class GeneratorService:
    metadata: GeneratorMetadataPort
    storage: UploadStoragePort

    async def list_generators(self, **kwargs: Any) -> dict[str, Any]:
        logger.info("Listing generators", extra=kwargs)
        items = await self.metadata.list_generators(
            language=kwargs.get("language"),
            version=kwargs.get("version"),
            stack=kwargs.get("stack"),
            tag=kwargs.get("tag"),
        )
        return {"items": items}

    async def create_generator(self, body: dict[str, Any]) -> dict[str, Any]:
        logger.info("Creating generator", extra={"generator_name": body.get("name")})
        generator = await self.metadata.create_generator(body)
        upload = await self.storage.build_upload_instruction(generator)
        logger.info("Generator created", extra={"id": generator.id})
        return {"generator": generator, "upload": upload}

    async def get_generator(self, generator_id: str) -> Generator | None:
        logger.info("Getting generator", extra={"id": generator_id})
        generator = await self.metadata.get_generator(generator_id)
        if generator:
            download_url = await self.storage.get_download_url(generator)
            generator.download_url = download_url
        return generator

    async def delete_generator(self, generator_id: str) -> bool:
        logger.info("Deleting generator", extra={"id": generator_id})
        return await self.metadata.delete_generator(generator_id)
