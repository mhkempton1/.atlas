import pytest
from unittest.mock import MagicMock
from services.contact_unification_service import match_email_to_contact, extract_domain_stem
from database.models import Contact

def test_extract_domain_stem():
    assert extract_domain_stem("bob@acmeinc.com") == "acmeinc"
    # Simple extraction leaves .co for .co.uk, which is acceptable for fuzzy match
    assert extract_domain_stem("bob@acmeinc.co.uk") == "acmeinc.co"
    assert extract_domain_stem("bob@google.com") == "google"
    assert extract_domain_stem("bob@localhost") == "localhost"
    assert extract_domain_stem(None) == ""
    assert extract_domain_stem("") == ""

def test_exact_match():
    db = MagicMock()
    contact = Contact(id=1, email_address="bob@example.com")

    # Mock exact match query
    # db.query(Contact).filter(...).first()
    db.query.return_value.filter.return_value.first.return_value = contact

    result = match_email_to_contact("bob@example.com", db)

    assert result is not None
    matched_contact, is_tentative = result
    assert matched_contact.id == 1
    assert is_tentative is False

def test_domain_match_confident():
    db = MagicMock()

    # Setup mocks
    query_mock = db.query.return_value
    filter_mock = query_mock.filter.return_value

    # We need to distinguish between the first call (exact match) and second call (all contacts)
    # Since they use the same mock chain structure, we can verify what was returned or use side_effect
    # But simpler: the code calls first() then all().
    # If first() returns None, it proceeds.
    filter_mock.first.return_value = None

    c1 = Contact(id=1, email_address="support@acmeinc.com", company="ACME Inc")
    c2 = Contact(id=2, email_address="other@other.com", company="Other Corp")
    filter_mock.all.return_value = [c1, c2]

    # "bob@acmeinc.com" -> stem "acmeinc"
    # c1 company "ACME Inc" -> "acme inc"
    # match > 0.8

    result = match_email_to_contact("bob@acmeinc.com", db)

    assert result is not None
    matched_contact, is_tentative = result
    assert matched_contact.id == 1
    assert is_tentative is False

def test_domain_match_tentative():
    db = MagicMock()
    query_mock = db.query.return_value
    filter_mock = query_mock.filter.return_value

    filter_mock.first.return_value = None

    # "micro" vs "microsoft" -> 0.71 (Tentative)
    c2 = Contact(id=2, email_address="bill@microsoft.com", company="Microsoft")
    filter_mock.all.return_value = [c2]

    result = match_email_to_contact("steve@micro.com", db)

    assert result is not None
    matched_contact, is_tentative = result
    assert matched_contact.id == 2
    assert is_tentative is True

def test_no_match():
    db = MagicMock()
    query_mock = db.query.return_value
    filter_mock = query_mock.filter.return_value

    filter_mock.first.return_value = None

    c1 = Contact(id=1, email_address="foo@bar.com", company="Bar Corp")
    filter_mock.all.return_value = [c1]

    # "bob@google.com" -> "google" vs "Bar Corp" -> low match

    result = match_email_to_contact("bob@google.com", db)

    assert result is None
