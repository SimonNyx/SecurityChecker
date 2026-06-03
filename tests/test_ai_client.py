import pytest
from unittest.mock import AsyncMock, MagicMock, patch

async def test_ai_client_complete_returns_string():
    from app.worker.ai_client import AIClient
    config = {
        "provider": "openwebui",
        "base_url": "http://localhost:3000",
        "api_key": "",
        "model_name": "llama3",
    }
    client = AIClient(config)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "This is the AI response."}}]
    }
    mock_response.raise_for_status = MagicMock()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await client.complete("Say hello")
    assert result == "This is the AI response."

async def test_ai_client_gemini_provider():
    from app.worker.ai_client import AIClient
    config = {
        "provider": "gemini",
        "base_url": "https://generativelanguage.googleapis.com",
        "api_key": "fake-key",
        "model_name": "gemini-1.5-flash",
    }
    client = AIClient(config)
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Gemini says hello."}]}}]
    }
    mock_response.raise_for_status = MagicMock()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await client.complete("Say hello")
    assert result == "Gemini says hello."
