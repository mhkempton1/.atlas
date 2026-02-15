from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc, cast, String, and_
from database.models import Email, Contact

def get_all_emails_with_contact(contact_id: int, db: Session, page: int = 1, per_page: int = 20):
    """
    Retrieve all emails associated with a contact, grouped by thread_id.
    - For emails with a thread_id, returns the latest email in the thread involving the contact.
    - For emails without a thread_id, returns them individually.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact or not contact.email_address:
        return []

    email_addr = contact.email_address.lower()
    search_term = f"%{email_addr}%"

    # Conditions to find emails involving the contact
    filter_conditions = or_(
        func.lower(Email.sender) == email_addr,
        func.lower(Email.from_address) == email_addr,
        cast(Email.recipients, String).ilike(search_term),
        cast(Email.to_addresses, String).ilike(search_term)
    )

    # 1. Threaded emails: Group by thread_id, get max date for each thread involving contact
    subquery = db.query(
        Email.thread_id,
        func.max(Email.date_received).label('max_date')
    ).filter(
        filter_conditions,
        Email.thread_id.isnot(None)
    ).group_by(Email.thread_id).subquery()

    query_threaded = db.query(Email).join(
        subquery,
        and_(
            Email.thread_id == subquery.c.thread_id,
            Email.date_received == subquery.c.max_date
        )
    ).filter(filter_conditions)

    # 2. Unthreaded emails: Return all directly
    query_unthreaded = db.query(Email).filter(
        filter_conditions,
        Email.thread_id.is_(None)
    )

    # 3. Union and sort by date descending
    final_query = query_threaded.union(query_unthreaded).order_by(desc(Email.date_received))

    # Pagination
    offset = (page - 1) * per_page
    results = final_query.limit(per_page).offset(offset).all()

    return results
