import pytest
from app.core.models import AltimeterProject, ExternalKeys

def test_altimeter_project_validation():
    data = {
        "id": "123",
        "name": "Test Project",
        "status": "active",
        "keys": {
            "quickbooks_project_id": "QB123"
        }
    }
    project = AltimeterProject(**data)
    assert project.id == "123"
    assert project.is_valid_for_atlas() is True

def test_altimeter_project_invalid_keys():
    data = {
        "id": "456",
        "name": "Invalid Project",
        "status": "active",
        "keys": {
            "exaktime_project_id": "EX123"
        }
    }
    project = AltimeterProject(**data)
    assert project.is_valid_for_atlas() is False

def test_altimeter_project_missing_keys():
    with pytest.raises(ValueError):
        AltimeterProject(id="1", name="N", status="S") # Missing 'keys'
