from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import unittest

from onecode_skill_sanitizer.intent import normalize_task
from onecode_skill_sanitizer.need_gate import decide_skill_need
from onecode_skill_sanitizer.semantic_provider import rerank_candidates
from onecode_skill_sanitizer.skill_candidates import (
    HIGH_FREQUENCY_SKILL_NAMES,
    load_cohort_profiles,
    load_routing_examples,
    retrieve_skill_candidates,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "catalog/routing-examples.json"
RECORD_KEYS = {
    "requested",
    "used",
    "model_or_adapter",
    "fallback_reason",
    "candidate_scope_hash",
    "response_status",
    "validation_reason_codes",
}
CANONICAL_CAPABILITIES = {
    "codebase-explore-map": "code.explore",
    "code-review-risk": "code.review",
    "code-test-regression": "code.test",
    "execution-browser-check": "execution.browser_check",
    "research-source-check": "research.source",
    "design-ui-review": "design.ui_review",
    "security-supply-chain-review": "security.supply_chain",
}


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
        if callable(self.response):
            return self.response(request)
        return self.response


class ExplodingAccessProvider:
    def __getattribute__(self, name):
        if name in {"name", "model_or_adapter", "rerank"}:
            raise AssertionError(f"provider accessed: {name}")
        return object.__getattribute__(self, name)


class FloatSubclass(float):
    pass


class Extra:
    pass


def candidate(
    skill,
    score,
    capability,
    *,
    excluded=False,
    description=None,
    semantic_score=None,
    final_score=None,
):
    return {
        "skill": skill,
        "status": "trusted",
        "excluded": excluded,
        "description": description if description is not None else f"Trusted {skill} profile",
        "deterministic_score": score,
        "matched_capabilities": [capability] if capability else [],
        "semantic_score": semantic_score,
        "final_score": score if final_score is None else final_score,
    }


def candidates(*, contaminated=False):
    semantic_score = 0.99 if contaminated else None
    final_score = 0.01 if contaminated else None
    return [
        candidate(
            "design-ui-review",
            0.7,
            "design.ui_review",
            semantic_score=semantic_score,
            final_score=final_score,
        ),
        candidate(
            "execution-browser-check",
            0.6,
            "execution.browser_check",
            semantic_score=semantic_score,
            final_score=final_score,
        ),
    ]


def valid_response(items=None):
    items = candidates() if items is None else items
    return {
        "status": "ok",
        "scores": [
            {"skill": item["skill"], "score": 0.5, "confidence": 0.8}
            for item in items
            if not item["excluded"]
        ],
    }


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
        self.assertEqual(set(record), RECORD_KEYS)

    def test_invalid_response_rejects_every_semantic_score(self):
        invalid = (
            TimeoutError("timed out with token=secret"),
            {"status": "ok", "scores": []},
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
                original = candidates(contaminated=True)
                routed, record = rerank_candidates(
                    "review the UI", {}, original, FakeProvider(response), mode="shadow"
                )
                self.assertTrue(all(item["semantic_score"] is None for item in routed))
                self.assertEqual([item["final_score"] for item in routed], [0.7, 0.6])
                self.assertNotEqual(record["fallback_reason"], "none")
                self.assertTrue(record["validation_reason_codes"])
                self.assertNotIn("secret", json.dumps(record))

    def test_low_confidence_influence_retains_deterministic_order(self):
        provider = FakeProvider({
            "status": "ok",
            "scores": [
                {"skill": "design-ui-review", "score": 0.1, "confidence": 0.4},
                {"skill": "execution-browser-check", "score": 0.9, "confidence": 0.4},
            ],
        })
        routed, record = rerank_candidates(
            "review the UI", {}, candidates(contaminated=True), provider, mode="influence"
        )

        self.assertEqual([item["skill"] for item in routed], ["design-ui-review", "execution-browser-check"])
        self.assertEqual([item["final_score"] for item in routed], [0.7, 0.6])
        self.assertTrue(all(item["semantic_score"] is None for item in routed))
        self.assertEqual(record["fallback_reason"], "low_semantic_confidence")

    def test_invalid_modes_raise_before_any_provider_access(self):
        for mode in ("bogus", "", None, False, 1):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(ValueError, "^mode must be one of none, shadow, influence$"):
                    rerank_candidates(
                        "review the UI", {}, candidates(), ExplodingAccessProvider(), mode=mode
                    )

    def test_not_requested_paths_return_cloned_cleared_baseline(self):
        cases = (
            ("no provider", None, "shadow", candidates(contaminated=True)),
            ("mode none", ExplodingAccessProvider(), "none", candidates(contaminated=True)),
            (
                "fewer than two eligible",
                ExplodingAccessProvider(),
                "shadow",
                [
                    candidates(contaminated=True)[0],
                    {
                        **candidates(contaminated=True)[1],
                        "excluded": True,
                        "deterministic_score": 0.0,
                    },
                ],
            ),
        )
        for label, provider, mode, original in cases:
            with self.subTest(label=label):
                routed, record = rerank_candidates(
                    "review the UI", {}, original, provider, mode=mode
                )
                self.assertEqual(
                    [item["final_score"] for item in routed],
                    [item["deterministic_score"] for item in original],
                )
                self.assertTrue(all(item["semantic_score"] is None for item in routed))
                self.assertTrue(all(left is not right for left, right in zip(routed, original)))
                self.assertEqual(record["response_status"], "not_requested")

    def test_candidates_are_validated_before_not_requested_return(self):
        malformed = candidates()
        del malformed[0]["skill"]
        with self.assertRaisesRegex(ValueError, r"^candidate\[0\]"):
            rerank_candidates("review the UI", {}, malformed, None, mode="none")

    def test_candidate_contract_rejects_malformed_untrusted_or_unbounded_values(self):
        base = candidates()
        cases = []

        def changed(index, field, value):
            result = copy.deepcopy(base)
            if value is DELETE:
                del result[index][field]
            else:
                result[index][field] = value
            return result

        cases.extend((
            ("not list", tuple(base)),
            ("too many", [copy.deepcopy(base[0]) for _ in range(8)]),
            ("not object", [None]),
            ("skill missing", changed(0, "skill", DELETE)),
            ("score missing", changed(0, "deterministic_score", DELETE)),
            ("out of cohort", changed(0, "skill", "safe-agent-router")),
            ("duplicate", [copy.deepcopy(base[0]), copy.deepcopy(base[0])]),
            ("untrusted", changed(0, "status", "draft")),
            ("excluded type", changed(0, "excluded", 0)),
            ("score bool", changed(0, "deterministic_score", True)),
            ("score subclass", changed(0, "deterministic_score", FloatSubclass(0.5))),
            ("score nan", changed(0, "deterministic_score", math.nan)),
            ("score inf", changed(0, "deterministic_score", math.inf)),
            ("score low", changed(0, "deterministic_score", -0.1)),
            ("score high", changed(0, "deterministic_score", 1.1)),
            ("description type", changed(0, "description", [])),
            ("description long", changed(0, "description", "x" * 4097)),
            ("capabilities type", changed(0, "matched_capabilities", "design.ui_review")),
            ("capability blank", changed(0, "matched_capabilities", [" "])),
            ("capability duplicate", changed(0, "matched_capabilities", ["design.ui_review"] * 2)),
            ("capability unknown", changed(0, "matched_capabilities", ["unknown.capability"])),
        ))
        for label, value in cases:
            with self.subTest(label=label):
                with self.assertRaises(ValueError) as context:
                    rerank_candidates("review the UI", {}, value, None, mode="none")
                self.assertLessEqual(len(str(context.exception)), 128)

    def test_candidate_capabilities_are_bound_to_each_fixed_skill_identity(self):
        for skill, capability in CANONICAL_CAPABILITIES.items():
            with self.subTest(skill=skill, valid="empty"):
                routed, _ = rerank_candidates(
                    "review", {}, [candidate(skill, 0.5, "")], None, mode="none"
                )
                self.assertEqual(routed[0]["matched_capabilities"], [])
            with self.subTest(skill=skill, valid="canonical"):
                routed, _ = rerank_candidates(
                    "review", {}, [candidate(skill, 0.5, capability)], None, mode="none"
                )
                self.assertEqual(routed[0]["matched_capabilities"], [capability])

        invalid = (
            ["security.supply_chain"],
            ["design.ui_review", "security.supply_chain"],
        )
        for capabilities in invalid:
            with self.subTest(capabilities=capabilities):
                item = candidate("design-ui-review", 0.5, "")
                item["matched_capabilities"] = capabilities
                with self.assertRaisesRegex(
                    ValueError,
                    r"^candidate\[0\]\.matched_capabilities",
                ):
                    rerank_candidates("review", {}, [item], None, mode="none")

    def test_excluded_candidate_requires_zero_deterministic_score(self):
        item = candidate(
            "design-ui-review", 1.0, "design.ui_review", excluded=True
        )

        with self.assertRaisesRegex(
            ValueError,
            r"^candidate\[0\]\.deterministic_score",
        ):
            rerank_candidates("review", {}, [item], None, mode="none")

        for zero in (0, 0.0):
            with self.subTest(zero=zero):
                valid = candidate(
                    "design-ui-review", zero, "", excluded=True
                )
                routed, _ = rerank_candidates(
                    "review", {}, [valid], None, mode="none"
                )
                self.assertEqual(routed[0]["final_score"], zero)

    def test_complete_candidate_output_is_allowlisted_bounded_strict_json(self):
        unknown = candidate("design-ui-review", 0.5, "design.ui_review")
        unknown["unexpected"] = Extra()
        custom = candidate("design-ui-review", 0.5, "design.ui_review")
        custom["positive_evidence"] = [Extra()]
        nonfinite = candidate("design-ui-review", 0.5, "design.ui_review")
        nonfinite["positive_evidence"] = [{"weight": math.nan}]
        oversized = candidate("design-ui-review", 0.5, "design.ui_review")
        oversized["reason_codes"] = ["x" * (64 * 1024)]

        for label, value in (
            ("unknown custom field", unknown),
            ("custom allowed field", custom),
            ("nonfinite allowed field", nonfinite),
            ("oversized allowed field", oversized),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError) as context:
                    rerank_candidates("review", {}, [value], None, mode="none")
                self.assertLessEqual(len(str(context.exception)), 128)

    def test_excluded_task4_candidate_never_enters_or_expands_provider_scope(self):
        task = normalize_task("Do not critique design; run the existing UI flow in a browser")
        need = decide_skill_need(task)
        task4_candidates = retrieve_skill_candidates(
            task,
            need,
            load_cohort_profiles(ROOT / "catalog"),
            load_routing_examples(EXAMPLES),
        )
        provider = FakeProvider(
            lambda request: {
                "status": "ok",
                "scores": [
                    {"skill": item["skill"], "score": 0.8, "confidence": 0.9}
                    for item in request["candidates"]
                ],
            }
        )

        routed, record = rerank_candidates(task.current, need, task4_candidates, provider, mode="shadow")

        request_names = [item["skill"] for item in provider.requests[0]["candidates"]]
        design = next(item for item in routed if item["skill"] == "design-ui-review")
        self.assertNotIn("design-ui-review", request_names)
        self.assertTrue(design["excluded"])
        self.assertIsNone(design["semantic_score"])
        self.assertEqual(design["final_score"], 0.0)
        self.assertEqual(record["response_status"], "accepted_shadow")

        extra = valid_response([item for item in task4_candidates if not item["excluded"]])
        extra["scores"].append(
            {"skill": "design-ui-review", "score": 1.0, "confidence": 1.0}
        )
        rejected, rejected_record = rerank_candidates(
            task.current, need, task4_candidates, FakeProvider(extra), mode="shadow"
        )
        self.assertTrue(all(item["semantic_score"] is None for item in rejected))
        self.assertEqual(rejected_record["fallback_reason"], "invalid_provider_response")

    def test_influence_sorts_eligible_first_and_never_revives_excluded(self):
        original = [
            candidate("design-ui-review", 0.7, "design.ui_review"),
            candidate("code-review-risk", 0.0, "", excluded=True),
            candidate("execution-browser-check", 0.6, "execution.browser_check"),
        ]
        response = {
            "status": "ok",
            "scores": [
                {"skill": "design-ui-review", "score": 0.1, "confidence": 0.8},
                {"skill": "execution-browser-check", "score": 0.9, "confidence": 0.8},
            ],
        }

        shadow, _ = rerank_candidates("review", {}, original, FakeProvider(response), mode="shadow")
        influenced, record = rerank_candidates(
            "review", {}, original, FakeProvider(response), mode="influence"
        )

        self.assertEqual([item["skill"] for item in shadow], [item["skill"] for item in original])
        self.assertEqual(
            [item["skill"] for item in influenced],
            ["execution-browser-check", "design-ui-review", "code-review-risk"],
        )
        self.assertIsNone(influenced[-1]["semantic_score"])
        self.assertEqual(influenced[-1]["final_score"], 0.0)
        self.assertEqual(record["response_status"], "accepted_influence")

    def test_constraints_reject_unknown_nested_and_wrong_primitive_values(self):
        invalid = (
            None,
            {"password": "secret"},
            {"missing_inputs": [{"token": "secret"}]},
            {"missing_inputs": ["duplicate", "duplicate"]},
            {"specialized_need": 1},
            {"decision": False},
        )
        for value in invalid:
            with self.subTest(value=value):
                provider = FakeProvider(valid_response())
                with self.assertRaises(ValueError):
                    rerank_candidates("review", value, candidates(), provider, mode="shadow")
                self.assertEqual(provider.requests, [])

    def test_request_is_redacted_detached_json_and_provider_mutation_safe(self):
        original_candidates = candidates()
        original_candidates[0]["description"] = "Review UI api_key=alpha"
        original_constraints = {
            "decision": "single",
            "specialized_need": True,
            "required_capabilities": ["design.ui_review"],
            "explicit_skills": [],
            "excluded_skills": [],
            "explanation_only": False,
            "inventory_only": False,
            "missing_inputs": ["token=alpha"],
            "mandatory_capabilities": [],
            "policy_block_reasons": [],
            "reason_codes": ["api_key=alpha"],
        }
        snapshot = {}

        def mutate(request):
            snapshot.update(copy.deepcopy(request))
            request["constraints"]["missing_inputs"][0] = "changed"
            request["candidates"][0]["matched_capabilities"].append("changed")
            return valid_response()

        routed, _ = rerank_candidates(
            "review token=alpha", original_constraints, original_candidates,
            FakeProvider(mutate), mode="shadow"
        )

        encoded = json.dumps(snapshot, allow_nan=False, sort_keys=True)
        self.assertNotIn("alpha", encoded)
        self.assertIn("[REDACTED]", encoded)
        self.assertEqual(
            set(snapshot), {"current_intent", "constraints", "candidates"}
        )
        self.assertEqual(
            set(snapshot["candidates"][0]),
            {"skill", "description", "deterministic_score", "matched_capabilities"},
        )
        self.assertEqual(original_constraints["missing_inputs"], ["token=alpha"])
        self.assertEqual(original_candidates[0]["matched_capabilities"], ["design.ui_review"])
        self.assertEqual([item["final_score"] for item in routed], [0.7, 0.6])

    def test_intent_constraints_and_request_envelope_are_bounded(self):
        cases = (
            (None, {}, candidates()),
            (1, {}, candidates()),
            (str("x") * 16385, {}, candidates()),
            ("review", {"missing_inputs": [f"value-{index}-" + "x" * 4000 for index in range(20)]}, candidates()),
        )
        for intent, constraints, candidate_items in cases:
            with self.subTest(intent_type=type(intent).__name__, constraints=bool(constraints)):
                provider = FakeProvider(valid_response())
                with self.assertRaises(ValueError):
                    rerank_candidates(intent, constraints, candidate_items, provider, mode="shadow")
                self.assertEqual(provider.requests, [])

    def test_scope_hash_binds_complete_sanitized_request_deterministically(self):
        def route(intent, constraints):
            _, record = rerank_candidates(
                intent, constraints, candidates(), FakeProvider(valid_response()), mode="shadow"
            )
            return record["candidate_scope_hash"]

        first = route("review UI", {"missing_inputs": ["first context"]})
        repeated = route("review UI", {"missing_inputs": ["first context"]})
        changed_intent = route("audit UI", {"missing_inputs": ["first context"]})
        changed_constraints = route("review UI", {"missing_inputs": ["second context"]})
        redacted_first = route("review token=alpha", {"missing_inputs": ["api_key=alpha"]})
        redacted_second = route("review token=beta", {"missing_inputs": ["api_key=beta"]})

        self.assertEqual(first, repeated)
        self.assertNotEqual(first, changed_intent)
        self.assertNotEqual(first, changed_constraints)
        self.assertEqual(redacted_first, redacted_second)

    def test_provider_metadata_lookup_call_and_validation_are_contained(self):
        class RaisingName:
            @property
            def name(self):
                raise RuntimeError("token=secret-name")

        class RaisingAdapter:
            name = "fake"

            @property
            def model_or_adapter(self):
                raise LookupError("token=secret-adapter")

        class MissingRerank:
            name = "fake"
            model_or_adapter = "fixture-v1"

        class NoncallableRerank(MissingRerank):
            rerank = 1

        providers = (
            RaisingName(),
            RaisingAdapter(),
            MissingRerank(),
            NoncallableRerank(),
            FakeProvider(RuntimeError("token=secret-call")),
        )
        for provider in providers:
            with self.subTest(provider=type(provider).__name__):
                routed, record = rerank_candidates(
                    "review", {}, candidates(contaminated=True), provider, mode="shadow"
                )
                self.assertTrue(all(item["semantic_score"] is None for item in routed))
                self.assertEqual([item["final_score"] for item in routed], [0.7, 0.6])
                self.assertEqual(record["fallback_reason"], "provider_failure")
                self.assertRegex(record["validation_reason_codes"][0], r"^provider_exception:[A-Za-z]+Error$")
                self.assertNotIn("secret", json.dumps(record))

    def test_invalid_provider_metadata_uses_safe_literals_and_valid_metadata_is_redacted(self):
        class MetadataProvider(FakeProvider):
            pass

        invalid = (
            (None, "fixture-v1"),
            ("", "fixture-v1"),
            ("x" * 129, "fixture-v1"),
            ("fake", None),
            ("fake", ""),
            ("fake", "x" * 129),
        )
        for name, adapter in invalid:
            with self.subTest(name=name, adapter=adapter):
                provider = MetadataProvider(valid_response())
                provider.name = name
                provider.model_or_adapter = adapter
                _, record = rerank_candidates("review", {}, candidates(), provider, mode="shadow")
                self.assertEqual(record["requested"], "invalid_provider")
                self.assertEqual(record["model_or_adapter"], "none")
                self.assertEqual(record["fallback_reason"], "provider_failure")

        provider = MetadataProvider(valid_response())
        provider.name = "provider api_key=alpha"
        provider.model_or_adapter = "model token=beta"
        _, record = rerank_candidates("review", {}, candidates(), provider, mode="shadow")
        self.assertNotIn("alpha", record["requested"])
        self.assertNotIn("beta", record["model_or_adapter"])
        self.assertIn("[REDACTED]", record["requested"])
        self.assertIn("[REDACTED]", record["model_or_adapter"])

    def test_response_validator_rejects_schema_scope_and_hostile_primitives_without_throwing(self):
        valid_scores = valid_response()["scores"]
        invalid = (
            None,
            [],
            {"status": "ok", "scores": valid_scores, "extra": True},
            {"status": "bad", "scores": valid_scores},
            {"status": "ok", "scores": "bad"},
            {"status": "ok", "scores": []},
            {"status": "ok", "scores": [None, valid_scores[1]]},
            {"status": "ok", "scores": [{"skill": ["design-ui-review"], "score": 0.5, "confidence": 0.8}, valid_scores[1]]},
            {"status": "ok", "scores": [{"skill": "safe-agent-router", "score": 0.5, "confidence": 0.8}, valid_scores[1]]},
            {"status": "ok", "scores": [{"skill": "design-ui-review", "score": FloatSubclass(0.5), "confidence": 0.8}, valid_scores[1]]},
            {"status": "ok", "scores": [{"skill": "design-ui-review", "score": 0.5, "confidence": FloatSubclass(0.8)}, valid_scores[1]]},
            {"status": "ok", "scores": [{"skill": "design-ui-review", "score": True, "confidence": 0.8}, valid_scores[1]]},
            {"status": "ok", "scores": [{"skill": "design-ui-review", "score": 0.5, "confidence": math.inf}, valid_scores[1]]},
            {"status": "ok", "scores": [{"skill": "design-ui-review", "score": 0.5}, valid_scores[1]]},
            {"status": "ok", "scores": [{"skill": "design-ui-review", "score": 0.5, "confidence": 0.8, "extra": 1}, valid_scores[1]]},
        )
        for response in invalid:
            with self.subTest(response=response):
                routed, record = rerank_candidates(
                    "review", {}, candidates(contaminated=True), FakeProvider(response), mode="shadow"
                )
                self.assertTrue(all(item["semantic_score"] is None for item in routed))
                self.assertEqual(record["fallback_reason"], "invalid_provider_response")
                self.assertTrue(record["validation_reason_codes"])

    def test_schema_bounds_and_enumerates_the_fixed_candidate_cohort(self):
        schema = json.loads(
            (ROOT / "schemas/semantic-rerank-response.schema.json").read_text(encoding="utf-8")
        )
        scores = schema["properties"]["scores"]
        skill = scores["items"]["properties"]["skill"]

        self.assertEqual(scores["minItems"], 1)
        self.assertEqual(scores["maxItems"], 7)
        self.assertEqual(skill["enum"], list(HIGH_FREQUENCY_SKILL_NAMES))


DELETE = object()


if __name__ == "__main__":
    unittest.main()
