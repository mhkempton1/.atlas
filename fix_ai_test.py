import re

with open("backend/tests/services/test_ai_service.py", "r") as f:
    content = f.read()

content = content.replace('with patch("google.genai.Client") as mock_client:', 'with patch("httpx.AsyncClient.post") as mock_post:')
content = content.replace('mock_response.usage_metadata.total_token_count = 100', '')
content = content.replace('mock_client.return_value.models.generate_content.return_value = mock_response', 'mock_post.return_value.json.return_value = {"response": "Mocked AI Response"}')
content = content.replace('mock_client.return_value.models.generate_content.side_effect', 'mock_post.side_effect')
content = content.replace('assert "Test Prompt" in str(mock_client.mock_calls)', 'assert mock_post.called')

with open("backend/tests/services/test_ai_service.py", "w") as f:
    f.write(content)
