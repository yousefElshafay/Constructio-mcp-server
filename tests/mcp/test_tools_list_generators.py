def test_mcp_list_generators_returns_minimal_fields(mcp_call_tool):
    result = mcp_call_tool("list_generators")
    items = result["items"]

    assert items
    allowed_keys = {"id", "name", "description", "language", "stack"}

    for item in items:
        assert "id" in item
        assert "name" in item
        assert "language" in item
        assert set(item.keys()).issubset(allowed_keys)
