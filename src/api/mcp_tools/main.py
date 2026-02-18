from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from fastmcp.tools.tool_transform import ArgTransformConfig, ToolTransformConfig

from dependencies import build_generator_service
from logger import logger
from models.dtos import (
    Generator,
    GeneratorCreateRequest,
    GeneratorCreateResponse,
    GeneratorListResponse,
    ListGeneratorsQuery,
)

mcp = FastMCP("Constructio")
_service = build_generator_service()

INTERNAL_FIELDS = {"artifact", "entrypoint"}
LIST_FIELDS = {"id", "name", "description", "language", "stack"}

CREATE_GENERATOR_BODY_EXAMPLE = {
    "name": "fastapi-crud",
    "description": "Generates CRUD scaffolding for FastAPI services.",
    "language": "python",
    "stack": "fastapi",
    "version": "1.0.0",
    "tags": ["api", "crud"],
    "entrypoint": "generate.py",
    "upload": {"content_type": "application/zip"},
}


@mcp.tool()
async def list_generators(filters: ListGeneratorsQuery | None = None) -> dict[str, Any]:
    """
    List generators with minimal fields for discovery.
    """
    query = filters or ListGeneratorsQuery()
    logger.info(
        "MCP: list_generators",
        extra={"query": query.model_dump(exclude_none=True)},
    )
    result = await _service.list_generators(**query.model_dump(exclude_none=True))

    response = GeneratorListResponse.model_validate(result)
    items = [
        Generator.model_validate(item).model_dump(
            mode="json",
            exclude_none=True,
            include=LIST_FIELDS,
        )
        for item in response.items
    ]
    return {"items": items}


@mcp.tool()
async def create_generator(body: GeneratorCreateRequest) -> dict[str, Any]:
    request = body

    logger.info("MCP: create_generator", extra={"generator_name": request.name})
    result = await _service.create_generator(request.model_dump(exclude_none=True))

    response = GeneratorCreateResponse.model_validate(result)
    return response.model_dump(
        mode="json",
        exclude_none=True,
        exclude={"generator": INTERNAL_FIELDS, "upload": {"artifact"}},
    )


mcp.add_tool_transformation(
    "create_generator",
    ToolTransformConfig(
        arguments={"body": ArgTransformConfig(examples=[CREATE_GENERATOR_BODY_EXAMPLE])}
    ),
)


@mcp.tool()
async def get_generator(generator_id: str) -> dict[str, Any]:
    generator = await _service.get_generator(generator_id)
    if not generator:
        return {
            "error": "not_found",
            "message": f"Generator '{generator_id}' was not found",
        }

    response = Generator.model_validate(generator)
    return response.model_dump(
        mode="json",
        exclude_none=True,
        exclude=INTERNAL_FIELDS,
    )


@mcp.tool()
async def delete_generator(generator_id: str) -> str | dict[str, Any]:
    deleted = await _service.delete_generator(generator_id)
    if not deleted:
        return {
            "error": "not_found",
            "message": f"Generator '{generator_id}' was not found",
        }
    return ""
