import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock bleach if it's not available to allow imports from email_persistence_service
if 'bleach' not in sys.modules:
    sys.modules['bleach'] = MagicMock()
    sys.modules['bleach.sanitizer'] = MagicMock()

from services.email_persistence_service import clean_html, ALLOWED_TAGS, ALLOWED_ATTRIBUTES

def test_clean_html_none():
    """Test that None input returns an empty string."""
    assert clean_html(None) == ""

def test_clean_html_empty_string():
    """Test that an empty string input returns an empty string."""
    assert clean_html("") == ""

def test_clean_html_delegates_to_bleach(monkeypatch):
    """
    Test that clean_html correctly delegates to bleach.clean
    with the expected arguments when BLEACH_AVAILABLE is True.
    """
    import services.email_persistence_service as eps

    # Ensure BLEACH_AVAILABLE is True for this test
    monkeypatch.setattr(eps, "BLEACH_AVAILABLE", True)

    # Create a mock for bleach.clean
    mock_clean = MagicMock(return_value="safe html")

    with patch("bleach.clean", mock_clean):
        html_input = "<p>unsafe <script>alert(1)</script></p>"
        result = eps.clean_html(html_input)

        assert result == "safe html"
        mock_clean.assert_called_once_with(
            html_input,
            tags=list(eps.ALLOWED_TAGS),
            attributes=eps.ALLOWED_ATTRIBUTES,
            strip=True
        )

def test_clean_html_returns_empty_when_bleach_unavailable(monkeypatch):
    """
    Test that clean_html returns an empty string
    when BLEACH_AVAILABLE is False for security.
    """
    import services.email_persistence_service as eps

    # Ensure BLEACH_AVAILABLE is False for this test
    monkeypatch.setattr(eps, "BLEACH_AVAILABLE", False)

    html_input = "<div>some html</div>"
    result = eps.clean_html(html_input)

    assert result == ""

def test_allowed_tags_constants():
    """Verify that ALLOWED_TAGS contains essential tags."""
    import services.email_persistence_service as eps
    # Since bleach might be mocked, we check the set defined in the module
    assert 'p' in eps.ALLOWED_TAGS
    assert 'br' in eps.ALLOWED_TAGS
    assert 'div' in eps.ALLOWED_TAGS
    assert 'a' in eps.ALLOWED_TAGS
    assert 'img' in eps.ALLOWED_TAGS

def test_allowed_attributes_constants():
    """Verify that ALLOWED_ATTRIBUTES contains essential attributes."""
    assert '*' in ALLOWED_ATTRIBUTES
    assert 'class' in ALLOWED_ATTRIBUTES['*']
    assert 'href' in ALLOWED_ATTRIBUTES['a']
    assert 'src' in ALLOWED_ATTRIBUTES['img']
