from sqlalchemy.orm import Session
from database.models import Contact
from services.altimeter_service import altimeter_service

def import_customers_from_altimeter(db: Session):
    """Import customers from Altimeter DB into Atlas contacts."""
    customers = altimeter_service.get_customers()
    stats = {"imported": 0, "updated": 0, "errors": 0}

    # Bulk fetch existing contacts to avoid N+1 queries
    emails = [c.get("email") for c in customers if c.get("email")]

    existing_contacts = []
    if emails:
        existing_contacts = db.query(Contact).filter(Contact.email_address.in_(emails)).all()

    existing_map = {c.email_address: c for c in existing_contacts}

    for cust in customers:
        try:
            email = cust.get("email")
            if not email:
                stats["errors"] += 1
                continue

            contact = existing_map.get(email)

            # Handle missing keys gracefully
            company = cust.get("company_name") or cust.get("company")
            phone = cust.get("phone")
            title = cust.get("title")
            name = cust.get("contact_name") or cust.get("name") or company
            customer_id = cust.get("customer_id") or cust.get("id")

            if contact:
                # Update existing
                if company:
                    contact.company = company
                if phone:
                    contact.phone = phone
                if title:
                    contact.title = title
                if customer_id:
                    contact.altimeter_customer_id = customer_id

                if not contact.relationship_type:
                    contact.relationship_type = "customer"

                stats["updated"] += 1
            else:
                # Create new
                new_contact = Contact(
                    email_address=email,
                    name=name,
                    company=company,
                    phone=phone,
                    title=title,
                    altimeter_customer_id=customer_id,
                    relationship_type="customer"
                )
                db.add(new_contact)
                existing_map[email] = new_contact
                stats["imported"] += 1
        except Exception as e:
            print(f"Error importing customer {cust}: {e}")
            stats["errors"] += 1

    db.commit()
    return stats

def import_vendors_from_altimeter(db: Session):
    """Import vendors from Altimeter DB into Atlas contacts."""
    vendors = altimeter_service.get_vendors()
    stats = {"imported": 0, "updated": 0, "errors": 0}

    emails = [v.get("email") for v in vendors if v.get("email")]

    existing_contacts = []
    if emails:
        existing_contacts = db.query(Contact).filter(Contact.email_address.in_(emails)).all()

    existing_map = {c.email_address: c for c in existing_contacts}

    for vend in vendors:
        try:
            email = vend.get("email")
            if not email:
                stats["errors"] += 1
                continue

            contact = existing_map.get(email)

            # Handle missing keys gracefully
            company = vend.get("company_name") or vend.get("company")
            phone = vend.get("phone")
            title = vend.get("title")
            name = vend.get("contact_name") or vend.get("name") or company
            vendor_id = vend.get("vendor_id") or vend.get("id")

            if contact:
                if company:
                    contact.company = company
                if phone:
                    contact.phone = phone
                if title:
                    contact.title = title
                if vendor_id:
                    contact.altimeter_vendor_id = vendor_id

                if not contact.relationship_type:
                    contact.relationship_type = "vendor"

                stats["updated"] += 1
            else:
                new_contact = Contact(
                    email_address=email,
                    name=name,
                    company=company,
                    phone=phone,
                    title=title,
                    altimeter_vendor_id=vendor_id,
                    relationship_type="vendor"
                )
                db.add(new_contact)
                existing_map[email] = new_contact
                stats["imported"] += 1
        except Exception as e:
            print(f"Error importing vendor {vend}: {e}")
            stats["errors"] += 1

    db.commit()
    return stats
