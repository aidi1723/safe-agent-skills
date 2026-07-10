import unittest

from onecode_skill_sanitizer.compatibility import build_route_id
from onecode_skill_sanitizer.compatibility import to_legacy_v1


class CompatibilityTest(unittest.TestCase):
    def test_route_id_is_stable_across_key_order_and_ignores_dynamic_or_secret_fields(self):
        first = {
            "task": {"current": "build site", "history": "review brief"},
            "strategy": "balanced",
            "provider": {"mode": "none", "api_key": "secret-one"},
            "generated_at": "2026-07-10T00:00:00Z",
        }
        second = {
            "generated_at": "2027-01-01T00:00:00Z",
            "provider": {"api_key": "secret-two", "mode": "none"},
            "strategy": "balanced",
            "task": {"history": "review brief", "current": "build site"},
        }

        self.assertEqual(build_route_id(first), build_route_id(second))
        self.assertRegex(build_route_id(first), r"^sha256:[0-9a-f]{64}$")

    def test_route_id_changes_when_material_routing_input_changes(self):
        base = {"task": {"current": "build site"}, "strategy": "balanced"}
        changed = {"task": {"current": "audit router"}, "strategy": "balanced"}

        self.assertNotEqual(build_route_id(base), build_route_id(changed))

    def test_to_legacy_v1_records_multi_intent_scenario_and_cross_edge_loss(self):
        payload = {
            "schema_version": 2,
            "normalized_task": {"current": "build and audit"},
            "intent_graph": {
                "intents": [{"id": "i1"}, {"id": "i2"}],
                "unresolved_dependencies": [],
            },
            "selected_scenarios": [
                {"scenario_id": "lower", "intent_ids": ["i1"], "score": 0.4},
                {"scenario_id": "primary", "intent_ids": ["i2"], "score": 0.9},
            ],
            "execution_graph": {
                "nodes": [
                    {"id": "a", "scenario_ids": ["lower"]},
                    {"id": "b", "scenario_ids": ["primary"]},
                ],
                "edges": [{"from": "a", "to": "b", "type": "intent_completion_dependency"}],
            },
        }

        legacy = to_legacy_v1(payload)

        self.assertEqual(legacy["schema_version"], 1)
        self.assertEqual(legacy["selected_scenario"]["id"], "primary")
        self.assertEqual(
            legacy["compatibility_loss"],
            {
                "multi_intent_dropped": True,
                "scenarios_dropped": ["lower"],
                "cross_scenario_edges_dropped": 1,
            },
        )

    def test_to_legacy_v1_is_bounded_and_robust_for_empty_or_malformed_input(self):
        for payload in ({}, None, {"selected_scenarios": "bad", "intent_graph": []}):
            with self.subTest(payload=payload):
                legacy = to_legacy_v1(payload)
                self.assertEqual(legacy["schema_version"], 1)
                self.assertEqual(legacy["selected_scenario"], {})
                self.assertEqual(legacy["compatibility_loss"]["scenarios_dropped"], [])


if __name__ == "__main__":
    unittest.main()
