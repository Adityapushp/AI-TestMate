"""Explainable local checks plus optional DeepEval metrics."""
import os
import re
from dataclasses import dataclass, asdict

@dataclass
class Evaluation:
    passed: bool
    score: float
    relevance: float
    groundedness_proxy: float
    safety_passed: bool
    feedback: list[str]
    deepeval: dict | None = None

def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))

class LocalEvaluator:
    """A deterministic baseline evaluator; not a semantic LLM judge."""
    def evaluate(self, case: dict, answer: str, contexts: list[str]) -> Evaluation:
        feedback = []
        expected = _tokens(case.get("expected_answer", ""))
        actual = _tokens(answer)
        keywords = set(case.get("must_include", []))
        keyword_hits = sum(1 for word in keywords if word.lower() in answer.lower())
        overlap = len(expected & actual) / max(1, len(expected))
        relevance = min(1.0, 0.65 * overlap + 0.35 * (keyword_hits / max(1, len(keywords))))
        context_tokens = set().union(*(_tokens(c) for c in contexts)) if contexts else set()
        groundedness = len(actual & context_tokens) / max(1, len(actual))
        safety_terms = case.get("must_not_include", [])
        safety_passed = not any(term.lower() in answer.lower() for term in safety_terms)
        if relevance < 0.20:
            feedback.append("The answer has low overlap with the expected answer; review relevance.")
        if not safety_passed:
            feedback.append("The answer contains a prohibited phrase from this test case.")
        if not feedback:
            feedback.append("Passed the configured local checks.")
        score = round((relevance * 0.65 + groundedness * 0.20 + (1.0 if safety_passed else 0.0) * 0.15), 3)
        passed = relevance >= 0.20 and safety_passed
        return Evaluation(passed, score, round(relevance, 3), round(groundedness, 3), safety_passed, feedback)

def add_deepeval_metrics(case: dict, answer: str, contexts: list[str]) -> dict | None:
    """Run optional DeepEval judge metrics. Requires deepeval and judge-model credentials."""
    if os.getenv("AI_TESTMATE_USE_DEEPEVAL", "false").lower() != "true":
        return None
    try:
        from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
        from deepeval.test_case import LLMTestCase
        test_case = LLMTestCase(
            input=case["question"],
            actual_output=answer,
            expected_output=case.get("expected_answer", ""),
            retrieval_context=contexts or ["No retrieval context supplied."],
        )
        relevance = AnswerRelevancyMetric(threshold=0.5)
        faithfulness = FaithfulnessMetric(threshold=0.5)
        relevance.measure(test_case)
        faithfulness.measure(test_case)
        return {
            "answer_relevancy": round(float(relevance.score or 0), 3),
            "faithfulness": round(float(faithfulness.score or 0), 3),
            "reasons": [str(relevance.reason or ""), str(faithfulness.reason or "")],
        }
    except ImportError as exc:
        return {"error": f"DeepEval is not installed: {exc}"}
    except Exception as exc:
        return {"error": f"DeepEval evaluation failed: {type(exc).__name__}: {exc}"}
