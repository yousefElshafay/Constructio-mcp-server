def test_mcp_get_generator_returns_item(mcp_call_tool):
    result = mcp_call_tool(
        "get_generator", {"generator_id": "gen_01HTZ7Y4M7Z7W2B8Q6P2"}
    )

    assert result["id"] == "gen_01HTZ7Y4M7Z7W2B8Q6P2"
    assert "artifact" not in result
    assert "entrypoint" not in result


def test_mcp_get_generator_returns_not_found(mcp_call_tool):
    result = mcp_call_tool("get_generator", {"generator_id": "gen_missing"})

    assert result["error"] == "not_found"
