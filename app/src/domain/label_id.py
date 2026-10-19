"""Shared label identifier validation for filesystem-safe paths."""

from __future__ import annotations

import re

_LABEL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")


def is_valid_label_id(label_id: str) -> bool:
    return bool(_LABEL_ID_PATTERN.match(label_id))


def sanitize_label_id(label_id: str) -> str | None:
    """Return label_id when safe for fixture path joins; otherwise None."""
    if not is_valid_label_id(label_id):
        return None
    return label_id
