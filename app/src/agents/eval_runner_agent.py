"""Offline eval runner agent (CI/dev)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path


class EvalRunnerAgent:
    role = "eval_runner"

    async def run(self, dataset_path: Path | None = None) -> dict:
        from evals.runners.run_eval_suite import main as run_main

        # run_eval_suite main returns exit code; invoke logic inline
        from evals.runners import run_eval_suite

        golden = await run_eval_suite.run_golden()
        adversarial = run_eval_suite.run_adversarial_warning()
        return {"golden": golden, "adversarial": adversarial}

    async def run_and_print(self) -> int:
        report = await self.run()
        print(json.dumps(report, indent=2))
        return 0
