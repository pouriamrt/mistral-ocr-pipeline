"""Pytest configuration and shared fixtures for the IE_Mistral test suite."""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so that `utils` and `info_extraction`
# packages are importable without an editable install.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
