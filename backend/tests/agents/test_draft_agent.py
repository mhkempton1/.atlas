import pytest
from unittest.mock import MagicMock, patch
from agents.draft_agent import DraftAgent

@pytest.fixture
def mock_altimeter_service():
    with patch("agents.draft_agent.altimeter_service") as mock:
        mock.get_context_for_email.return_value = {
            "project": {"name": "Test Project", "number": "25-0001", "status": "Active"},
            "company_role": "Client",
            "file_context": "Important project info"
        }
        yield mock

@pytest.fixture
def mock_agent_ai_service(mock_ai_service):
    # Patch the ai_service imported in draft_agent.py
    with patch("agents.draft_agent.ai_service", mock_ai_service):
        yield mock_ai_service

@pytest.mark.asyncio
async def test_draft_agent_process(mock_altimeter_service, mock_agent_ai_service):
    # mock_agent_ai_service masks the import in draft_agent
    agent = DraftAgent()
    
    context = {
        "subject": "Inquiry",
        "sender": "client@example.com",
        "body": "When is the project starting?",
        "instructions": "Be polite"
    }
    
    result = await agent.process(context)
    
    assert result["status"] == "generated"
    assert result["draft_text"] == "Mocked AI Response"
    
    # Check if altimeter was called
    mock_altimeter_service.get_context_for_email.assert_called_once_with("client@example.com", "Inquiry")
    
    # Check if ai_service was called with a prompt containing project info
    call_args = mock_agent_ai_service.generate_content.call_args
    prompt = call_args[0][0]
    assert "Test Project" in prompt
    assert "Important project info" in prompt
