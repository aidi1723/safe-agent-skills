from __future__ import annotations

import math
import unittest

from onecode_skill_sanitizer.semantic_provider import rerank_candidates


class FakeProvider:
    name = "fake"
    model_or_adapter = "fixture-v1"

    def __init__(self, response):
        self.response = response
        self.requests = []

    def rerank(self, request):
        self.requests.append(request)
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


def candidates():
    return [
        {"skill": "design-ui-review", "deterministic_score": 0.7, "semantic_score": None, "final_score": 0.7},
        {"skill": "execution-browser-check", "deterministic_score": 0.6, "semantic_score": None, "final_score": 0.6},
    ]


class SemanticProviderTest(unittest.TestCase):
    def test_shadow_records_scores_without_changing_final_order(self):
        provider = FakeProvider({
            "status": "ok",
            "scores": [
                {"skill": "design-ui-review", "score": 0.1, "confidence": 0.8},
                {"skill": "execution-browser-check", "score": 0.9, "confidence": 0.8},
            ],
        })
        routed, record = rerank_candidates("review the UI", {}, candidates(), provider, mode="shadow")

        self.assertEqual([item["skill"] for item in routed], ["design-ui-review", "execution-browser-check"])
        self.assertEqual([item["semantic_score"] for item in routed], [0.1, 0.9])
        self.assertEqual([item["final_score"] for item in routed], [0.7, 0.6])
        self.assertEqual(record["response_status"], "accepted_shadow")
        self.assertRegex(record["candidate_scope_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_invalid_response_rejects_every_semantic_score(self):
        invalid = (
            TimeoutError("timed out"),
            {"status": "ok", "scores": [{"skill": "unknown", "score": 0.5, "confidence": 0.5}]},
            {"status": "ok", "scores": [
                {"skill": "design-ui-review", "score": 0.5, "confidence": 0.5},
                {"skill": "design-ui-review", "score": 0.6, "confidence": 0.5},
            ]},
            {"status": "ok", "scores": [{"skill": "design-ui-review", "score": 0.5, "confidence": 0.5}]},
            {"status": "ok", "scores": [
                {"skill": "design-ui-review", "score": math.nan, "confidence": 0.5},
                {"skill": "execution-browser-check", "score": 0.5, "confidence": 0.5},
            ]},
            {"status": "ok", "scores": [
                {"skill": "design-ui-review", "score": 1.2, "confidence": 0.5},
                {"skill": "execution-browser-check", "score": 0.5, "confidence": 0.5},
            ]},
        )
        for response in invalid:
            with self.subTest(response=response):
                routed, record = rerank_candidates(
                    "review the UI", {}, candidates(), FakeProvider(response), mode="shadow"
                )
                self.assertTrue(all(item["semantic_score"] is None for item in routed))
                self.assertEqual([item["final_score"] for item in routed], [0.7, 0.6])
                self.assertNotEqual(record["fallback_reason"], "none")
                self.assertTrue(record["validation_reason_codes"])

    def test_low_confidence_influence_retains_deterministic_order(self):
        provider = FakeProvider({
            "status": "ok",
            "scores": [
                {"skill": "design-ui-review", "score": 0.1, "confidence": 0.4},
                {"skill": "execution-browser-check", "score": 0.9, "confidence": 0.4},
            ],
        })
        routed, record = rerank_candidates(
            "review the UI", {}, candidates(), provider, mode="influence"
        )

        self.assertEqual([item["skill"] for item in routed], ["design-ui-review", "execution-browser-check"])
        self.assertEqual([item["final_score"] for item in routed], [0.7, 0.6])
        self.assertTrue(all(item["semantic_score"] is None for item in routed))
        self.assertEqual(record["fallback_reason"], "low_semantic_confidence")


if __name__ == "__main__":
    unittest.main()
