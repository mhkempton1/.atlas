import unittest
import os
from unittest.mock import patch

class TestDebugMode(unittest.TestCase):
    def test_debug_disabled_by_default(self):
        """
        Verify that DEBUG is False by default when no environment variable is set.
        """
        # Patching os.environ to ensure DEBUG is not set
        with patch.dict(os.environ, {}, clear=True):
            # We import Settings inside the test to avoid using a previously
            # initialized singleton if possible, although BaseSettings
            # can be re-instantiated.
            from core.config import Settings

            # Create a new instance of Settings
            settings = Settings()

            # It should be False by default for security
            self.assertFalse(settings.DEBUG, "DEBUG mode should be False by default for security.")

    def test_debug_can_be_enabled_via_env(self):
        """
        Verify that DEBUG can still be enabled via environment variable if needed.
        """
        with patch.dict(os.environ, {"DEBUG": "True"}):
            from core.config import Settings
            settings = Settings()
            self.assertTrue(settings.DEBUG, "DEBUG mode should be overridable via environment variable.")

if __name__ == '__main__':
    unittest.main()
