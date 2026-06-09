"""Deterministic rules engine composing IFieldRule implementations."""

from __future__ import annotations

from src.domain.interfaces import IFieldRule, IRulesEngine
from src.domain.models import ApplicationRecord, ExtractedLabelRecord, FieldVerdict, VerdictStatus
from src.rules.field_rules import (
    ABVPatternRule,
    AddressContainsRule,
    BrandFuzzyRule,
    ClassTypeRule,
    CountryExactRule,
    NetContentsRule,
    WarningExactRule,
)


def default_field_rules() -> list[IFieldRule]:
    return [
        BrandFuzzyRule(),
        ClassTypeRule(),
        ABVPatternRule(),
        NetContentsRule(),
        WarningExactRule(),
        AddressContainsRule(),
        CountryExactRule(),
    ]


class DeterministicRulesEngine(IRulesEngine):
    def __init__(self, rules: list[IFieldRule] | None = None) -> None:
        self._rules = rules or default_field_rules()

    def evaluate_all(
        self,
        application: ApplicationRecord,
        extracted: ExtractedLabelRecord,
    ) -> list[FieldVerdict]:
        verdicts: list[FieldVerdict] = []
        for rule in self._rules:
            verdict = rule.evaluate(application, extracted)
            if extracted.extraction_confidence < 0.4 and verdict.status == VerdictStatus.MATCH:
                verdict = FieldVerdict(
                    field=verdict.field,
                    status=VerdictStatus.UNABLE_TO_VERIFY,
                    application_value=verdict.application_value,
                    label_value=verdict.label_value,
                    reason="Low OCR confidence — cannot verify safely.",
                    confidence=extracted.extraction_confidence,
                )
            verdicts.append(verdict)
        return verdicts
