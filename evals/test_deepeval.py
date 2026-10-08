"""DeepEval replay. The metric is exact intent match, not an LLM judge.

Compliance is not scored here. A judge model does not get a vote on disclosure.
"""

from __future__ import annotations

import pytest

deepeval = pytest.importorskip("deepeval")
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from evals.harness import replay_all


class IntentReplayMetric(BaseMetric):
    def __init__(self) -> None:
        self.threshold = 0.85
        self.score = 0.0
        self.success = False
        self.reason = ""

    def measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        self.score = 1.0 if test_case.actual_output == test_case.expected_output else 0.0
        self.success = self.score >= self.threshold
        self.reason = "exact intent match" if self.success else "intent miss"
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success


def test_deepeval_replays_labeled_intents():
    metric = IntentReplayMetric()
    scored = 0
    passed = 0
    for replay in replay_all("v2"):
        for turn, result in zip(replay.case["turns"], replay.results):
            if not turn.get("gold_intent"):
                continue
            case = LLMTestCase(
                input=turn["user"],
                actual_output=result.intent or "",
                expected_output=turn["gold_intent"],
            )
            metric.measure(case)
            scored += 1
            passed += int(metric.is_successful())
    assert scored >= 70
    assert passed / scored >= 0.85
