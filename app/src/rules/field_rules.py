"""Individual TTB field verification rules."""

from __future__ import annotations

from src.domain.constants import GOVERNMENT_WARNING_CANONICAL
from src.domain.interfaces import IFieldRule
from src.domain.models import ApplicationRecord, ExtractedLabelRecord, FieldVerdict, VerdictStatus
from src.rules.normalize import extract_abv_numbers, normalize_brand, normalize_text, normalize_units


def _verdict(
    field: str,
    status: VerdictStatus,
    app_val: str | None,
    label_val: str | None,
    reason: str,
    confidence: float = 1.0,
) -> FieldVerdict:
    return FieldVerdict(
        field=field,
        status=status,
        application_value=app_val,
        label_value=label_val,
        reason=reason,
        confidence=confidence,
    )


def _skip_if_empty(field: str, app_val: str | None, label_val: str | None) -> FieldVerdict | None:
    if not app_val and not label_val:
        return _verdict(field, VerdictStatus.UNABLE_TO_VERIFY, app_val, label_val, "Field not provided in application or label.")
    if not app_val:
        return _verdict(field, VerdictStatus.UNABLE_TO_VERIFY, app_val, label_val, "Application value missing.")
    if not label_val:
        return _verdict(field, VerdictStatus.UNABLE_TO_VERIFY, app_val, label_val, "Could not extract value from label.")
    return None


class BrandFuzzyRule(IFieldRule):
    @property
    def field_name(self) -> str:
        return "brand_name"

    def evaluate(self, application: ApplicationRecord, extracted: ExtractedLabelRecord) -> FieldVerdict:
        app_val = application.brand_name
        label_val = extracted.brand_name
        skip = _skip_if_empty(self.field_name, app_val, label_val)
        if skip:
            if extracted.extraction_confidence < 0.4:
                skip.confidence = extracted.extraction_confidence
            return skip

        app_n = normalize_brand(app_val)
        label_n = normalize_brand(label_val)
        if app_n == label_n:
            if app_val != label_val:
                return _verdict(
                    self.field_name,
                    VerdictStatus.NEEDS_REVIEW,
                    app_val,
                    label_val,
                    "Brand names equivalent after normalization — casing/punctuation difference (Dave Morrison nuance).",
                )
            return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Brand names match.")
        if app_n.replace(" ", "") == label_n.replace(" ", ""):
            return _verdict(
                self.field_name,
                VerdictStatus.NEEDS_REVIEW,
                app_val,
                label_val,
                "Brand names differ only by spacing/punctuation — likely equivalent (human review recommended).",
            )
        if app_n in label_n or label_n in app_n:
            return _verdict(
                self.field_name,
                VerdictStatus.NEEDS_REVIEW,
                app_val,
                label_val,
                "Brand names are similar — casing or punctuation difference (Dave Morrison nuance).",
            )
        return _verdict(self.field_name, VerdictStatus.MISMATCH, app_val, label_val, "Brand names do not match.")


class ClassTypeRule(IFieldRule):
    @property
    def field_name(self) -> str:
        return "class_type"

    def evaluate(self, application: ApplicationRecord, extracted: ExtractedLabelRecord) -> FieldVerdict:
        app_val = application.class_type
        label_val = extracted.class_type
        skip = _skip_if_empty(self.field_name, app_val, label_val)
        if skip:
            return skip
        if normalize_text(app_val) == normalize_text(label_val):
            return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Class/type matches.")
        return _verdict(self.field_name, VerdictStatus.MISMATCH, app_val, label_val, "Class/type designation mismatch.")


class ABVPatternRule(IFieldRule):
    @property
    def field_name(self) -> str:
        return "alcohol_content"

    def evaluate(self, application: ApplicationRecord, extracted: ExtractedLabelRecord) -> FieldVerdict:
        app_val = application.alcohol_content
        label_val = extracted.alcohol_content
        skip = _skip_if_empty(self.field_name, app_val, label_val)
        if skip:
            return skip
        app_pct, app_proof = extract_abv_numbers(app_val)
        label_pct, label_proof = extract_abv_numbers(label_val)
        if app_pct is not None and label_pct is not None and abs(app_pct - label_pct) < 0.01:
            return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Alcohol content matches.")
        if app_proof is not None and label_proof is not None and abs(app_proof - label_proof) < 0.01:
            return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Proof matches.")
        if normalize_text(app_val) == normalize_text(label_val):
            return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Alcohol content text matches.")
        return _verdict(self.field_name, VerdictStatus.MISMATCH, app_val, label_val, "Alcohol content mismatch.")


class NetContentsRule(IFieldRule):
    @property
    def field_name(self) -> str:
        return "net_contents"

    def evaluate(self, application: ApplicationRecord, extracted: ExtractedLabelRecord) -> FieldVerdict:
        app_val = application.net_contents
        label_val = extracted.net_contents
        skip = _skip_if_empty(self.field_name, app_val, label_val)
        if skip:
            return skip
        if normalize_units(app_val) == normalize_units(label_val):
            return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Net contents match.")
        return _verdict(self.field_name, VerdictStatus.MISMATCH, app_val, label_val, "Net contents mismatch.")


class WarningExactRule(IFieldRule):
    @property
    def field_name(self) -> str:
        return "government_warning"

    def evaluate(self, application: ApplicationRecord, extracted: ExtractedLabelRecord) -> FieldVerdict:
        app_val = application.government_warning or GOVERNMENT_WARNING_CANONICAL
        label_val = extracted.government_warning
        if not label_val:
            return _verdict(
                self.field_name,
                VerdictStatus.UNABLE_TO_VERIFY,
                app_val,
                label_val,
                "Government warning not detected on label.",
                confidence=extracted.extraction_confidence,
            )
        if "government warning:" in label_val and "GOVERNMENT WARNING:" not in label_val:
            return _verdict(
                self.field_name,
                VerdictStatus.MISMATCH,
                app_val,
                label_val,
                "Warning header must be 'GOVERNMENT WARNING:' in all caps (Jenny Park).",
            )
        if not label_val.strip().startswith("GOVERNMENT WARNING:"):
            return _verdict(
                self.field_name,
                VerdictStatus.MISMATCH,
                app_val,
                label_val,
                "Warning header must start with 'GOVERNMENT WARNING:' in all caps.",
            )
        canonical = GOVERNMENT_WARNING_CANONICAL
        norm_label = normalize_text(label_val)
        norm_canon = normalize_text(canonical)
        if norm_label != norm_canon:
            return _verdict(
                self.field_name,
                VerdictStatus.MISMATCH,
                app_val,
                label_val,
                "Government warning text must match exactly, word-for-word.",
            )
        if extracted.government_warning_header_bold is False:
            return _verdict(
                self.field_name,
                VerdictStatus.NEEDS_REVIEW,
                app_val,
                label_val,
                "Warning header may not be bold — verify visually (bold detection is heuristic).",
                confidence=0.7,
            )
        bold_conf = extracted.government_warning_bold_confidence
        if extracted.government_warning_header_bold is None or (
            bold_conf is not None and bold_conf < 0.5
        ):
            return _verdict(
                self.field_name,
                VerdictStatus.NEEDS_REVIEW,
                app_val,
                label_val,
                "Bold weight uncertain — verify visually.",
                confidence=0.6,
            )
        return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Government warning matches exactly.")


class AddressContainsRule(IFieldRule):
    @property
    def field_name(self) -> str:
        return "bottler_producer_address"

    def evaluate(self, application: ApplicationRecord, extracted: ExtractedLabelRecord) -> FieldVerdict:
        app_val = application.bottler_producer_address
        label_val = extracted.bottler_producer_address
        if not app_val and not label_val:
            return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Address not required for this label type.")
        skip = _skip_if_empty(self.field_name, app_val, label_val)
        if skip:
            return skip
        app_n = normalize_text(app_val)
        label_n = normalize_text(label_val)
        if app_n in label_n or label_n in app_n:
            return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Bottler/producer address matches.")
        return _verdict(self.field_name, VerdictStatus.MISMATCH, app_val, label_val, "Bottler/producer address mismatch.")


class CountryExactRule(IFieldRule):
    @property
    def field_name(self) -> str:
        return "country_of_origin"

    def evaluate(self, application: ApplicationRecord, extracted: ExtractedLabelRecord) -> FieldVerdict:
        app_val = application.country_of_origin
        label_val = extracted.country_of_origin
        if not app_val and not label_val:
            return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Country of origin not applicable.")
        skip = _skip_if_empty(self.field_name, app_val, label_val)
        if skip:
            return skip
        if normalize_text(app_val) == normalize_text(label_val):
            return _verdict(self.field_name, VerdictStatus.MATCH, app_val, label_val, "Country of origin matches.")
        return _verdict(self.field_name, VerdictStatus.MISMATCH, app_val, label_val, "Country of origin mismatch.")
