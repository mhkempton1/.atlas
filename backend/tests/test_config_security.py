import unittest
import os
from unittest.mock import patch, MagicMock

# We need to mock os.getenv and file reading BEFORE importing config
# because config runs logic on import (settings = Settings())
# However, modifying sys.modules or using reload is tricky.
# Instead, we can verify the behavior of the Settings class if we instantiate it.

class TestConfigSecurity(unittest.TestCase):

    def test_secure_fallback_generation(self):
        """
        Test that if JWT_SECRET_KEY is missing or insecure,
        load_secrets generates a secure random one.
        """
        # We need to import inside test or reload module,
        # but since Settings is a class, we can just instantiate it if we patch env.

        # Patching os.environ to ensure no env var interferes
        with patch.dict(os.environ, {"JWT_SECRET_KEY": ""}):
            from core.config import Settings

            # Create instance
            settings = Settings()
            # Force JWT_SECRET_KEY to empty (as base settings might pick up defaults)
            settings.JWT_SECRET_KEY = ""

            # Mock os.path.exists to return False so it doesn't read real secrets.json
            with patch("os.path.exists", return_value=False):
                settings.load_secrets()

                # Check that it is NOT empty
                self.assertTrue(settings.JWT_SECRET_KEY)
                # Check length (32 bytes urlsafe is approx 43 chars)
                self.assertGreaterEqual(len(settings.JWT_SECRET_KEY), 32)
                # Check it is not the insecure default
                self.assertNotEqual(settings.JWT_SECRET_KEY, "insecure-fallback-development-only")

    def test_insecure_default_replacement(self):
        """
        Test that if JWT_SECRET_KEY is the insecure default, it gets replaced.
        """
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "insecure-fallback-development-only"}):
            from core.config import Settings
            settings = Settings()
            # Even if env var set it, load_secrets should replace it because it's in the forbidden list

            # We must ensure load_secrets doesn't overwrite with file values for this test
            with patch("os.path.exists", return_value=False):
                settings.load_secrets()

                self.assertNotEqual(settings.JWT_SECRET_KEY, "insecure-fallback-development-only")
                self.assertGreaterEqual(len(settings.JWT_SECRET_KEY), 32)

if __name__ == '__main__':
    unittest.main()
