import pytest
from services.altimeter_service import AltimeterService

def test_rfp_detection():
    service = AltimeterService()
    
    # Test cases for RFP detection
    rfp_subjects = [
        "Request for Proposal - Project Alpha",
        "New RFP: Downtown Office Complex",
        "Invitation to Bid: Electrical Wring",
        "Pricing Request for Server Room"
    ]
    
    normal_subjects = [
        "Meeting notes",
        "Lunch tomorrow?",
        "Project update",
        "Invoice attached"
    ]
    
    for subject in rfp_subjects:
        result = service.parse_email_for_project(subject)
        assert result["is_proposal"] == True, f"Failed to detect RFP in: {subject}"
        
    for subject in normal_subjects:
        result = service.parse_email_for_project(subject)
        assert result["is_proposal"] == False, f"False positive RFP in: {subject}"

def test_daily_log_detection():
    service = AltimeterService()
    log_subjects = [
        "Daily Log - Site A",
        "Field Report: 123 Main St",
        "Superintendent Report for Monday"
    ]
    
    for subject in log_subjects:
        result = service.parse_email_for_project(subject)
        assert result["is_daily_log"] == True, f"Failed to detect Daily Log in: {subject}"

def test_context_includes_proposal_flag():
    service = AltimeterService()
    context = service.get_context_for_email("client@example.com", "RFP: New Warehouse")
    assert context["is_proposal"] == True
