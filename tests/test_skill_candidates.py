from __future__ import annotations

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from onecode_skill_sanitizer.skill_candidates import (
    HIGH_FREQUENCY_ENTRY_NAMES,
    HIGH_FREQUENCY_SKILL_NAMES,
    RoutingExampleError,
    load_routing_examples,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "catalog/routing-examples.json"
DELETE = object()


class SkillCandidateTest(unittest.TestCase):
    def test_runtime_examples_are_reviewed_and_limited_to_the_fixed_cohort(self):
        examples = load_routing_examples(EXAMPLES)
        classes = Counter(example["example_class"] for example in examples)

        self.assertEqual(HIGH_FREQUENCY_ENTRY_NAMES[0], "safe-agent-router")
        self.assertEqual(len(HIGH_FREQUENCY_ENTRY_NAMES), 8)
        self.assertEqual(len(HIGH_FREQUENCY_SKILL_NAMES), 7)
        self.assertEqual(len(examples), 35)
        self.assertEqual(
            classes,
            Counter(
                {
                    "positive": 21,
                    "near_miss": 7,
                    "explanation_only": 1,
                    "negation": 1,
                    "composition": 5,
                }
            ),
        )
        self.assertEqual(
            {name for example in examples for name in example["required_skills"]},
            set(HIGH_FREQUENCY_SKILL_NAMES),
        )
        self.assertTrue(all(example["review"]["status"] == "approved" for example in examples))
        self.assertTrue(all(example["review"]["generated_from_router"] is False for example in examples))

    def test_loader_rejects_unreviewed_out_of_cohort_and_overlapping_labels(self):
        payload = json.loads(EXAMPLES.read_text(encoding="utf-8"))
        mutations = (
            lambda item: item["review"].update(status="draft"),
            lambda item: item.update(required_skills=["execution-publish-check"]),
            lambda item: item.update(forbidden_skills=item["required_skills"]),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as temp_dir:
                changed = json.loads(json.dumps(payload))
                mutate(changed["examples"][0])
                path = Path(temp_dir) / "routing-examples.json"
                path.write_text(json.dumps(changed), encoding="utf-8")
                with self.assertRaises(RoutingExampleError):
                    load_routing_examples(path)

    def test_loader_rejects_every_malformed_contract_branch(self):
        payload = json.loads(EXAMPLES.read_text(encoding="utf-8"))
        first_query = payload["examples"][0]["query"]
        first_id = payload["examples"][0]["id"]
        cases = (
            ("top-level type", (), []),
            ("top-level missing key", ("scope",), DELETE),
            ("top-level extra key", ("unexpected",), True),
            ("schema true", ("schema_version",), True),
            ("schema false", ("schema_version",), False),
            ("schema float", ("schema_version",), 1.0),
            ("schema string", ("schema_version",), "1"),
            ("schema unknown", ("schema_version",), 2),
            ("scope mismatch", ("scope", "candidate_names"), []),
            ("examples not list", ("examples",), {}),
            ("example not object", ("examples", 0), []),
            ("example missing field", ("examples", 0, "query"), DELETE),
            ("example extra field", ("examples", 0, "unexpected"), True),
            ("id blank", ("examples", 0, "id"), " \t"),
            ("id not string", ("examples", 0, "id"), 1),
            ("id duplicate", ("examples", 1, "id"), first_id),
            ("query blank", ("examples", 0, "query"), " \t"),
            ("query not string", ("examples", 0, "query"), []),
            (
                "query normalized duplicate",
                ("examples", 1, "query"),
                "  " + "   ".join(first_query.upper().split()) + "  ",
            ),
            ("need list", ("examples", 0, "expected_need"), []),
            ("need object", ("examples", 0, "expected_need"), {}),
            ("need not string", ("examples", 0, "expected_need"), 1),
            ("need unknown", ("examples", 0, "expected_need"), "unknown"),
            ("class list", ("examples", 0, "example_class"), []),
            ("class object", ("examples", 0, "example_class"), {}),
            ("class not string", ("examples", 0, "example_class"), 1),
            ("class unknown", ("examples", 0, "example_class"), "unknown"),
            ("required not list", ("examples", 0, "required_skills"), "codebase-explore-map"),
            ("required blank", ("examples", 0, "required_skills"), [" "]),
            ("required non-string", ("examples", 0, "required_skills"), [1]),
            (
                "required duplicate",
                ("examples", 0, "required_skills"),
                ["codebase-explore-map", "codebase-explore-map"],
            ),
            ("forbidden not list", ("examples", 0, "forbidden_skills"), "code-review-risk"),
            ("forbidden blank", ("examples", 0, "forbidden_skills"), [" "]),
            ("forbidden non-string", ("examples", 0, "forbidden_skills"), [1]),
            (
                "forbidden duplicate",
                ("examples", 0, "forbidden_skills"),
                ["code-review-risk", "code-review-risk"],
            ),
            ("intent not list", ("examples", 0, "intent_labels"), "code.explore"),
            ("intent blank", ("examples", 0, "intent_labels"), [" "]),
            ("intent non-string", ("examples", 0, "intent_labels"), [1]),
            ("intent duplicate", ("examples", 0, "intent_labels"), ["code.explore", "code.explore"]),
            ("capability not list", ("examples", 0, "capability_labels"), "code.explore"),
            ("capability blank", ("examples", 0, "capability_labels"), [" "]),
            ("capability non-string", ("examples", 0, "capability_labels"), [1]),
            (
                "capability duplicate",
                ("examples", 0, "capability_labels"),
                ["code.explore", "code.explore"],
            ),
            (
                "out-of-cohort skill",
                ("examples", 0, "required_skills"),
                ["execution-publish-check"],
            ),
            (
                "required forbidden overlap",
                ("examples", 0, "forbidden_skills"),
                ["codebase-explore-map"],
            ),
            ("review not object", ("examples", 0, "review"), []),
            ("review missing key", ("examples", 0, "review", "reviewed_at"), DELETE),
            ("review extra key", ("examples", 0, "review", "unexpected"), True),
            ("review status", ("examples", 0, "review", "status"), "draft"),
            ("review generated true", ("examples", 0, "review", "generated_from_router"), True),
            ("review generated zero", ("examples", 0, "review", "generated_from_router"), 0),
            (
                "reviewer role",
                ("examples", 0, "review", "reviewer_role"),
                "automated_router",
            ),
            ("reviewer role blank", ("examples", 0, "review", "reviewer_role"), " "),
            (
                "source classification",
                ("examples", 0, "review", "source_classification"),
                "router_output",
            ),
            (
                "source classification blank",
                ("examples", 0, "review", "source_classification"),
                " ",
            ),
            ("review date not string", ("examples", 0, "review", "reviewed_at"), 20260715),
            ("review date blank", ("examples", 0, "review", "reviewed_at"), " "),
            ("review date format", ("examples", 0, "review", "reviewed_at"), "2026/07/15"),
            ("review date compact", ("examples", 0, "review", "reviewed_at"), "20260715"),
            ("review date impossible", ("examples", 0, "review", "reviewed_at"), "2026-02-30"),
        )

        for name, path, value in cases:
            with self.subTest(name=name):
                changed = json.loads(json.dumps(payload))
                if path:
                    target = changed
                    for part in path[:-1]:
                        target = target[part]
                    if value is DELETE:
                        del target[path[-1]]
                    else:
                        target[path[-1]] = value
                else:
                    changed = value
                self._assert_payload_rejected(changed)

    def test_loader_accepts_a_future_valid_review_date(self):
        payload = json.loads(EXAMPLES.read_text(encoding="utf-8"))
        payload["examples"][0]["review"]["reviewed_at"] = "2027-01-01"

        self.assertEqual(len(self._load_temporary_payload(payload)), 35)

    def _assert_payload_rejected(self, payload):
        with self.assertRaises(RoutingExampleError):
            self._load_temporary_payload(payload)

    def _load_temporary_payload(self, payload):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "routing-examples.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return load_routing_examples(path)


if __name__ == "__main__":
    unittest.main()
