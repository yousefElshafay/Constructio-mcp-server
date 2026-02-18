def test_create_generator_rejects_invalid_name(client, valid_create_body):
    invalid_body = dict(valid_create_body)
    invalid_body["name"] = "BadName"

    response = client.post("/v1/generators", json=invalid_body)

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"].lower().replace(" ", "_") == "bad_request"
