#!/usr/bin/env python3
"""Generate 300 unique scale-test label fixtures and batch manifests."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.domain.constants import GOVERNMENT_WARNING_CANONICAL
from scripts.generate_fixtures import (
    BASE_APP,
    WARNING_TRUNCATED,
    _domestic_lines,
    _label_fixture,
    draw_label,
    draw_label_bold_header,
    draw_label_glare,
    draw_label_low_contrast,
    draw_label_rotated,
)

LABELS_DIR = ROOT / "fixtures" / "labels"
APPS_DIR = ROOT / "fixtures" / "applications"

SCALE_COUNT = 300

BRANDS = [
    "OLD TOM DISTILLERY",
    "STONE'S THROW",
    "HIGHLAND MIST",
    "CHATEAU NORD",
    "PACIFIC VODKA CO",
    "COPPER STILL WORKS",
    "BLUE RIDGE SPIRITS",
    "GOLDEN GRAIN DISTILLERY",
    "SILVER CREEK BRAND",
    "IRON HORSE WHISKEY",
    "MAPLE GROVE DISTILLERY",
    "RIDGE LINE BOURBON",
    "HARBOR LIGHT RUM",
    "DESERT SUN TEQUILA",
    "NORTHERN STAR GIN",
    "VALLEY VIEW VODKA",
    "COASTAL BREEZE RUM",
    "MOUNTAIN PEAK SCOTCH",
    "RIVER RUN WHISKEY",
    "SUNSET DISTILLING",
    "EMBER OAK BOURBON",
    "FROST LINE VODKA",
    "CANYON CREST TEQUILA",
    "MEADOW LARK GIN",
    "THUNDER BAY RUM",
]

CLASS_TYPES = [
    "Kentucky Straight Bourbon Whiskey",
    "Straight Bourbon Whiskey",
    "Vodka",
    "London Dry Gin",
    "Aged Rum",
    "Blanco Tequila",
    "Blended Scotch Whisky",
    "Cognac",
    "Irish Whiskey",
    "Tennessee Whiskey",
    "Rye Whiskey",
    "White Rum",
]

ADDRESSES = [
    "Old Tom Distillery, Louisville, KY 40202",
    "Copper Still Works, Nashville, TN 37201",
    "Blue Ridge Spirits, Asheville, NC 28801",
    "Golden Grain Distillery, Denver, CO 80202",
    "Pacific Vodka Co, Portland, OR 97201",
]

IMPORT_COUNTRIES = ["France", "Scotland", "Japan", "Mexico", "Ireland"]

ABV_OPTIONS = [
    ("40% Alc./Vol. (80 Proof)", "40% Alc./Vol. (80 Proof)"),
    ("43% Alc./Vol. (86 Proof)", "43% Alc./Vol. (86 Proof)"),
    ("45% Alc./Vol. (90 Proof)", "45% Alc./Vol. (90 Proof)"),
    ("46% Alc./Vol. (92 Proof)", "46% Alc./Vol. (92 Proof)"),
    ("50% Alc./Vol. (100 Proof)", "50% Alc./Vol. (100 Proof)"),
]

NET_OPTIONS = ["750 mL", "700 mL", "1 L", "375 mL", "25.4 fl oz"]


def _brand_app_name(brand: str) -> str:
    if brand == "STONE'S THROW":
        return "Stone's Throw"
    return brand.title() if brand.isupper() else brand


def _outcome_for_index(i: int) -> str:
    """Weighted outcome assignment for reproducible distribution."""
    weights = [
        ("pass", 45),
        ("abv_mismatch", 10),
        ("net_contents_mismatch", 10),
        ("class_type_mismatch", 8),
        ("proof_mismatch", 5),
        ("warning_title_case", 5),
        ("warning_truncated", 4),
        ("brand_nuance", 8),
        ("import_pass", 6),
        ("import_country_mismatch", 4),
        ("visual_stress", 3),
        ("blank", 2),
    ]
    total = sum(w for _, w in weights)
    slot = i % total
    cumulative = 0
    for name, weight in weights:
        cumulative += weight
        if slot < cumulative:
            return name
    return "pass"


def scale_fixture_catalog(count: int = SCALE_COUNT) -> list[dict]:
    random.seed(42)
    fixtures: list[dict] = []
    for i in range(count):
        label_id = f"scale_{i + 1:03d}"
        brand = BRANDS[i % len(BRANDS)]
        class_type = CLASS_TYPES[(i // len(BRANDS)) % len(CLASS_TYPES)]
        abv_label, abv_app = ABV_OPTIONS[i % len(ABV_OPTIONS)]
        net_label = NET_OPTIONS[i % len(NET_OPTIONS)]
        net_app = net_label
        address = ADDRESSES[i % len(ADDRESSES)]
        outcome = _outcome_for_index(i)

        if outcome == "blank":
            fixtures.append(
                _label_fixture(
                    label_id,
                    "needs_review",
                    [],
                    {**BASE_APP, "label_id": label_id, "brand_name": brand},
                    blank=True,
                )
            )
            continue

        if outcome == "visual_stress":
            render = ["rotated", "low_contrast", "glare"][i % 3]
            lines = _domestic_lines(brand, class_type, abv_label, net_label, address)
            fixtures.append(
                _label_fixture(
                    label_id,
                    "passed",
                    lines,
                    {
                        **BASE_APP,
                        "label_id": label_id,
                        "brand_name": brand,
                        "class_type": class_type,
                        "alcohol_content": abv_label,
                        "net_contents": net_label,
                        "bottler_producer_address": address,
                    },
                    render=render,
                )
            )
            continue

        if outcome == "import_pass":
            country = IMPORT_COUNTRIES[i % len(IMPORT_COUNTRIES)]
            lines = [
                brand,
                class_type,
                abv_label,
                net_label,
                f"Product of {country}",
                GOVERNMENT_WARNING_CANONICAL,
            ]
            fixtures.append(
                _label_fixture(
                    label_id,
                    "passed",
                    lines,
                    {
                        "label_id": label_id,
                        "brand_name": brand,
                        "class_type": class_type,
                        "alcohol_content": abv_label,
                        "net_contents": net_label,
                        "government_warning": GOVERNMENT_WARNING_CANONICAL,
                        "bottler_producer_address": "",
                        "country_of_origin": country,
                    },
                )
            )
            continue

        if outcome == "import_country_mismatch":
            country_label = IMPORT_COUNTRIES[i % len(IMPORT_COUNTRIES)]
            country_app = IMPORT_COUNTRIES[(i + 1) % len(IMPORT_COUNTRIES)]
            lines = [
                brand,
                class_type,
                abv_label,
                net_label,
                f"Product of {country_label}",
                GOVERNMENT_WARNING_CANONICAL,
            ]
            fixtures.append(
                _label_fixture(
                    label_id,
                    "failed",
                    lines,
                    {
                        "label_id": label_id,
                        "brand_name": brand,
                        "class_type": class_type,
                        "alcohol_content": abv_label,
                        "net_contents": net_label,
                        "government_warning": GOVERNMENT_WARNING_CANONICAL,
                        "bottler_producer_address": "",
                        "country_of_origin": country_app,
                    },
                )
            )
            continue

        if outcome == "abv_mismatch":
            wrong_abv = ABV_OPTIONS[(i + 2) % len(ABV_OPTIONS)][0]
            lines = _domestic_lines(brand, class_type, wrong_abv, net_label, address)
            fixtures.append(
                _label_fixture(
                    label_id,
                    "failed",
                    lines,
                    {
                        **BASE_APP,
                        "label_id": label_id,
                        "brand_name": brand,
                        "class_type": class_type,
                        "alcohol_content": abv_label,
                        "net_contents": net_label,
                        "bottler_producer_address": address,
                    },
                )
            )
            continue

        if outcome == "net_contents_mismatch":
            wrong_net = NET_OPTIONS[(i + 1) % len(NET_OPTIONS)]
            lines = _domestic_lines(brand, class_type, abv_label, wrong_net, address)
            fixtures.append(
                _label_fixture(
                    label_id,
                    "failed",
                    lines,
                    {
                        **BASE_APP,
                        "label_id": label_id,
                        "brand_name": brand,
                        "class_type": class_type,
                        "alcohol_content": abv_label,
                        "net_contents": net_label,
                        "bottler_producer_address": address,
                    },
                )
            )
            continue

        if outcome == "class_type_mismatch":
            wrong_class = CLASS_TYPES[(i + 3) % len(CLASS_TYPES)]
            lines = _domestic_lines(brand, wrong_class, abv_label, net_label, address)
            fixtures.append(
                _label_fixture(
                    label_id,
                    "failed",
                    lines,
                    {
                        **BASE_APP,
                        "label_id": label_id,
                        "brand_name": brand,
                        "class_type": class_type,
                        "alcohol_content": abv_label,
                        "net_contents": net_label,
                        "bottler_producer_address": address,
                    },
                )
            )
            continue

        if outcome == "proof_mismatch":
            lines = _domestic_lines(brand, class_type, "46% Alc./Vol. (92 Proof)", net_label, address)
            fixtures.append(
                _label_fixture(
                    label_id,
                    "failed",
                    lines,
                    {
                        **BASE_APP,
                        "label_id": label_id,
                        "brand_name": brand,
                        "class_type": class_type,
                        "alcohol_content": abv_label,
                        "net_contents": net_label,
                        "bottler_producer_address": address,
                    },
                )
            )
            continue

        if outcome == "warning_title_case":
            lines = _domestic_lines(brand, class_type, abv_label, net_label, address, include_warning=False)
            lines.append(
                "Government Warning: (1) According to the Surgeon General, women should not drink "
                "alcoholic beverages during pregnancy because of the risk of birth defects. "
                "(2) Consumption of alcoholic beverages impairs your ability to drive a car or "
                "operate machinery, and may cause health problems."
            )
            fixtures.append(
                _label_fixture(
                    label_id,
                    "failed",
                    lines,
                    {
                        **BASE_APP,
                        "label_id": label_id,
                        "brand_name": brand,
                        "class_type": class_type,
                        "alcohol_content": abv_label,
                        "net_contents": net_label,
                        "bottler_producer_address": address,
                    },
                )
            )
            continue

        if outcome == "warning_truncated":
            lines = _domestic_lines(brand, class_type, abv_label, net_label, address, include_warning=False)
            lines.append(WARNING_TRUNCATED)
            fixtures.append(
                _label_fixture(
                    label_id,
                    "failed",
                    lines,
                    {
                        **BASE_APP,
                        "label_id": label_id,
                        "brand_name": brand,
                        "class_type": class_type,
                        "alcohol_content": abv_label,
                        "net_contents": net_label,
                        "bottler_producer_address": address,
                    },
                )
            )
            continue

        if outcome == "brand_nuance":
            label_brand = brand.upper() if i % 2 == 0 else brand.title()
            app_brand = _brand_app_name(brand)
            lines = _domestic_lines(label_brand, class_type, abv_label, net_label, address)
            fixtures.append(
                _label_fixture(
                    label_id,
                    "needs_review",
                    lines,
                    {
                        **BASE_APP,
                        "label_id": label_id,
                        "brand_name": app_brand,
                        "class_type": class_type,
                        "alcohol_content": abv_label,
                        "net_contents": net_label,
                        "bottler_producer_address": address,
                    },
                )
            )
            continue

        # pass (default)
        lines = _domestic_lines(brand, class_type, abv_label, net_label, address)
        fixtures.append(
            _label_fixture(
                label_id,
                "passed",
                lines,
                {
                    **BASE_APP,
                    "label_id": label_id,
                    "brand_name": brand,
                    "class_type": class_type,
                    "alcohol_content": abv_label,
                    "net_contents": net_label,
                    "bottler_producer_address": address,
                },
            )
        )

    return fixtures


def _write_fixture(fx: dict) -> None:
    label_path = LABELS_DIR / f"{fx['id']}.png"
    if fx.get("blank"):
        sidecar = LABELS_DIR / f"{fx['id']}.txt"
        if sidecar.exists():
            sidecar.unlink()
        Image.new("RGB", (100, 100), (128, 128, 128)).save(label_path)
    else:
        render = fx.get("render", "default")
        header_bold = fx.get("header_bold", True)
        lines = fx["lines"]
        if render == "rotated":
            draw_label_rotated(lines, label_path)
        elif render == "low_contrast":
            draw_label_low_contrast(lines, label_path)
        elif render == "glare":
            draw_label_glare(lines, label_path)
        elif header_bold is False:
            draw_label_bold_header(lines, label_path, header_bold=False)
        else:
            draw_label(lines, label_path)
        sidecar = LABELS_DIR / f"{fx['id']}.txt"
        sidecar.write_text("\n".join(lines), encoding="utf-8")
    app_path = APPS_DIR / f"{fx['id']}.json"
    app_path.write_text(json.dumps(fx["app"], indent=2), encoding="utf-8")


def generate_scale_manifest(size: int, fixtures: list[dict]) -> list[dict]:
    if size > len(fixtures):
        raise ValueError(f"Requested {size} entries but only {len(fixtures)} scale fixtures exist.")
    return [dict(fx["app"]) for fx in fixtures[:size]]


def main() -> None:
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    APPS_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = scale_fixture_catalog(SCALE_COUNT)
    for fx in fixtures:
        _write_fixture(fx)

    summary: dict[str, int] = {"passed": 0, "failed": 0, "needs_review": 0}
    for fx in fixtures:
        summary[fx["expected_summary"]] = summary.get(fx["expected_summary"], 0) + 1

    for size in (200, 300):
        manifest = generate_scale_manifest(size, fixtures)
        out = APPS_DIR / f"batch_manifest_{size}.json"
        out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Wrote {len(manifest)} entries to {out}")

    summary_path = APPS_DIR / "scale_manifest_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "total_fixtures": len(fixtures),
                "expected_summary": summary,
                "manifest_sizes": {"200": 200, "300": 300},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Generated {len(fixtures)} scale labels in {LABELS_DIR}")
    print(f"Expected summary: {summary}")


if __name__ == "__main__":
    main()
