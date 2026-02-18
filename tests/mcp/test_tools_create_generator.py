def test_mcp_create_generator_returns_upload(mcp_call_tool, valid_create_body):
    result = mcp_call_tool("create_generator", {"body": valid_create_body})

    assert "generator" in result
    assert "upload" in result

    generator = result["generator"]
    upload = result["upload"]

    assert generator["name"] == valid_create_body["name"]
    assert "artifact" not in generator
    assert "entrypoint" not in generator
    assert "artifact" not in upload
