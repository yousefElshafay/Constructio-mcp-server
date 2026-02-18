from .tools.main import mcp

mcp_http_app = mcp.http_app(
    path="/",
    transport="http",
    stateless_http=True,
    json_response=True,
)

__all__ = ["mcp_http_app", "mcp"]
