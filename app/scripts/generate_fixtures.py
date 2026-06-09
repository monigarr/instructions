#!/usr/bin/env python3
"""Generate synthetic TTB label images and application JSON fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.domain.constants import GOVERNMENT_WARNING_CANONICAL

ROOT = Path(__file__).resolve().parent.parent
LABELS_DIR = ROOT / "fixtures" / "labels"
APPS_DIR = ROOT / "fixtures" / "applications"

BASE_APP = {
    "brand_name": "OLD TOM DISTILLERY",
    "class_type": "Kentucky Straight Bourbon Whiskey",
    "alcohol_content": "45% Alc./Vol. (90 Proof)",
    "net_contents": "750 mL",
    "government_warning": GOVERNMENT_WARNING_CANONICAL,
    "bottler_producer_address": "Old Tom Distillery, Louisville, KY 40202",
    "country_of_origin": "",
}


def _font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def draw_label(lines: list[str], path: Path, width: int = 800, height: int = 1000) -> None:
    img = Image.new("RGB", (width, height), color=(250, 245, 235))
    draw = ImageDraw.Draw(img)
    y = 40
    for i, line in enumerate(lines):
        size = 28 if i == 0 else 18
        if line.startswith("GOVERNMENT WARNING"):
            size = 16
        font = _font(size)
        draw.text((40, y), line, fill=(20, 20, 20), font=font)
        y += size + 14
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")


def main() -> None:
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    APPS_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = [
        {
            "id": "old_tom_match",
            "lines": [
                "OLD TOM DISTILLERY",
                "Kentucky Straight Bourbon Whiskey",
                "45% Alc./Vol. (90 Proof)",
                "750 mL",
                "Distilled and Bottled by",
                "Old Tom Distillery, Louisville, KY 40202",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            "app": {**BASE_APP, "label_id": "old_tom_match"},
        },
        {
            "id": "old_tom_abv_mismatch",
            "lines": [
                "OLD TOM DISTILLERY",
                "Kentucky Straight Bourbon Whiskey",
                "40% Alc./Vol. (80 Proof)",
                "750 mL",
                "Distilled and Bottled by",
                "Old Tom Distillery, Louisville, KY 40202",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            "app": {**BASE_APP, "label_id": "old_tom_abv_mismatch"},
        },
        {
            "id": "warning_title_case",
            "lines": [
                "OLD TOM DISTILLERY",
                "Kentucky Straight Bourbon Whiskey",
                "45% Alc./Vol. (90 Proof)",
                "750 mL",
                "Government Warning: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
            ],
            "app": {**BASE_APP, "label_id": "warning_title_case"},
        },
        {
            "id": "stones_throw_brand",
            "lines": [
                "STONE'S THROW",
                "Kentucky Straight Bourbon Whiskey",
                "45% Alc./Vol. (90 Proof)",
                "750 mL",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            "app": {
                **BASE_APP,
                "label_id": "stones_throw_brand",
                "brand_name": "Stone's Throw",
            },
        },
        {
            "id": "import_france",
            "lines": [
                "CHATEAU NORD",
                "Cognac",
                "40% Alc./Vol. (80 Proof)",
                "750 mL",
                "Product of France",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            "app": {
                "label_id": "import_france",
                "brand_name": "CHATEAU NORD",
                "class_type": "Cognac",
                "alcohol_content": "40% Alc./Vol. (80 Proof)",
                "net_contents": "750 mL",
                "government_warning": GOVERNMENT_WARNING_CANONICAL,
                "bottler_producer_address": "",
                "country_of_origin": "France",
            },
        },
        {
            "id": "unreadable_blank",
            "lines": [],
            "app": {**BASE_APP, "label_id": "unreadable_blank"},
            "blank": True,
        },
    ]

    manifest = []
    for fx in fixtures:
        label_path = LABELS_DIR / f"{fx['id']}.png"
        if fx.get("blank"):
            Image.new("RGB", (100, 100), (128, 128, 128)).save(label_path)
        else:
            draw_label(fx["lines"], label_path)
            sidecar = LABELS_DIR / f"{fx['id']}.txt"
            sidecar.write_text("\n".join(fx["lines"]), encoding="utf-8")
        app_path = APPS_DIR / f"{fx['id']}.json"
        app_path.write_text(json.dumps(fx["app"], indent=2), encoding="utf-8")
        manifest.append(fx["app"])

    (APPS_DIR / "batch_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(fixtures)} labels in {LABELS_DIR}")


if __name__ == "__main__":
    main()
