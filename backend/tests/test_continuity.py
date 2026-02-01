import pytest
from backend.app.services.altimeter_connector import AltimeterConnector
from backend.app.core.models import AltimeterProject

def test_continuity_contract():
    """
    Verify Atlas can parse the EXACT payload Altimeter generates.
    This ensures 'Way 1' (Atlas Reading Altimeter) is safe.
    """
    
    # 1. The Payload (Copy-Pasted from Altimeter's Output in Phase 2)
    altimeter_payload = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Integration Job",
        "status": "Pending",
        "keys": {
            "quickbooks_customer_id": "QB-123",
            "quickbooks_project_id": "QB-PROJ-999",
            "exaktime_project_id": "XT-555"
        },
        "scope": [],
        "contract_value": 50000.0,
        "start_date": "2026-01-01",
        "completion_date": "2026-02-01"
    }
    
    # 2. Atlas Parsing
    project = AltimeterProject(**altimeter_payload)
    
    # 3. Validation
    assert project.name == "Integration Job"
    assert project.keys.quickbooks_project_id == "QB-PROJ-999"
    assert project.is_valid_for_atlas() is True

def test_reverse_continuity_stub():
    """
    Verify Connector has slots for Altimeter -> Atlas updates
    ('Way 2' Continuity)
    """
    connector = AltimeterConnector()
    success = connector.parse_webhook_update({"event": "project_created"})
    assert success is True
