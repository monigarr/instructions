"""
===============================================================================
FILE: streamlit_app.py
AUTHOR: MoniGarr (Monica Peters)
CREATED: 2026-10-19
UPDATED: 2026-10-19
CLASSIFICATION: Internal

PURPOSE:
Streamlit Community Cloud root entrypoint. Community Cloud's deploy form
defaults to streamlit_app.py at the repository root; the implementation lives in
app/streamlit_app.py so it can import the shared verification engine.

DEPENDENCIES:
  - app/streamlit_app.py — actual Streamlit implementation
  - runpy / pathlib — Python standard library only

SECURITY:
  - Executes only the repository's own implementation; no user-controlled path.
  - All upload validation and logging controls live in the implementation.

PERFORMANCE:
  - Negligible overhead: one local file read per Streamlit rerun.

OPERATIONAL:
  - Community Cloud: main file path streamlit_app.py (root)
  - Local: streamlit run streamlit_app.py or app/streamlit_app.py
  - The app sets __file__ to app/streamlit_app.py, so fixture paths resolve
    identically for both entrypoints.
===============================================================================
"""

from __future__ import annotations

import runpy
from pathlib import Path

IMPLEMENTATION = Path(__file__).resolve().parent / "app" / "streamlit_app.py"

runpy.run_path(str(IMPLEMENTATION), run_name="__main__")
