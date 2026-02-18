from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "src" / "api"


def _clear_api_modules() -> None:
    prefixes = (
        "app",
        "config",
        "dependencies",
        "mcp",
        "repositories",
        "services",
        "interfaces",
        "models",
        "controllers",
        "middleware",
        "shared",
    )
    for name in list(sys.modules):
        if name == "app" or name.startswith(prefixes):
            sys.modules.pop(name, None)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("USE_IN_MEMORY_ADAPTERS", "true")

    if str(API_PATH) not in sys.path:
        sys.path.insert(0, str(API_PATH))

    _clear_api_modules()
    app_module = importlib.import_module("app")

    with TestClient(app_module.app) as test_client:
        yield test_client


@pytest.fixture()
def valid_create_body() -> dict[str, object]:
    return {
        "name": "test-generator",
        "description": "Generates a sample project.",
        "language": "python",
        "stack": "fastapi",
        "version": "1.0.0",
        "tags": ["api", "test"],
        "entrypoint": "generate.py",
        "upload": {"content_type": "application/zip"},
    }


@pytest.fixture()
def mcp_call(client: TestClient):
    def _call(
        method: str, params: dict[str, object] | None = None
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "jsonrpc": "2.0",
            "id": "test",
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        response = client.post(
            "/mcp/",
            json=payload,
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 200
        return response.json()

    return _call


@pytest.fixture()
def mcp_call_tool(mcp_call):
    def _call(
        name: str, arguments: dict[str, object] | None = None
    ) -> dict[str, object]:
        params: dict[str, object] = {"name": name, "arguments": arguments or {}}
        response = mcp_call("tools/call", params)
        result = response.get("result", {})
        if isinstance(result, dict) and "structuredContent" in result:
            structured = result["structuredContent"]
            if isinstance(structured, dict) and set(structured.keys()) == {"result"}:
                return structured["result"]
            return structured
        return result

    return _call
