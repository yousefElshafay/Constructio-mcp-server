def test_tools_list_includes_generators(mcp_call):
    response = mcp_call("tools/list")

    tools = response["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}

    assert {
        "list_generators",
        "create_generator",
        "get_generator",
        "delete_generator",
    }.issubset(tool_names)
