import pytest
from services.altimeter_service import AltimeterService

def test_memorial_hall_rfp_detection():
    service = AltimeterService()
    
    # Content from User's Example
    subject = "FW: Addendum #2 - Memorial Hall Renovation - College of the Ozarks"
    body = """
    Please see attached addendum 2 for the above referenced project. 
    
    From: Cody Ritter
    Sent: Friday, January 16, 2026 12:27 PM
    To: Lindsay Ritter <lindsay@base-cm.com>
    Subject: Bid - Memorial Hall Renovation - College of the Ozarks
    
    To all:
    
    Please see below link for Memorial Hall Renovation - College of the Ozarks– Branson, MO.  Bids are due 2/4 at 12 pm. 
    
    There is a site walk thru on Wednesday, January 21st at 2:30 pm at the Memorial Hall building. 
    """
    
    result = service.parse_email_for_project(subject, body)
    
    # Must detect proposal based on "Bid", "Bids are due", "Addendum"
    assert result["is_proposal"] == True, "Failed to detect Memorial Hall RFP"

def test_daily_log_in_body():
    service = AltimeterService()
    subject = "Update from site"
    body = "Here is the daily log for today."
    
    result = service.parse_email_for_project(subject, body)
    assert result["is_daily_log"] == True

