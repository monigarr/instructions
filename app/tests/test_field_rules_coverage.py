"""Branch coverage for deterministic field rules and normalization helpers.

These tests pin the compliance semantics that matter in review: missing values
never fail silently, unit/format equivalences are accepted deliberately, and the
government warning has no tolerance for casing or wording drift.
"""

from __future__ import annotations

import pytest

from src.domain.constants import GOVERNMENT_WARNING_CANONICAL
from src.domain.models import ApplicationRecord, ExtractedLabelRecord, VerdictStatus
from src.rules.engine import DeterministicRulesEngine, default_field_rules
from src.rules.field_rules import (
    ABVPatternRule,
    AddressContainsRule,
    BrandFuzzyRule,
    ClassTypeRule,
    CountryExactRule,
    NetContentsRule,
    WarningExactRule,
)
from src.rules.normalize import (
    extract_abv_numbers,
    normalize_brand,
    normalize_text,
    normalize_units,
)


def _app(**overrides) -> ApplicationRecord:
    values = {
        "label_id": "test",
        "brand_name": "OLD TOM DISTILLERY",
        "class_type": "Kentucky Straight Bourbon Whiskey",
        "alcohol_content": "45% Alc./Vol. (90 Proof)",
        "net_contents": "750 mL",
        "government_warning": GOVERNMENT_WARNING_CANONICAL,
        "bottler_producer_address": "Louisville, KY",
        "country_of_origin": "United States",
    }
    values.update(overrides)
    return ApplicationRecord(**values)


def _extracted(**overrides) -> ExtractedLabelRecord:
    values = {
        "brand_name": "OLD TOM DISTILLERY",
        "class_type": "Kentucky Straight Bourbon Whiskey",
        "alcohol_content": "45% Alc./Vol. (90 Proof)",
        "net_contents": "750 mL",
        "government_warning": GOVERNMENT_WARNING_CANONICAL,
        "government_warning_header_bold": True,
        "government_warning_bold_confidence": 0.9,
        "bottler_producer_address": "Louisville, KY",
        "country_of_origin": "United States",
        "extraction_confidence": 0.95,
    }
    values.update(overrides)
    return ExtractedLabelRecord(**values)


# --------------------------------------------------------------------------- #
# Normalization
# --------------------------------------------------------------------------- #


def test_normalize_text_handles_empty_and_unicode():
    assert normalize_text(None) == ""
    assert normalize_text("  ") == ""
    assert normalize_text("Café  RÉSUMÉ") == "cafe resume"
    assert normalize_text("A--B") == "a--b"
    assert normalize_text("100% Alc./Vol. (90 Proof)") == "100% alc./vol. (90 proof)"


def test_normalize_brand_collapses_apostrophes():
    assert normalize_brand(None) == ""
    assert normalize_brand("Stone’s Throw") == normalize_brand("Stone's Throw")


def test_normalize_units_is_space_and_case_insensitive():
    assert normalize_units(None) == ""
    assert normalize_units("750ml") == normalize_units("750 mL") == "750 ml"
    assert normalize_units("12 FL OZ") == normalize_units("12 fl oz") == "12 fl oz"
    assert normalize_units("1.5 L") == "1.5 l"


def test_extract_abv_numbers_variants():
    assert extract_abv_numbers(None) == (None, None)
    assert extract_abv_numbers("45% Alc./Vol. (90 Proof)") == (45.0, 90.0)
    assert extract_abv_numbers("90 Proof") == (None, 90.0)
    assert extract_abv_numbers("12.5%") == (12.5, None)
    assert extract_abv_numbers("no numbers here") == (None, None)


# --------------------------------------------------------------------------- #
# Brand
# --------------------------------------------------------------------------- #


def test_brand_missing_values_are_unable_to_verify():
    rule = BrandFuzzyRule()
    both_missing = rule.evaluate(_app(brand_name=None), _extracted(brand_name=None))
    assert both_missing.status == VerdictStatus.UNABLE_TO_VERIFY
    assert "not provided" in both_missing.reason.lower()

    app_missing = rule.evaluate(_app(brand_name=None), _extracted())
    assert app_missing.status == VerdictStatus.UNABLE_TO_VERIFY
    assert "application value missing" in app_missing.reason.lower()

    label_missing = rule.evaluate(_app(), _extracted(brand_name=None))
    assert label_missing.status == VerdictStatus.UNABLE_TO_VERIFY
    assert "could not extract" in label_missing.reason.lower()


def test_brand_low_confidence_is_carried_on_unable_to_verify():
    verdict = BrandFuzzyRule().evaluate(
        _app(), _extracted(brand_name=None, extraction_confidence=0.2)
    )
    assert verdict.status == VerdictStatus.UNABLE_TO_VERIFY
    assert verdict.confidence == pytest.approx(0.2)


def test_brand_exact_match():
    verdict = BrandFuzzyRule().evaluate(_app(), _extracted())
    assert verdict.status == VerdictStatus.MATCH
    assert verdict.reason == "Brand names match."


def test_brand_casing_or_punctuation_difference_needs_review():
    verdict = BrandFuzzyRule().evaluate(
        _app(brand_name="Stone's Throw"), _extracted(brand_name="STONE'S THROW")
    )
    assert verdict.status == VerdictStatus.NEEDS_REVIEW
    assert "casing/punctuation" in verdict.reason.lower()


def test_brand_spacing_only_difference_needs_review():
    verdict = BrandFuzzyRule().evaluate(
        _app(brand_name="Old Tom"), _extracted(brand_name="OldTom")
    )
    assert verdict.status == VerdictStatus.NEEDS_REVIEW
    assert "spacing/punctuation" in verdict.reason.lower()


def test_brand_containment_needs_review():
    verdict = BrandFuzzyRule().evaluate(
        _app(brand_name="Old Tom Distillery"),
        _extracted(brand_name="Old Tom Distillery Co."),
    )
    assert verdict.status == VerdictStatus.NEEDS_REVIEW
    assert "similar" in verdict.reason.lower()


def test_brand_mismatch():
    verdict = BrandFuzzyRule().evaluate(_app(), _extracted(brand_name="NEW TOM DISTILLERY"))
    assert verdict.status == VerdictStatus.MISMATCH


# --------------------------------------------------------------------------- #
# Class / type
# --------------------------------------------------------------------------- #


def test_class_type_missing_and_normalized_match_and_mismatch():
    rule = ClassTypeRule()
    assert rule.evaluate(_app(class_type=None), _extracted(class_type=None)).status == VerdictStatus.UNABLE_TO_VERIFY
    assert rule.evaluate(_app(), _extracted(class_type=None)).status == VerdictStatus.UNABLE_TO_VERIFY
    assert rule.evaluate(_app(class_type=None), _extracted()).status == VerdictStatus.UNABLE_TO_VERIFY
    assert (
        rule.evaluate(
            _app(class_type="Kentucky Straight Bourbon Whiskey"),
            _extracted(class_type="kentucky straight bourbon whiskey"),
        ).status
        == VerdictStatus.MATCH
    )
    assert (
        rule.evaluate(_app(), _extracted(class_type="Straight Rye Whiskey")).status
        == VerdictStatus.MISMATCH
    )


# --------------------------------------------------------------------------- #
# Alcohol content
# --------------------------------------------------------------------------- #


def test_abv_missing_values():
    rule = ABVPatternRule()
    assert rule.evaluate(_app(alcohol_content=None), _extracted(alcohol_content=None)).status == VerdictStatus.UNABLE_TO_VERIFY
    assert rule.evaluate(_app(), _extracted(alcohol_content=None)).status == VerdictStatus.UNABLE_TO_VERIFY
    assert rule.evaluate(_app(alcohol_content=None), _extracted()).status == VerdictStatus.UNABLE_TO_VERIFY


def test_abv_percentage_equivalence_accepted():
    verdict = ABVPatternRule().evaluate(
        _app(alcohol_content="45% Alc./Vol."), _extracted(alcohol_content="45 % alc/vol")
    )
    assert verdict.status == VerdictStatus.MATCH
    assert "alcohol content matches" in verdict.reason.lower()


def test_abv_proof_equivalence_accepted():
    verdict = ABVPatternRule().evaluate(
        _app(alcohol_content="90 Proof"), _extracted(alcohol_content="(90 proof)")
    )
    assert verdict.status == VerdictStatus.MATCH
    assert "proof matches" in verdict.reason.lower()


def test_abv_text_equivalence_accepted():
    verdict = ABVPatternRule().evaluate(
        _app(alcohol_content="Forty-five percent"), _extracted(alcohol_content="forty-five PERCENT")
    )
    assert verdict.status == VerdictStatus.MATCH
    assert "text matches" in verdict.reason.lower()


def test_abv_mismatch_when_neither_measure_nor_text_match():
    verdict = ABVPatternRule().evaluate(
        _app(alcohol_content="45% Alc./Vol. (90 Proof)"),
        _extracted(alcohol_content="40% Alc./Vol. (80 Proof)"),
    )
    assert verdict.status == VerdictStatus.MISMATCH


# --------------------------------------------------------------------------- #
# Net contents
# --------------------------------------------------------------------------- #


def test_net_contents_missing_match_and_mismatch():
    rule = NetContentsRule()
    assert rule.evaluate(_app(net_contents=None), _extracted(net_contents=None)).status == VerdictStatus.UNABLE_TO_VERIFY
    assert rule.evaluate(_app(), _extracted(net_contents=None)).status == VerdictStatus.UNABLE_TO_VERIFY
    assert rule.evaluate(_app(net_contents=None), _extracted()).status == VerdictStatus.UNABLE_TO_VERIFY
    assert rule.evaluate(_app(net_contents="750ml"), _extracted(net_contents="750 mL")).status == VerdictStatus.MATCH
    assert rule.evaluate(_app(), _extracted(net_contents="1 L")).status == VerdictStatus.MISMATCH


# --------------------------------------------------------------------------- #
# Government warning
# --------------------------------------------------------------------------- #


def test_warning_missing_is_unable_to_verify_with_confidence():
    verdict = WarningExactRule().evaluate(
        _app(), _extracted(government_warning=None, extraction_confidence=0.3)
    )
    assert verdict.status == VerdictStatus.UNABLE_TO_VERIFY
    assert "not detected" in verdict.reason.lower()
    assert verdict.confidence == pytest.approx(0.3)


def test_warning_lowercase_header_rejected_as_all_caps_requirement():
    lower = GOVERNMENT_WARNING_CANONICAL.replace("GOVERNMENT WARNING:", "government warning:")
    verdict = WarningExactRule().evaluate(_app(), _extracted(government_warning=lower))
    assert verdict.status == VerdictStatus.MISMATCH
    assert "all caps" in verdict.reason.lower()


def test_warning_header_must_start_with_uppercase_label():
    prefix = "Contains: " + GOVERNMENT_WARNING_CANONICAL
    verdict = WarningExactRule().evaluate(_app(), _extracted(government_warning=prefix))
    assert verdict.status == VerdictStatus.MISMATCH
    assert "must start" in verdict.reason.lower()


def test_warning_text_must_match_word_for_word():
    altered = GOVERNMENT_WARNING_CANONICAL.replace("impair", "affect")
    verdict = WarningExactRule().evaluate(_app(), _extracted(government_warning=altered))
    assert verdict.status == VerdictStatus.MISMATCH
    assert "word-for-word" in verdict.reason.lower()


def test_warning_absent_app_value_falls_back_to_canonical():
    verdict = WarningExactRule().evaluate(_app(government_warning=None), _extracted())
    assert verdict.status == VerdictStatus.MATCH
    assert verdict.application_value == GOVERNMENT_WARNING_CANONICAL


def test_warning_bold_confidence_threshold():
    low = WarningExactRule().evaluate(
        _app(),
        _extracted(
            government_warning_header_bold=True,
            government_warning_bold_confidence=0.49,
        ),
    )
    assert low.status == VerdictStatus.NEEDS_REVIEW
    assert low.confidence == pytest.approx(0.6)

    high = WarningExactRule().evaluate(
        _app(),
        _extracted(
            government_warning_header_bold=True,
            government_warning_bold_confidence=0.5,
        ),
    )
    assert high.status == VerdictStatus.MATCH


# --------------------------------------------------------------------------- #
# Address and country
# --------------------------------------------------------------------------- #


def test_address_optional_match_containment_and_mismatch():
    rule = AddressContainsRule()
    both_missing = rule.evaluate(
        _app(bottler_producer_address=None),
        _extracted(bottler_producer_address=None),
    )
    assert both_missing.status == VerdictStatus.MATCH
    assert "not required" in both_missing.reason.lower()

    assert rule.evaluate(_app(), _extracted(bottler_producer_address=None)).status == VerdictStatus.UNABLE_TO_VERIFY
    assert rule.evaluate(_app(bottler_producer_address=None), _extracted()).status == VerdictStatus.UNABLE_TO_VERIFY

    contained = rule.evaluate(
        _app(bottler_producer_address="Louisville, KY"),
        _extracted(bottler_producer_address="Bottled in Louisville, KY by Old Tom"),
    )
    assert contained.status == VerdictStatus.MATCH

    assert rule.evaluate(_app(), _extracted(bottler_producer_address="Frankfort, KY")).status == VerdictStatus.MISMATCH


def test_country_optional_match_normalized_and_mismatch():
    rule = CountryExactRule()
    both_missing = rule.evaluate(
        _app(country_of_origin=None), _extracted(country_of_origin=None)
    )
    assert both_missing.status == VerdictStatus.MATCH
    assert "not applicable" in both_missing.reason.lower()

    assert rule.evaluate(_app(), _extracted(country_of_origin=None)).status == VerdictStatus.UNABLE_TO_VERIFY
    assert rule.evaluate(_app(country_of_origin=None), _extracted()).status == VerdictStatus.UNABLE_TO_VERIFY

    normalized = rule.evaluate(
        _app(country_of_origin="United States"),
        _extracted(country_of_origin="united states"),
    )
    assert normalized.status == VerdictStatus.MATCH

    assert rule.evaluate(_app(), _extracted(country_of_origin="Scotland")).status == VerdictStatus.MISMATCH


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #


def test_default_engine_covers_all_ttb_fields():
    verdicts = DeterministicRulesEngine().evaluate_all(_app(), _extracted())
    assert [v.field for v in verdicts] == [
        "brand_name",
        "class_type",
        "alcohol_content",
        "net_contents",
        "government_warning",
        "bottler_producer_address",
        "country_of_origin",
    ]
    assert all(v.status == VerdictStatus.MATCH for v in verdicts)


def test_engine_downgrades_matches_below_confidence_floor():
    verdicts = DeterministicRulesEngine().evaluate_all(
        _app(), _extracted(extraction_confidence=0.3)
    )
    assert all(v.status == VerdictStatus.UNABLE_TO_VERIFY for v in verdicts)
    assert all("Low OCR confidence" in v.reason for v in verdicts)


def test_engine_accepts_injected_rule_list():
    class AlwaysMismatch:
        @property
        def field_name(self) -> str:
            return "custom"

        def evaluate(self, application, extracted):
            return WarningExactRule().evaluate(
                _app(government_warning="x"), _extracted(government_warning="GOVERNMENT WARNING: x")
            )

    verdicts = DeterministicRulesEngine(rules=[AlwaysMismatch()]).evaluate_all(_app(), _extracted())
    assert len(verdicts) == 1
    assert verdicts[0].status == VerdictStatus.MISMATCH


def test_default_field_rules_are_stable_instances():
    rules = default_field_rules()
    assert len(rules) == 7
    assert {rule.field_name for rule in rules} == {
        "brand_name",
        "class_type",
        "alcohol_content",
        "net_contents",
        "government_warning",
        "bottler_producer_address",
        "country_of_origin",
    }
