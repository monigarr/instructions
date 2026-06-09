"""Unit tests for TTB field verification rules."""

from src.domain.constants import GOVERNMENT_WARNING_CANONICAL
from src.domain.models import ApplicationRecord, ExtractedLabelRecord, VerdictStatus
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
        bottler_producer_address="Louisville, KY",
        country_of_origin="",
        raw_text="",
        extraction_confidence=0.9,
    )
    base.update(kwargs)
    return ExtractedLabelRecord(**base)


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


def test_brand_fuzzy_needs_review():
    rule = BrandFuzzyRule()
    v = rule.evaluate(_app(brand_name="Stone's Throw"), _extracted(brand_name="STONE'S THROW"))
    assert v.status == VerdictStatus.NEEDS_REVIEW


def test_abv_mismatch():
    rule = ABVPatternRule()
    v = rule.evaluate(_app(), _extracted(alcohol_content="40% Alc./Vol. (80 Proof)"))
    assert v.status == VerdictStatus.MISMATCH
