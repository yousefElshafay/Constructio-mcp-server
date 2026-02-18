def test_create_generator_returns_upload(client, valid_create_body):
    response = client.post("/v1/generators", json=valid_create_body)

    assert response.status_code == 201
    payload = response.json()
    assert "generator" in payload
    assert "upload" in payload

    generator = payload["generator"]
    upload = payload["upload"]

    assert generator["name"] == valid_create_body["name"]
    assert "artifact" not in generator
    assert "entrypoint" not in generator
    assert "artifact" not in upload
