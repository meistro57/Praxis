from unittest.mock import patch, MagicMock
from app.services.llm_client import LLMClient
from config import Settings
from pydantic import BaseModel

class DummyResponse(BaseModel):
    reply: str

def test_llm_client_routing_direct_deepseek():
    # Test that direct deepseek routing is active and translates models correctly
    config = Settings(
        DEEPSEEK_API_KEY="test_deepseek_key",
        DEEPSEEK_BASE_URL="https://api.deepseek.com",
        DEEPSEEK_REASONER_MODEL="deepseek-reasoner",
        OPENROUTER_API_KEY="test_openrouter_key",
        OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
    )
    client = LLMClient(config)
    
    # 1. Routing for reasoner model
    headers, url = client._get_headers_and_url("deepseek/deepseek-r1")
    assert url == "https://api.deepseek.com/chat/completions"
    assert headers["Authorization"] == "Bearer test_deepseek_key"
    
    # Test payload generation via generate_completions mocking
    with patch.object(client.client, "post") as mock_post:
        # Mock response to avoid real network call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"reply": "test"}'}}],
            "usage": {}
        }
        mock_post.return_value = mock_response
        
        client.generate_completions(
            system_prompt="sys",
            user_prompt="user",
            model="deepseek/deepseek-r1",
            response_model=DummyResponse
        )
        
        # Verify call arguments
        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        called_payload = called_kwargs["json"]
        
        # Reasoner model should map to DEEPSEEK_REASONER_MODEL and omit temperature
        assert called_payload["model"] == "deepseek-reasoner"
        assert "temperature" not in called_payload

def test_llm_client_routing_direct_deepseek_chat():
    config = Settings(
        DEEPSEEK_API_KEY="test_deepseek_key",
        DEEPSEEK_BASE_URL="https://api.deepseek.com",
        DEEPSEEK_REASONER_MODEL="deepseek-reasoner",
        OPENROUTER_API_KEY="test_openrouter_key",
        OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
    )
    client = LLMClient(config)
    
    # 2. Routing for chat model
    with patch.object(client.client, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"reply": "test"}'}}],
            "usage": {}
        }
        mock_post.return_value = mock_response
        
        client.generate_completions(
            system_prompt="sys",
            user_prompt="user",
            model="deepseek/deepseek-chat",
            response_model=DummyResponse
        )
        
        # Chat model should map to deepseek-chat and keep temperature
        called_payload = mock_post.call_args[1]["json"]
        assert called_payload["model"] == "deepseek-chat"
        assert called_payload["temperature"] == 0.0

def test_llm_client_routing_openrouter():
    # If DEEPSEEK_API_KEY is not set, deepseek model should route to OpenRouter
    config = Settings(
        DEEPSEEK_API_KEY=None,
        OPENROUTER_API_KEY="test_openrouter_key",
        OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
    )
    client = LLMClient(config)
    
    headers, url = client._get_headers_and_url("deepseek/deepseek-r1")
    assert url == "https://openrouter.ai/api/v1/chat/completions"
    assert headers["Authorization"] == "Bearer test_openrouter_key"
    
    with patch.object(client.client, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"reply": "test"}'}}],
            "usage": {}
        }
        mock_post.return_value = mock_response
        
        client.generate_completions(
            system_prompt="sys",
            user_prompt="user",
            model="deepseek/deepseek-r1",
            response_model=DummyResponse
        )
        
        called_payload = mock_post.call_args[1]["json"]
        assert called_payload["model"] == "deepseek/deepseek-r1"
        assert called_payload["temperature"] == 0.0
