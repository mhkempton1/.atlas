import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from agents.calendar_agent import CalendarAgent
from datetime import datetime

@pytest.fixture
def mock_ai_service():
    with patch("agents.calendar_agent.ai_service") as mock:
        mock.generate_content = AsyncMock()
        mock.generate_content.return_value = '{"is_event": true, "event": {"title": "Team Sync", "start_time": "2025-02-01T10:00:00", "end_time": "2025-02-01T11:00:00", "location": "Conf Room A", "attendees": ["bob@example.com"]}}'
        yield mock

@pytest.mark.asyncio
async def test_calendar_extraction(mock_ai_service):
    agent = CalendarAgent()
    context = {
        "subject": "Team Sync",
        "sender": "alice@example.com",
        "body": "Let's meet on Feb 1st at 10am in Conf Room A.",
        "message_id": "msg_456"
    }
    
    result = await agent.process(context)
    
    assert result["status"] == "success"
    assert result["data"]["is_event"] is True
    event = result["data"]["event"]
    assert event["title"] == "Team Sync"
    assert event["location"] == "Conf Room A"
    assert "bob@example.com" in event["attendees"]
    assert result["data"]["source_id"] == "msg_456"

@pytest.mark.asyncio
async def test_no_event_found(mock_ai_service):
    mock_ai_service.generate_content.return_value = '{"is_event": false, "event": null}'
    
    agent = CalendarAgent()
    result = await agent.process({"body": "Just saying hi"})
    
    assert result["status"] == "success"
    assert result["data"]["is_event"] is False
    assert result["data"]["event"] is None
