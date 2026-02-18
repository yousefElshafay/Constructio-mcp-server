def test_mcp_delete_generator_round_trip(mcp_call_tool, valid_create_body):
    create_result = mcp_call_tool("create_generator", {"body": valid_create_body})
    generator_id = create_result["generator"]["id"]

    delete_result = mcp_call_tool("delete_generator", {"generator_id": generator_id})
    assert delete_result == ""

    missing_result = mcp_call_tool("delete_generator", {"generator_id": generator_id})
    assert missing_result["error"] == "not_found"
