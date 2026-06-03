from unittest.mock import AsyncMock

async def test_resolve_product_parses_json():
    from app.worker.product_lookup import resolve_product
    from app.worker.ai_client import AIClient

    mock_config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(mock_config)
    client.complete = AsyncMock(return_value='{"name":"Slack","vendor":"Salesforce","url":"https://slack.com","confidence":"high","description":"Team messaging"}')

    result = await resolve_product("Slack", client)
    assert result["name"] == "Slack"
    assert result["vendor"] == "Salesforce"
    assert result["confidence"] == "high"

async def test_resolve_product_handles_bad_json():
    from app.worker.product_lookup import resolve_product
    from app.worker.ai_client import AIClient

    mock_config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(mock_config)
    client.complete = AsyncMock(return_value="I cannot identify that product.")

    result = await resolve_product("??gibberish??", client)
    assert result["name"] == "??gibberish??"
    assert result["confidence"] == "low"
