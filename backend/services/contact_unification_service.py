from sqlalchemy.orm import Session
from database.models import Contact
import difflib

def extract_domain_stem(email):
    """
    Extracts the domain stem from an email address.
    Example: "bob@acmeinc.com" -> "acmeinc"
    """
    if not email:
        return ""
    try:
        domain = email.split('@')[1]
        # Simple TLD stripping: take everything before the last dot
        if '.' in domain:
            return domain.rsplit('.', 1)[0]
        return domain
    except IndexError:
        return ""

def match_email_to_contact(email_address: str, db: Session):
    """
    Matches an email address to a contact.

    1. Exact match: query contacts by email_address -> return (contact, False)
    2. Domain match: extract domain from email, fuzzy-match against company names
       - Threshold: >0.8 similarity = confident match (contact, False)
       - Threshold: >0.6 similarity = tentative match (contact, True)
    3. No match: return None

    Returns:
        tuple: (Contact, is_tentative) or None
    """
    if not email_address:
        return None

    email_address = email_address.lower()

    # 1. Exact Match
    contact = db.query(Contact).filter(Contact.email_address == email_address).first()
    if contact:
        return (contact, False)

    # 2. Domain Match
    domain_stem = extract_domain_stem(email_address)
    if not domain_stem:
        return None

    # Iterate contacts with company
    # Note: iterating all contacts might be slow for large datasets,
    # but for now we assume manageable size or future optimization (e.g. vector search)
    contacts_with_company = db.query(Contact).filter(Contact.company.isnot(None)).all()

    best_match = None
    best_ratio = 0.0

    domain_stem_lower = domain_stem.lower()

    for c in contacts_with_company:
        if not c.company:
            continue

        company_lower = c.company.lower()

        # Calculate similarity
        ratio = difflib.SequenceMatcher(None, domain_stem_lower, company_lower).ratio()

        if ratio > best_ratio:
            best_ratio = ratio
            best_match = c

    if best_match:
        if best_ratio > 0.8:
            return (best_match, False) # Confident
        elif best_ratio > 0.6:
            return (best_match, True) # Tentative

    return None
