import asyncio
import sys
import os
import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.data_api import data_api
from services.altimeter_service import altimeter_service
from agents.task_agent import task_agent
from agents.calendar_agent import calendar_agent
from database.database import Base, engine

async def process_task(task):
    print(f"Processing task {task['id']}...")
    payload = task['payload']

    email_id = payload.get('email_id')
    subject = payload.get('subject')
    sender = payload.get('from_address')
    body = payload.get('body_text')
    remote_id = payload.get('remote_id')
    provider_type = payload.get('provider_type', 'google')

    # 1. Get Context (Now enriched with mission_intel/SOPs)
    context = altimeter_service.get_context_for_email(sender, subject, body)

    agent_context = {
        "subject": subject,
        "sender": sender,
        "body": body or "",
        "remote_id": remote_id,
        "provider_type": provider_type
    }

    if context.get("is_proposal"):
        agent_context["instructions"] = "This appears to be a Request for Proposal (RFP). Create a high priority task to review and bid."

    # 2. Run Task Agent
    task_out = await task_agent.process(agent_context)
    if task_out.get("status") == "success":
        for t_data in task_out["data"].get("tasks", []):
            if context.get("is_proposal"):
                t_data["title"] = f"PROPOSAL: {t_data['title']}"
                t_data["priority"] = "high"

            # Enrich with Mission Intel (SOPs, active phases)
            intel_notes = ""
            if context.get("mission_intel"):
                intel_notes = "\n\n### 💎 Mission Intel (SOPs/Context):\n"
                for intel in context["mission_intel"]:
                    intel_notes += f"- **{intel['title']}**: {intel['snippet']}\n"

            new_task_data = {
                "title": t_data["title"],
                "description": t_data["description"] + intel_notes,
                "priority": t_data["priority"].lower(),
                "due_date": datetime.datetime.fromisoformat(t_data["due_date"]) if t_data.get("due_date") else None,
                "project_id": context.get("project", {}).get("number") if context.get("project") else None,
                "email_id": email_id,
                "created_from": provider_type
            }

            # Write via Data API
            t_id = data_api.create_project_task(new_task_data)
            print(f"  -> Created Task {t_id}")

    # 3. Run Calendar Agent
    event_out = await calendar_agent.process(agent_context)
    if event_out.get("status") == "success" and event_out["data"].get("is_event"):
        e_data = event_out["data"]["event"]
        new_event_data = {
            "title": e_data["title"],
            "description": e_data["description"],
            "location": e_data.get("location"),
            "start_time": datetime.datetime.fromisoformat(e_data["start_time"]) if e_data.get("start_time") else None,
            "end_time": datetime.datetime.fromisoformat(e_data["end_time"]) if e_data.get("end_time") else None,
            "status": "confirmed",
            "project_id": context.get("project", {}).get("number") if context.get("project") else None,
            "email_id": email_id
        }

        # Write via Data API
        e_id = data_api.create_calendar_event(new_event_data)
        print(f"  -> Created Event {e_id}")

    data_api.complete_task(task['id'])
    print(f"Task {task['id']} completed.")

async def worker_loop():
    print("Worker started. Waiting for tasks...")
    while True:
        # Claim task
        task = data_api.claim_next_task("analyze_email", "worker_1")
        if task:
            try:
                await process_task(task)
            except Exception as e:
                print(f"Error processing task {task['id']}: {e}")
                data_api.fail_task(task['id'], str(e))
        else:
            # Sleep briefly to avoid busy loop
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        # Ensure database tables exist
        Base.metadata.create_all(bind=engine)

        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        print("Worker stopped.")
