def test_get_generator_returns_item(client):
    response = client.get("/v1/generators/gen_01HTZ7Y4M7Z7W2B8Q6P2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "gen_01HTZ7Y4M7Z7W2B8Q6P2"
    assert "artifact" not in payload
    assert "entrypoint" not in payload


def test_get_generator_returns_not_found(client):
    response = client.get("/v1/generators/gen_missing")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"] == "not_found"
