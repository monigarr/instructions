"""
===============================================================================
FILE: rules_engine_agent.py
AUTHOR: MoniGarr (Monica Peters)
CLASSIFICATION: Internal

PURPOSE:
IAgentNode — runs IRulesEngine; owns deterministic verdict bits.
===============================================================================
"""

from __future__ import annotations

from src.domain.interfaces import IRulesEngine


class RulesEngineAgent:
    role = "rules_engine"

    def __init__(self, engine: IRulesEngine) -> None:
        self._engine = engine

    async def run(self, state: dict) -> dict:
        application = state["application"]
        extracted = state.get("extracted")
        if not extracted:
            errors = list(state.get("errors") or [])
            errors.append("Missing extracted fields for rules evaluation.")
            return {**state, "errors": errors, "status": "failed"}
        verdicts = self._engine.evaluate_all(application, extracted)
        return {**state, "verdicts": verdicts, "route": "rules"}
