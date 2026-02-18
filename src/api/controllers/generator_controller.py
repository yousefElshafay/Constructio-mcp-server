from __future__ import annotations

from typing import Any

from dependencies import build_generator_service
from logger import logger
from models.dtos import (
    Generator,
    GeneratorCreateRequest,
    GeneratorCreateResponse,
    GeneratorListResponse,
    ListGeneratorsQuery,
)

_service = build_generator_service()

# Fields to prune from public API responses
INTERNAL_FIELDS = {"artifact", "entrypoint"}


async def list_generators(**kwargs) -> dict[str, Any]:
    # Validation handled by middleware/connexion
    query = ListGeneratorsQuery.model_validate(kwargs)

    logger.info(
        "Controller: list_generators",
        extra={"query": query.model_dump(exclude_none=True)},
    )
    result = await _service.list_generators(**query.model_dump(exclude_none=True))

    response = GeneratorListResponse.model_validate(result)
    return response.model_dump(
        mode="json",
        exclude_none=True,
        exclude={"items": {i: INTERNAL_FIELDS for i in range(len(result.get("items", [])))}}
        if isinstance(result, dict) else {"items": {i: INTERNAL_FIELDS for i in range(len(result.items))}}
    )


async def create_generator(body) -> tuple[dict[str, Any], int]:
    request = GeneratorCreateRequest.model_validate(body)

    logger.info("Controller: create_generator", extra={"generator_name": request.name})
    result = await _service.create_generator(request.model_dump(exclude_none=True))

    response = GeneratorCreateResponse.model_validate(result)
    return response.model_dump(
        mode="json", 
        exclude_none=True, 
        exclude={"generator": INTERNAL_FIELDS, "upload": {"artifact"}}
    ), 201


async def get_generator(generatorId) -> dict[str, Any] | tuple[dict[str, Any], int]:
    generator = await _service.get_generator(generatorId)
    if not generator:
        # We can eventually use a proper NotFoundException
        # For now, return 404 manually or raise exception
        return {
            "error": "not_found",
            "message": f"Generator '{generatorId}' was not found",
        }, 404

    response = Generator.model_validate(generator)
    return response.model_dump(mode="json", exclude_none=True, exclude=INTERNAL_FIELDS)


async def delete_generator(generatorId) -> tuple[str, int] | tuple[dict[str, Any], int]:
    deleted = await _service.delete_generator(generatorId)
    if not deleted:
        return {
            "error": "not_found",
            "message": f"Generator '{generatorId}' was not found",
        }, 404
    return "", 204
