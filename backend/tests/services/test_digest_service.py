import pytest
from datetime import datetime, timedelta, timezone, time
from services.digest_service import digest_service
from database.models import Task

def test_generate_daily_digest(db):
    now = datetime.now(timezone.utc)
    today = now.date()

    # Create test tasks

    # 1. Due Today (should be in due_today and due_this_week)
    task_due_today = Task(
        title="Due Today",
        status="open",
        priority="high",
        due_date=now,
        created_at=now
    )
    db.add(task_due_today)

    # 2. Due Tomorrow (should be in due_this_week only)
    task_due_tomorrow = Task(
        title="Due Tomorrow",
        status="open",
        priority="medium",
        due_date=now + timedelta(days=1),
        created_at=now
    )
    db.add(task_due_tomorrow)

    # 3. Due Next Week (should be in neither - assuming > 7 days)
    # The service logic is today to today+6 days.
    # So if we add 8 days, it should be outside.
    task_due_next_week = Task(
        title="Due Next Week",
        status="open",
        priority="low",
        due_date=now + timedelta(days=8),
        created_at=now
    )
    db.add(task_due_next_week)

    # 4. Overdue (should be in overdue)
    task_overdue = Task(
        title="Overdue",
        status="open",
        priority="high",
        due_date=now - timedelta(days=2),
        created_at=now - timedelta(days=5)
    )
    db.add(task_overdue)

    # 5. Completed Yesterday (should be in completed_yesterday)
    yesterday = now - timedelta(days=1)
    task_completed_yesterday = Task(
        title="Completed Yesterday",
        status="completed",
        priority="low",
        due_date=yesterday,
        completed_at=yesterday,
        created_at=now - timedelta(days=5)
    )
    db.add(task_completed_yesterday)

    # 6. Completed Today (should not be in completed_yesterday)
    task_completed_today = Task(
        title="Completed Today",
        status="completed",
        priority="low",
        due_date=now,
        completed_at=now,
        created_at=now
    )
    db.add(task_completed_today)

    db.commit()

    # Generate digest
    digest = digest_service.generate_daily_digest(db)

    # Verify Due Today
    assert len(digest["due_today"]) == 1
    assert digest["due_today"][0]["title"] == "Due Today"

    # Verify Due This Week (Today + Tomorrow)
    # logic: today to today+6 days (inclusive).
    # Today is included. Tomorrow is included.
    assert len(digest["due_this_week"]) == 2
    titles = [t["title"] for t in digest["due_this_week"]]
    assert "Due Today" in titles
    assert "Due Tomorrow" in titles

    # Verify Overdue
    assert len(digest["overdue"]) == 1
    assert digest["overdue"][0]["title"] == "Overdue"

    # Verify Completed Yesterday
    assert len(digest["completed_yesterday"]) == 1
    assert digest["completed_yesterday"][0]["title"] == "Completed Yesterday"
