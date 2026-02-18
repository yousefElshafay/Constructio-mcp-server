def test_list_generators_returns_items(client):
    response = client.get("/v1/generators")

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert isinstance(payload["items"], list)

    for item in payload["items"]:
        assert "artifact" not in item
        assert "entrypoint" not in item
