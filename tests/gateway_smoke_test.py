import os
import time

import httpx


class TestApiGatewaySmoke:
    base_url = os.getenv("GATEWAY_HOST")

    def _headers(self) -> dict[str, str]:
        if not self.base_url:
            raise RuntimeError("GATEWAY_HOST is required for gateway tests")
        bearer_token = os.getenv("API_BEARER_TOKEN")
        if not bearer_token:
            raise RuntimeError("API_BEARER_TOKEN is required for gateway tests")
        return {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def test_list_generators(self) -> None:
        response = httpx.get(
            f"{self.base_url}/v1/generators",
            headers=self._headers(),
            timeout=30.0,
        )
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, dict)
        assert "items" in payload

    def test_create_generator_signed_url(self) -> None:
        timestamp = int(time.time())
        payload = {
            "name": f"gw-smoke-{timestamp}",
            "language": "python",
            "upload": {"content_type": "application/zip"},
        }
        response = httpx.post(
            f"{self.base_url}/v1/generators",
            headers=self._headers(),
            json=payload,
            timeout=30.0,
        )
        assert response.status_code == 201
        body = response.json()
        assert "upload" in body
        assert "upload_url" in body["upload"]
        assert "expires_at" in body["upload"]

    def test_mcp_tools_list(self) -> None:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        }
        response = httpx.post(
            f"{self.base_url}/v1/mcp",
            headers=self._headers(),
            json=payload,
            timeout=30.0,
        )
        assert response.status_code == 200
        body = response.json()
        assert "result" in body
        assert "tools" in body["result"]
