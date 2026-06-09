"""Text normalization helpers for field rules."""

from __future__ import annotations

import re
import unicodedata


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s%\.'\-/()]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def normalize_brand(value: str | None) -> str:
    return normalize_text(value).replace("'", "'")


def normalize_units(value: str | None) -> str:
    if not value:
        return ""
    text = normalize_text(value)
    text = text.replace("ml", " ml").replace("fl oz", " fl oz")
    text = re.sub(r"(\d+)\s*ml", r"\1 ml", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_abv_numbers(value: str | None) -> tuple[float | None, float | None]:
    if not value:
        return None, None
    pct_m = re.search(r"(\d{1,2}(?:\.\d+)?)\s*%", value)
    proof_m = re.search(r"\(?\s*(\d{1,3})\s*proof\s*\)?", value, re.IGNORECASE)
    pct = float(pct_m.group(1)) if pct_m else None
    proof = float(proof_m.group(1)) if proof_m else None
    return pct, proof
