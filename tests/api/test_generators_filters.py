def test_list_generators_filters_by_language(client):
    response = client.get("/v1/generators", params={"language": "python"})

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["language"] == "python" for item in items)


def test_list_generators_filters_by_stack(client):
    response = client.get("/v1/generators", params={"stack": "fastapi"})

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item.get("stack") == "fastapi" for item in items)


def test_list_generators_filters_by_tag(client):
    response = client.get("/v1/generators", params={"tag": "crud"})

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all("crud" in (item.get("tags") or []) for item in items)
