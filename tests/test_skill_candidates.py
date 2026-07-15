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


class SkillCandidateTest(unittest.TestCase):
    def test_runtime_examples_are_reviewed_and_limited_to_the_fixed_cohort(self):
        examples = load_routing_examples(EXAMPLES)
        classes = Counter(example["example_class"] for example in examples)

        self.assertEqual(HIGH_FREQUENCY_ENTRY_NAMES[0], "safe-agent-router")
        self.assertEqual(len(HIGH_FREQUENCY_ENTRY_NAMES), 8)
        self.assertEqual(len(HIGH_FREQUENCY_SKILL_NAMES), 7)
        self.assertGreaterEqual(len(examples), 35)
        self.assertGreaterEqual(classes["positive"], 21)
        self.assertGreaterEqual(classes["near_miss"], 7)
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


if __name__ == "__main__":
    unittest.main()
