import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from agents.task_agent import TaskAgent

@pytest.fixture
def mock_ai_service():
    with patch("agents.task_agent.ai_service") as mock:
        mock.generate_content = AsyncMock()
        mock.generate_content.return_value = '{"tasks": [{"title": "Review Proposal", "description": "Check the budget.", "priority": "High", "due_date": "2025-02-01", "confidence": 0.9, "evidence": "Please review the attached proposal by Friday."}]}'
        yield mock

@pytest.mark.asyncio
async def test_task_extraction(mock_ai_service):
    agent = TaskAgent()
    context = {
        "subject": "Urgent: Proposal Review",
        "sender": "boss@example.com",
        "body": "Please review the attached proposal by Friday.",
        "message_id": "msg_123"
    }
    
    result = await agent.process(context)
    
    assert result["status"] == "success"
    tasks = result["data"]["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Review Proposal"
    assert tasks[0]["priority"] == "High"
    assert tasks[0]["source_id"] == "msg_123"
    assert tasks[0]["confidence"] == 0.9
    assert tasks[0]["evidence"] == "Please review the attached proposal by Friday."
    
@pytest.mark.asyncio
async def test_task_extraction_error(mock_ai_service):
    mock_ai_service.generate_content.return_value = "Invalid JSON"
    
    agent = TaskAgent()
    result = await agent.process({"body": "test"})
    
    assert result["status"] == "error"
