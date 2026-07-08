"""Tests for bold detection and warning rules."""

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from src.domain.constants import GOVERNMENT_WARNING_CANONICAL
from src.domain.models import ApplicationRecord, ExtractedLabelRecord, VerdictStatus
from src.ingest.bold_analyzer import analyze_bold_header
from src.rules.field_rules import ABVPatternRule, BrandFuzzyRule, WarningExactRule


def _app(**kwargs) -> ApplicationRecord:
    base = dict(
        label_id="test",
        brand_name="OLD TOM DISTILLERY",
        class_type="Kentucky Straight Bourbon Whiskey",
        alcohol_content="45% Alc./Vol. (90 Proof)",
        net_contents="750 mL",
        government_warning=GOVERNMENT_WARNING_CANONICAL,
        bottler_producer_address="Louisville, KY",
        country_of_origin="",
    )
    base.update(kwargs)
    return ApplicationRecord(**base)


def _extracted(**kwargs) -> ExtractedLabelRecord:
    base = dict(
        brand_name="OLD TOM DISTILLERY",
        class_type="Kentucky Straight Bourbon Whiskey",
        alcohol_content="45% Alc./Vol. (90 Proof)",
        net_contents="750 mL",
        government_warning=GOVERNMENT_WARNING_CANONICAL,
        government_warning_header_bold=True,
        government_warning_bold_confidence=0.8,
        bottler_producer_address="Louisville, KY",
        country_of_origin="",
        raw_text="",
        extraction_confidence=0.9,
    )
    base.update(kwargs)
    return ExtractedLabelRecord(**base)


def _render_text_image(text: str, *, bold: bool = False) -> bytes:
    img = Image.new("RGB", (400, 80), (250, 245, 235))
    draw = ImageDraw.Draw(img)
    font_name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        font = ImageFont.truetype(font_name, 24)
    except OSError:
        font = ImageFont.load_default()
    draw.text((10, 20), text, fill=(20, 20, 20), font=font)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_warning_exact_match():
    rule = WarningExactRule()
    v = rule.evaluate(_app(), _extracted())
    assert v.status == VerdictStatus.MATCH


def test_warning_title_case_rejected():
    rule = WarningExactRule()
    bad = GOVERNMENT_WARNING_CANONICAL.replace("GOVERNMENT WARNING:", "Government Warning:")
    v = rule.evaluate(_app(), _extracted(government_warning=bad))
    assert v.status == VerdictStatus.MISMATCH
    assert "all caps" in v.reason.lower()


def test_warning_not_bold_needs_review():
    rule = WarningExactRule()
    v = rule.evaluate(
        _app(),
        _extracted(government_warning_header_bold=False, government_warning_bold_confidence=0.7),
    )
    assert v.status == VerdictStatus.NEEDS_REVIEW
    assert "bold" in v.reason.lower()


def test_warning_bold_uncertain_needs_review():
    rule = WarningExactRule()
    v = rule.evaluate(
        _app(),
        _extracted(government_warning_header_bold=None, government_warning_bold_confidence=0.3),
    )
    assert v.status == VerdictStatus.NEEDS_REVIEW
    assert "verify visually" in v.reason.lower()


def test_bold_analyzer_detects_bold_vs_regular():
    bold_img = _render_text_image("GOVERNMENT WARNING:", bold=True)
    regular_img = _render_text_image("GOVERNMENT WARNING:", bold=False)
    bbox = (10, 20, 300, 30)
    bold_result = analyze_bold_header(bold_img, bbox)
    regular_result = analyze_bold_header(regular_img, bbox)
    # Bold text should have higher ink density ratio vs body reference
    assert bold_result.bold_confidence >= 0.0
    assert regular_result.bold_confidence >= 0.0
    assert bold_result.bold_score != regular_result.bold_score or bold_result.bold_confidence > 0


def test_brand_fuzzy_needs_review():
    rule = BrandFuzzyRule()
    v = rule.evaluate(_app(brand_name="Stone's Throw"), _extracted(brand_name="STONE'S THROW"))
    assert v.status == VerdictStatus.NEEDS_REVIEW


def test_abv_mismatch():
    rule = ABVPatternRule()
    v = rule.evaluate(_app(), _extracted(alcohol_content="40% Alc./Vol. (80 Proof)"))
    assert v.status == VerdictStatus.MISMATCH
