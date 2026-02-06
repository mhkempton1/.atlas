import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.communication_service import comm_service
from services.altimeter_service import altimeter_service

def verify_comm_logic():
    print("--- Decoupling V2 Verification ---")
    
    # 1. Check Factory
    print(f"Active Provider: {comm_service.active_provider_name}")
    print(f"Providers Available: {list(comm_service.providers.keys())}")
    
    # 2. Test Bridge Context
    print("\nTesting Bridge Context (Simulated RFP)...")
    context = altimeter_service.get_context_for_email(
        sender="bids@contractor.com",
        subject="Project 25-0001: RFP for electrical work",
        body="Please see attached RFP for the new data center."
    )
    
    project = context.get('project')
    project_number = project.get('number') if project else "None"
    print(f"Project Identified: {project_number}")
    print(f"Is Proposal: {context.get('is_proposal')}")
    print(f"Mission Intel Found: {len(context.get('mission_intel', []))}")
    
    if context.get('mission_intel'):
        print("Intel Sample:")
        for intel in context['mission_intel']:
            print(f"  - {intel['title']}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    try:
        verify_comm_logic()
    except Exception as e:
        import traceback
        print(f"Verification Failed:")
        traceback.print_exc()
