from starlette.requests import Request
from starlette.responses import Response

from .app import mcp_http_app


async def mcp_proxy(request: Request) -> Response:
    scope = dict(request.scope)
    scope["path"] = "/"
    scope["raw_path"] = b"/"
    body_chunks: list[bytes] = []
    status_code = 500
    response_headers: list[tuple[bytes, bytes]] = []

    async def send(message):
        nonlocal status_code, response_headers
        if message.get("type") == "http.response.start":
            status_code = message.get("status", 500)
            response_headers = message.get("headers", [])
        elif message.get("type") == "http.response.body":
            body_chunks.append(message.get("body", b""))

    await mcp_http_app(scope, request.receive, send)
    headers = {key.decode(): value.decode() for key, value in response_headers}
    return Response(
        content=b"".join(body_chunks), status_code=status_code, headers=headers
    )
