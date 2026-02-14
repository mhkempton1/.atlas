import pytest
from unittest.mock import MagicMock, patch
from services.ai_service import GeminiService
from core.config import settings

@pytest.fixture
def ai_service_instance(monkeypatch):
    # Mock settings to have an API key
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake_key")
    with patch("google.genai.Client") as mock_client:
        service = GeminiService()
        return service, mock_client

@pytest.mark.asyncio
async def test_generate_content_success(ai_service_instance):
    service, mock_client_class = ai_service_instance
    mock_client = mock_client_class.return_value
    
    # Mock response
    mock_response = MagicMock()
    mock_response.text = "Generated AI Content"
    mock_client.models.generate_content.return_value = mock_response
    
    result = await service.generate_content("Hello")
    assert result == "Generated AI Content"
    mock_client.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_generate_content_no_key(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    service = GeminiService()
    
    result = await service.generate_content("Hello")
    assert "AI Service Unavailable" in result

@pytest.mark.asyncio
async def test_generate_content_api_error(ai_service_instance):
    service, mock_client_class = ai_service_instance
    mock_client = mock_client_class.return_value
    
    # Mock API exception
    mock_client.models.generate_content.side_effect = Exception("API Error")
    
    result = await service.generate_content("Hello")
    assert "Error generating content" in result

@pytest.mark.asyncio
async def test_generate_content_json_mode(ai_service_instance):
    service, mock_client_class = ai_service_instance
    mock_client = mock_client_class.return_value

    # Mock response
    mock_response = MagicMock()
    mock_response.text = '{"key": "value"}'
    mock_client.models.generate_content.return_value = mock_response

    result = await service.generate_content("Hello", json_mode=True)
    assert result == '{"key": "value"}'

    # Verify config passed
    mock_client.models.generate_content.assert_called_with(
        model='gemini-2.0-flash',
        contents='Hello',
        config={'response_mime_type': 'application/json'}
    )
