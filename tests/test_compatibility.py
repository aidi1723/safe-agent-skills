import json
import unittest

from onecode_skill_sanitizer.compatibility import build_route_id
from onecode_skill_sanitizer.compatibility import build_route_identity_payload
from onecode_skill_sanitizer.compatibility import to_legacy_v1


class CompatibilityTest(unittest.TestCase):
    def test_route_id_is_stable_across_key_order_for_sanitized_allowlist(self):
        first = {"current": "build site", "history": "review brief", "strategy": "balanced"}
        second = {"strategy": "balanced", "history": "review brief", "current": "build site"}

        self.assertEqual(build_route_id(first), build_route_id(second))
        self.assertRegex(build_route_id(first), r"^sha256:[0-9a-f]{64}$")

    def test_route_identity_payload_excludes_raw_and_redacts_embedded_secret_values(self):
        first = build_route_identity_payload(
            current="build site api_key=alpha Bearer aaa.bbb 密钥: 中文秘密",
            history="audit auth: first-token and password=first-password",
            stale="session: first-session preserve stale context",
            stale_policy="ignore",
            invariants=["credential=first-credential keep compliance"],
            strategy="balanced",
            provider_identifier="none",
            catalog_content_hash="sha256:catalog",
            bundle_content_hash="sha256:bundle",
            overlap_content_hash="sha256:overlap",
            router_version="0.2.0",
            package_version="0.2.0",
        )
        second = build_route_identity_payload(
            current="build site api_key=beta Bearer ccc.ddd 密钥: 另一个秘密",
            history="audit auth: second-token and password=second-password",
            stale="session: second-session preserve stale context",
            stale_policy="ignore",
            invariants=["credential=second-credential keep compliance"],
            strategy="balanced",
            provider_identifier="none",
            catalog_content_hash="sha256:catalog",
            bundle_content_hash="sha256:bundle",
            overlap_content_hash="sha256:overlap",
            router_version="0.2.0",
            package_version="0.2.0",
        )

        serialized = json.dumps(first, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("raw", first)
        for secret in ["alpha", "aaa.bbb", "中文秘密", "first-token", "first-password", "first-session", "first-credential"]:
            self.assertNotIn(secret, serialized)
        self.assertIn("build site", serialized)
        self.assertIn("preserve stale context", serialized)
        self.assertEqual(build_route_id(first), build_route_id(second))

        changed = dict(first)
        changed["current"] = "audit router api_key=[REDACTED]"
        self.assertNotEqual(build_route_id(first), build_route_id(changed))

    def test_route_identity_redacts_bare_credentials_without_erasing_intent(self):
        secret_variants = [
            "sk-alpha1234567890",
            "sk-proj-alpha1234567890",
            "ghp_alpha1234567890",
            "github_pat_alpha1234567890",
            "AKIAABCDEFGHIJKLMNOP",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature",
            "https://user:first-password@example.com/deploy",
        ]
        replacement_variants = [
            "sk-beta0987654321",
            "sk-proj-beta0987654321",
            "ghp_beta0987654321",
            "github_pat_beta0987654321",
            "AKIAQRSTUVWXYZABCDEF",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI5ODc2NTQzMjEwIn0.other-signature",
            "https://user:second-password@example.com/deploy",
        ]

        for first_secret, second_secret in zip(secret_variants, replacement_variants):
            with self.subTest(secret=first_secret):
                first = build_route_identity_payload(
                    current=f"deploy release using {first_secret}",
                    history="",
                    stale="",
                    stale_policy="ignore",
                    invariants=[],
                    strategy="balanced",
                    provider_identifier="none",
                    catalog_content_hash="sha256:catalog",
                    bundle_content_hash="sha256:bundle",
                    overlap_content_hash="none",
                    router_version="v2",
                    package_version="v2",
                )
                second = build_route_identity_payload(
                    current=f"deploy release using {second_secret}",
                    history="",
                    stale="",
                    stale_policy="ignore",
                    invariants=[],
                    strategy="balanced",
                    provider_identifier="none",
                    catalog_content_hash="sha256:catalog",
                    bundle_content_hash="sha256:bundle",
                    overlap_content_hash="none",
                    router_version="v2",
                    package_version="v2",
                )
                self.assertEqual(build_route_id(first), build_route_id(second))
                self.assertNotIn(first_secret, json.dumps(first))

        ordinary = build_route_identity_payload(
            current="review responsive-layout and release-candidate notes",
            history="",
            stale="",
            stale_policy="ignore",
            invariants=[],
            strategy="balanced",
            provider_identifier="none",
            catalog_content_hash="sha256:catalog",
            bundle_content_hash="sha256:bundle",
            overlap_content_hash="none",
            router_version="v2",
            package_version="v2",
        )
        changed_host = dict(first)
        changed_host["current"] = "deploy release using https://user:[REDACTED]@other.example/deploy"
        self.assertIn("responsive-layout", ordinary["current"])
        self.assertNotEqual(build_route_id(first), build_route_id(changed_host))

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
