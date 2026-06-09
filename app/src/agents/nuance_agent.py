"""Brand nuance agent — proposes equivalence for casing differences."""

from __future__ import annotations

from src.domain.models import NuanceSuggestion, VerdictStatus
from src.rules.normalize import normalize_brand


class NuanceAgent:
    role = "nuance"

    async def run(self, state: dict) -> dict:
        verdicts = list(state.get("verdicts") or [])
        application = state["application"]
        extracted = state.get("extracted")
        nuance = None
        if application and extracted:
            app_b = application.brand_name or ""
            label_b = extracted.brand_name or ""
            app_n = normalize_brand(app_b)
            label_n = normalize_brand(label_b)
            equivalent = app_n == label_n or app_n.replace(" ", "") == label_n.replace(" ", "")
            if equivalent and app_b != label_b:
                nuance = NuanceSuggestion(
                    field="brand_name",
                    application_value=app_b,
                    label_value=label_b,
                    equivalent=True,
                    reason="Brand names equivalent after normalization (Dave Morrison nuance).",
                )
                for i, v in enumerate(verdicts):
                    if v.field == "brand_name" and v.status == VerdictStatus.NEEDS_REVIEW:
                        verdicts[i] = v.model_copy(
                            update={"reason": nuance.reason + " Flagged for human confirmation."}
                        )
        return {**state, "nuance": nuance, "verdicts": verdicts, "route": "nuance"}
