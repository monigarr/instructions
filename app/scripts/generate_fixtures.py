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


def _wrap_line(line: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, draw: ImageDraw.ImageDraw, max_width: int) -> list[str]:
    words = line.split()
    if not words:
        return [line]
    wrapped: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            wrapped.append(current)
            current = word
    wrapped.append(current)
    return wrapped


def draw_label(lines: list[str], path: Path, width: int = 800, height: int = 1200) -> None:
    img = Image.new("RGB", (width, height), color=(250, 245, 235))
    draw = ImageDraw.Draw(img)
    margin = 40
    max_text_width = width - (margin * 2)
    y = margin
    for i, line in enumerate(lines):
        size = 28 if i == 0 else 18
        if line.startswith("GOVERNMENT WARNING"):
            size = 16
        font = _font(size)
        for wrapped in _wrap_line(line, font, draw, max_text_width):
            draw.text((margin, y), wrapped, fill=(20, 20, 20), font=font)
            y += size + 10
        y += 4
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG")


WARNING_PARAPHRASED = (
    "GOVERNMENT WARNING: (1) Per the Surgeon General, women must not consume alcohol "
    "during pregnancy due to birth defect risk. (2) Drinking impairs driving and machine "
    "operation and may harm health."
)

WARNING_TRUNCATED = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink "
    "alcoholic beverages during pregnancy because of the risk of birth defects."
)


def _label_fixture(
    label_id: str,
    expected_summary: str,
    lines: list[str],
    app: dict,
    *,
    blank: bool = False,
) -> dict:
    return {"id": label_id, "expected_summary": expected_summary, "lines": lines, "app": app, "blank": blank}


def _domestic_lines(
    brand: str,
    class_type: str,
    abv: str = "45% Alc./Vol. (90 Proof)",
    net: str = "750 mL",
    address: str = "Old Tom Distillery, Louisville, KY 40202",
    *,
    include_address: bool = True,
    include_warning: bool = True,
) -> list[str]:
    lines = [brand, class_type, abv, net]
    if include_address:
        lines.extend(["Distilled and Bottled by", address])
    if include_warning:
        lines.append(GOVERNMENT_WARNING_CANONICAL)
    return lines


def fixture_catalog() -> list[dict]:
    return [
        {
            "id": "old_tom_match",
            "expected_summary": "passed",
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
            "expected_summary": "failed",
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
            "expected_summary": "failed",
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
            "expected_summary": "needs_review",
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
            "expected_summary": "passed",
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
            "expected_summary": "needs_review",
            "lines": [],
            "app": {**BASE_APP, "label_id": "unreadable_blank"},
            "blank": True,
        },
        {
            "id": "net_contents_mismatch",
            "expected_summary": "failed",
            "lines": [
                "OLD TOM DISTILLERY",
                "Kentucky Straight Bourbon Whiskey",
                "45% Alc./Vol. (90 Proof)",
                "700 mL",
                "Distilled and Bottled by",
                "Old Tom Distillery, Louisville, KY 40202",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            "app": {**BASE_APP, "label_id": "net_contents_mismatch"},
        },
        {
            "id": "class_type_mismatch",
            "expected_summary": "failed",
            "lines": [
                "OLD TOM DISTILLERY",
                "Straight Bourbon Whiskey",
                "45% Alc./Vol. (90 Proof)",
                "750 mL",
                "Distilled and Bottled by",
                "Old Tom Distillery, Louisville, KY 40202",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            "app": {**BASE_APP, "label_id": "class_type_mismatch"},
        },
        {
            "id": "brand_hard_mismatch",
            "expected_summary": "failed",
            "lines": [
                "WRONG BRAND",
                "Kentucky Straight Bourbon Whiskey",
                "45% Alc./Vol. (90 Proof)",
                "750 mL",
                "Distilled and Bottled by",
                "Old Tom Distillery, Louisville, KY 40202",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            "app": {**BASE_APP, "label_id": "brand_hard_mismatch"},
        },
        {
            "id": "import_country_mismatch",
            "expected_summary": "failed",
            "lines": [
                "CHATEAU NORD",
                "Cognac",
                "40% Alc./Vol. (80 Proof)",
                "750 mL",
                "Product of Mexico",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            "app": {
                "label_id": "import_country_mismatch",
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
            "id": "warning_wording_change",
            "expected_summary": "failed",
            "lines": [
                "OLD TOM DISTILLERY",
                "Kentucky Straight Bourbon Whiskey",
                "45% Alc./Vol. (90 Proof)",
                "750 mL",
                WARNING_PARAPHRASED,
            ],
            "app": {**BASE_APP, "label_id": "warning_wording_change"},
        },
        {
            "id": "warning_missing",
            "expected_summary": "needs_review",
            "lines": [
                "OLD TOM DISTILLERY",
                "Kentucky Straight Bourbon Whiskey",
                "45% Alc./Vol. (90 Proof)",
                "750 mL",
                "Distilled and Bottled by",
                "Old Tom Distillery, Louisville, KY 40202",
            ],
            "app": {**BASE_APP, "label_id": "warning_missing"},
        },
        {
            "id": "address_mismatch",
            "expected_summary": "failed",
            "lines": [
                "OLD TOM DISTILLERY",
                "Kentucky Straight Bourbon Whiskey",
                "45% Alc./Vol. (90 Proof)",
                "750 mL",
                "Distilled and Bottled by",
                "Old Tom Distillery, Nashville, TN 37201",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            "app": {**BASE_APP, "label_id": "address_mismatch"},
        },
        _label_fixture(
            "vodka_match",
            "passed",
            [
                "CRYSTAL VODKA",
                "Vodka",
                "40% Alc./Vol. (80 Proof)",
                "750 mL",
                "Distilled and Bottled by",
                "Crystal Spirits, Austin, TX 78701",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            {
                "label_id": "vodka_match",
                "brand_name": "CRYSTAL VODKA",
                "class_type": "Vodka",
                "alcohol_content": "40% Alc./Vol. (80 Proof)",
                "net_contents": "750 mL",
                "government_warning": GOVERNMENT_WARNING_CANONICAL,
                "bottler_producer_address": "Crystal Spirits, Austin, TX 78701",
                "country_of_origin": "",
            },
        ),
        _label_fixture(
            "gin_match",
            "passed",
            _domestic_lines("JUNIPER LANE", "Gin", "47% Alc./Vol. (94 Proof)", address="Juniper Lane Distillery, Portland, OR 97201"),
            {
                "label_id": "gin_match",
                "brand_name": "JUNIPER LANE",
                "class_type": "Gin",
                "alcohol_content": "47% Alc./Vol. (94 Proof)",
                "net_contents": "750 mL",
                "government_warning": GOVERNMENT_WARNING_CANONICAL,
                "bottler_producer_address": "Juniper Lane Distillery, Portland, OR 97201",
                "country_of_origin": "",
            },
        ),
        _label_fixture(
            "rum_match",
            "passed",
            _domestic_lines("ISLAND SPICE", "Rum", "35% Alc./Vol. (70 Proof)", address="Island Spice Co., Miami, FL 33101"),
            {
                "label_id": "rum_match",
                "brand_name": "ISLAND SPICE",
                "class_type": "Rum",
                "alcohol_content": "35% Alc./Vol. (70 Proof)",
                "net_contents": "750 mL",
                "government_warning": GOVERNMENT_WARNING_CANONICAL,
                "bottler_producer_address": "Island Spice Co., Miami, FL 33101",
                "country_of_origin": "",
            },
        ),
        _label_fixture(
            "tequila_match",
            "passed",
            _domestic_lines("AGAVE GOLD", "Tequila", "38% Alc./Vol. (76 Proof)", address="Agave Gold LLC, San Antonio, TX 78205"),
            {
                "label_id": "tequila_match",
                "brand_name": "AGAVE GOLD",
                "class_type": "Tequila",
                "alcohol_content": "38% Alc./Vol. (76 Proof)",
                "net_contents": "750 mL",
                "government_warning": GOVERNMENT_WARNING_CANONICAL,
                "bottler_producer_address": "Agave Gold LLC, San Antonio, TX 78205",
                "country_of_origin": "",
            },
        ),
        _label_fixture(
            "scotch_import_match",
            "passed",
            [
                "HIGHLAND MIST",
                "Blended Scotch Whisky",
                "43% Alc./Vol. (86 Proof)",
                "750 mL",
                "Product of Scotland",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            {
                "label_id": "scotch_import_match",
                "brand_name": "HIGHLAND MIST",
                "class_type": "Blended Scotch Whisky",
                "alcohol_content": "43% Alc./Vol. (86 Proof)",
                "net_contents": "750 mL",
                "government_warning": GOVERNMENT_WARNING_CANONICAL,
                "bottler_producer_address": "",
                "country_of_origin": "Scotland",
            },
        ),
        _label_fixture(
            "japan_import_match",
            "passed",
            [
                "SAKURA SPIRIT",
                "Whiskey",
                "43% Alc./Vol. (86 Proof)",
                "750 mL",
                "Product of Japan",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            {
                "label_id": "japan_import_match",
                "brand_name": "SAKURA SPIRIT",
                "class_type": "Whiskey",
                "alcohol_content": "43% Alc./Vol. (86 Proof)",
                "net_contents": "750 mL",
                "government_warning": GOVERNMENT_WARNING_CANONICAL,
                "bottler_producer_address": "",
                "country_of_origin": "Japan",
            },
        ),
        _label_fixture(
            "mexico_tequila_import",
            "passed",
            [
                "SIERRA AZUL",
                "Tequila",
                "40% Alc./Vol. (80 Proof)",
                "750 mL",
                "Product of Mexico",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            {
                "label_id": "mexico_tequila_import",
                "brand_name": "SIERRA AZUL",
                "class_type": "Tequila",
                "alcohol_content": "40% Alc./Vol. (80 Proof)",
                "net_contents": "750 mL",
                "government_warning": GOVERNMENT_WARNING_CANONICAL,
                "bottler_producer_address": "",
                "country_of_origin": "Mexico",
            },
        ),
        _label_fixture(
            "brand_casing_nuance",
            "needs_review",
            _domestic_lines("old tom distillery", "Kentucky Straight Bourbon Whiskey"),
            {**BASE_APP, "label_id": "brand_casing_nuance"},
        ),
        _label_fixture(
            "brand_apostrophe_nuance",
            "needs_review",
            _domestic_lines("TOM'S DISTILLERY", "Kentucky Straight Bourbon Whiskey"),
            {**BASE_APP, "label_id": "brand_apostrophe_nuance", "brand_name": "Tom's Distillery"},
        ),
        _label_fixture(
            "class_type_lowercase_match",
            "passed",
            _domestic_lines("OLD TOM DISTILLERY", "kentucky straight bourbon whiskey"),
            {**BASE_APP, "label_id": "class_type_lowercase_match"},
        ),
        _label_fixture(
            "abv_format_variant_match",
            "passed",
            _domestic_lines("OLD TOM DISTILLERY", "Kentucky Straight Bourbon Whiskey", "45% Alc/Vol (90 Proof)"),
            {**BASE_APP, "label_id": "abv_format_variant_match"},
        ),
        _label_fixture(
            "net_contents_floz_mismatch",
            "failed",
            _domestic_lines("OLD TOM DISTILLERY", "Kentucky Straight Bourbon Whiskey", net="25.4 fl oz"),
            {**BASE_APP, "label_id": "net_contents_floz_mismatch"},
        ),
        _label_fixture(
            "warning_truncated",
            "failed",
            _domestic_lines("OLD TOM DISTILLERY", "Kentucky Straight Bourbon Whiskey", include_warning=False)
            + [WARNING_TRUNCATED],
            {**BASE_APP, "label_id": "warning_truncated"},
        ),
        _label_fixture(
            "scotch_country_mismatch",
            "failed",
            [
                "HIGHLAND MIST",
                "Blended Scotch Whisky",
                "43% Alc./Vol. (86 Proof)",
                "750 mL",
                "Product of Ireland",
                GOVERNMENT_WARNING_CANONICAL,
            ],
            {
                "label_id": "scotch_country_mismatch",
                "brand_name": "HIGHLAND MIST",
                "class_type": "Blended Scotch Whisky",
                "alcohol_content": "43% Alc./Vol. (86 Proof)",
                "net_contents": "750 mL",
                "government_warning": GOVERNMENT_WARNING_CANONICAL,
                "bottler_producer_address": "",
                "country_of_origin": "Scotland",
            },
        ),
        _label_fixture(
            "domestic_no_address_match",
            "passed",
            _domestic_lines("OLD TOM DISTILLERY", "Kentucky Straight Bourbon Whiskey", include_address=False),
            {
                **BASE_APP,
                "label_id": "domestic_no_address_match",
                "bottler_producer_address": "",
            },
        ),
        _label_fixture(
            "proof_mismatch",
            "failed",
            _domestic_lines("OLD TOM DISTILLERY", "Kentucky Straight Bourbon Whiskey", "46% Alc./Vol. (92 Proof)"),
            {**BASE_APP, "label_id": "proof_mismatch"},
        ),
        _label_fixture(
            "brand_substring_nuance",
            "needs_review",
            _domestic_lines("OLD TOM", "Kentucky Straight Bourbon Whiskey"),
            {**BASE_APP, "label_id": "brand_substring_nuance"},
        ),
    ]


def main() -> None:
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    APPS_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = fixture_catalog()
    manifest = []
    for fx in fixtures:
        if fx.get("blank"):
            sidecar = LABELS_DIR / f"{fx['id']}.txt"
            if sidecar.exists():
                sidecar.unlink()
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
