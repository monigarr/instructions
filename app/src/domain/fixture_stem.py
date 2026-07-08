"""Map batch label_id values to fixture file stems."""

from __future__ import annotations

import re

_SCALE_SUFFIX = re.compile(r"^(.+)_(\d{3})$")


def resolve_fixture_stem(label_id: str) -> str:
    """Strip a trailing _NNN scale suffix when present; otherwise return label_id."""
    if label_id.startswith("scale_"):
        return label_id
    match = _SCALE_SUFFIX.match(label_id)
    return match.group(1) if match else label_id
