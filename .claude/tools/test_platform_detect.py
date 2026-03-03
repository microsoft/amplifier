"""
Tests for platform_detect.py — env var priority detection.

Run with: python .claude/tools/test_platform_detect.py
"""

import os
import sys
import unittest


def reload_detect(env_overrides: dict) -> object:
    """Reload platform_detect with the given env vars patched."""
    saved = {}
    for k, v in env_overrides.items():
        saved[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

    if "platform_detect" in sys.modules:
        del sys.modules["platform_detect"]

    tools_dir = os.path.dirname(os.path.abspath(__file__))
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)

    import platform_detect as mod

    for k, orig in saved.items():
        if orig is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = orig

    return mod


class TestPlatformDetect(unittest.TestCase):

    def test_claudecode_env_takes_priority(self):
        """CLAUDECODE=1 wins even if OPENCODE=1 is also set."""
        mod = reload_detect({"CLAUDECODE": "1", "OPENCODE": "1"})
        self.assertTrue(mod.IS_CLAUDE_CODE, "CLAUDECODE=1 should set IS_CLAUDE_CODE=True")
        self.assertFalse(mod.IS_OPENCODE, "CLAUDECODE=1 should set IS_OPENCODE=False")

    def test_opencode_env_activates_opencode(self):
        """OPENCODE=1 (with no CLAUDECODE) should set IS_OPENCODE=True."""
        mod = reload_detect({"CLAUDECODE": None, "OPENCODE": "1"})
        self.assertFalse(mod.IS_CLAUDE_CODE, "OPENCODE=1 alone should not set IS_CLAUDE_CODE")
        self.assertTrue(mod.IS_OPENCODE, "OPENCODE=1 should set IS_OPENCODE=True")

    def test_no_env_vars_falls_back_to_directory(self):
        """Without env vars, falls back to directory-based detection."""
        mod = reload_detect({"CLAUDECODE": None, "OPENCODE": None})
        self.assertIsInstance(mod.IS_CLAUDE_CODE, bool)
        self.assertIsInstance(mod.IS_OPENCODE, bool)

    def test_opencode_env_sets_correct_root(self):
        """OPENCODE=1 should set AMPLIFIER_ROOT to C:/Przemek (Windows) or /opt (Linux)."""
        mod = reload_detect({"CLAUDECODE": None, "OPENCODE": "1"})
        if sys.platform.startswith("linux"):
            # On Linux, IS_LINUX takes precedence over OPENCODE for root path
            self.assertEqual(mod.AMPLIFIER_ROOT, "/opt")
        else:
            self.assertEqual(mod.AMPLIFIER_ROOT, "C:/Przemek")

    def test_claudecode_env_sets_correct_root(self):
        """CLAUDECODE=1 should set AMPLIFIER_ROOT to C:/claude."""
        mod = reload_detect({"CLAUDECODE": "1", "OPENCODE": None})
        if sys.platform.startswith("linux"):
            self.assertEqual(mod.AMPLIFIER_ROOT, "/opt")
        else:
            self.assertEqual(mod.AMPLIFIER_ROOT, "C:/claude")

    def test_linux_detection_without_env_vars(self):
        """On Linux without env vars, should detect via directory presence."""
        mod = reload_detect({"CLAUDECODE": None, "OPENCODE": None})
        if sys.platform.startswith("linux"):
            self.assertTrue(mod.IS_LINUX, "Should detect Linux platform")
            self.assertEqual(mod.AMPLIFIER_ROOT, "/opt")
            self.assertFalse(mod.IS_OPENCODE, "Linux should not be OpenCode")

    def test_linux_sets_empty_superpowers_fallback(self):
        """On Linux, SUPERPOWERS_FALLBACK should be empty."""
        mod = reload_detect({"CLAUDECODE": None, "OPENCODE": None})
        if sys.platform.startswith("linux"):
            self.assertEqual(mod.SUPERPOWERS_FALLBACK, "")

    def test_claudecode_on_linux_sets_linux_flag(self):
        """CLAUDECODE=1 on Linux should still set IS_LINUX=True."""
        mod = reload_detect({"CLAUDECODE": "1", "OPENCODE": None})
        if sys.platform.startswith("linux"):
            self.assertTrue(mod.IS_LINUX, "CLAUDECODE on Linux should set IS_LINUX=True")
            self.assertTrue(mod.IS_CLAUDE_CODE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
