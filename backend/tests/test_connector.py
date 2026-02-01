import pytest
from backend.app.services.altimeter_connector import AltimeterConnector

def test_connector_init():
    """Test connector initialization"""
    connector = AltimeterConnector(altimeter_api_url="http://test-url")
    assert connector.base_url == "http://test-url"

def test_get_active_projects_safe_fail():
    """Test that connection failure handles gracefully (doesn't crash Atlas)"""
    connector = AltimeterConnector(altimeter_api_url="http://invalid-url")
    projects = connector.get_active_projects()
    assert isinstance(projects, list)
    assert len(projects) == 0
