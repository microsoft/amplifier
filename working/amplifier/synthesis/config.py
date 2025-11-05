"""
Centralized configuration for the synthesis module.
"""

import os

# --- Path Definitions ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
CACHE_DIR = os.path.join(REPO_ROOT, ".tmp", "synthesizer_cache")

# --- Model Names ---
ANALYST_MODEL = "gpt-4o"
SYNTHESIST_MODEL = "gpt-4o"
TRIAGE_MODEL = "gpt-4o-mini"
