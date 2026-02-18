def test_delete_generator_round_trip(client, valid_create_body):
    create_response = client.post("/v1/generators", json=valid_create_body)
    generator_id = create_response.json()["generator"]["id"]

    delete_response = client.delete(f"/v1/generators/{generator_id}")
    assert delete_response.status_code == 204

    missing_response = client.delete(f"/v1/generators/{generator_id}")
    assert missing_response.status_code == 404
