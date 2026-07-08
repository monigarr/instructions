#!/usr/bin/env python3
"""Generate 200/300-item batch manifests from scale fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.generate_scale_fixtures import main as generate_all

if __name__ == "__main__":
    generate_all()
