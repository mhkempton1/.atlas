import sys
import os
import asyncio
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.database.database import SessionLocal
from backend.database.models import Email, Task
from backend.agents.task_agent import task_agent
from backend.services.activity_service import activity_service
from backend.services.altimeter_service import altimeter_service

async def process_email_tasks(email, db):
    """
    Use AI TaskAgent to extract real tasks and save them.
    """
    # Get project context via Altimeter
    context = altimeter_service.get_context_for_email(email.from_address, email.subject, email.body_text)
    
    agent_context = {
        "subject": email.subject,
        "sender": email.from_address,
        "body": email.body_text or "",
        "message_id": email.message_id
    }

    print(f"  Analyzing: {email.subject[:50]}...")
    result = await task_agent.process(agent_context)
    
    if result.get("status") != "success":
        print(f"  [ERROR] AI analysis failed: {result.get('error')}")
        return 0

    tasks_data = result["data"].get("tasks", [])
    count = 0
    
    for t_data in tasks_data:
        # Avoid duplicate titles for the same email
        existing = db.query(Task).filter(Task.email_id == email.email_id, Task.title == t_data["title"]).first()
        if existing:
            continue

        task = Task(
            title=t_data["title"],
            description=t_data["description"],
            priority=t_data["priority"].lower(),
            status="todo",
            due_date=datetime.fromisoformat(t_data["due_date"]) if t_data.get("due_date") else None,
            original_due_date=datetime.fromisoformat(t_data["due_date"]) if t_data.get("due_date") else None,
            project_id=context.get("project", {}).get("number") if context.get("project") else None,
            email_id=email.email_id,
            created_from="email",
            created_at=datetime.now()
        )
        db.add(task)
        count += 1
        print(f"    [SAVED] {task.priority.upper()}: {task.title}")

    return count

async def main():
    print("--- Atlas Autonomous Email Scanner ---")
    print(f"Time: {datetime.now()}")
    
    db = SessionLocal()
    try:
        # Fetch last 10 emails that haven't been processed into tasks yet
        # (Simple check: emails where no task exists with that email_id)
        subquery = db.query(Task.email_id).filter(Task.email_id.isnot(None))
        emails = db.query(Email).filter(Email.email_id.not_in(subquery)).order_by(Email.date_received.desc()).limit(5).all()
        
        if not emails:
            print("No new emails requiring task extraction.")
            return

        print(f"Found {len(emails)} new emails to analyze.")
        
        total_tasks = 0
        for email in emails:
            tasks_created = await process_email_tasks(email, db)
            total_tasks += tasks_created
        
        if total_tasks > 0:
            db.commit()
            activity_service.log_activity(
                type="task",
                action="Autonomous Extraction",
                target=f"{total_tasks} new tasks",
                details=f"Scanned {len(emails)} emails; identified {total_tasks} project action items."
            )
            print(f"\nScan Complete. Created {total_tasks} tasks in database.")
        else:
            print("\nScan Complete. No new tasks identified.")

    except Exception as e:
        print(f"Fatal error during scan: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())

