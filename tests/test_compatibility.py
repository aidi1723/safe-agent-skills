import json
import unittest

from onecode_skill_sanitizer.compatibility import build_route_id
from onecode_skill_sanitizer.compatibility import build_route_identity_payload
from onecode_skill_sanitizer.compatibility import to_legacy_v1
from onecode_skill_sanitizer.compatibility import v3_compatibility_report


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
            "sk-alpha1234567890beta1234567890",
            "sk-proj-alpha1234567890beta1234567890",
            "ghp_alpha1234567890beta1234567890",
            "gho_alpha1234567890beta1234567890",
            "ghu_alpha1234567890beta1234567890",
            "ghs_alpha1234567890beta1234567890",
            "ghr_alpha1234567890beta1234567890",
            "github_pat_alpha1234567890_beta1234567890",
            "AKIAABCDEFGHIJKLMNOP",
            "ASIAABCDEFGHIJKLMNOP",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature1234567",
            "https://user:first-password@example.com/deploy",
        ]
        replacement_variants = [
            "sk-gamma0987654321delta0987654321",
            "sk-proj-gamma0987654321delta0987654321",
            "ghp_gamma0987654321delta0987654321",
            "gho_gamma0987654321delta0987654321",
            "ghu_gamma0987654321delta0987654321",
            "ghs_gamma0987654321delta0987654321",
            "ghr_gamma0987654321delta0987654321",
            "github_pat_gamma0987654321_delta0987654321",
            "AKIAQRSTUVWXYZABCDEF",
            "ASIAQRSTUVWXYZABCDEF",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI5ODc2NTQzMjEwIn0.other_signature987",
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

    def test_route_identity_preserves_benign_token_like_material(self):
        benign_values = [
            "sk-telemetry-plugin",
            "abcdefgh.12345678.deadbeef",
            "AKIA-short-label",
            "ASIA-roadmap-note",
        ]
        for first_value in benign_values:
            second_value = f"changed-{first_value}"
            with self.subTest(value=first_value):
                first = build_route_identity_payload(
                    current=f"review {first_value}",
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
                second = dict(first)
                second["current"] = f"review {second_value}"
                self.assertIn(first_value, first["current"])
                self.assertNotEqual(build_route_id(first), build_route_id(second))

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

    def test_v3_compatibility_report_records_v2_and_v1_projection_losses(self):
        report = v3_compatibility_report(
            {
                "need_decision": {"decision": "composite"},
                "selection": {
                    "selected_skills": [
                        {"name": "code-review-risk"},
                        {"name": "code-test-regression"},
                    ]
                },
                "provider": {"used": "fake"},
                "confidence": {"level": "medium"},
                "execution_graph": {"edges": [{"type": "artifact_dependency"}]},
            }
        )

        self.assertFalse(report["v2"]["lossless"])
        self.assertIn("skill_level_selection", report["v2"]["losses"])
        self.assertIn("semantic_provider_evidence", report["v1"]["losses"])
        self.assertIn("confidence_and_abstention", report["v1"]["losses"])

    def test_v3_compatibility_report_is_bounded_deterministic_and_deduplicated(self):
        malformed_inputs = (
            {},
            None,
            {"selection": {"selected_skills": "bad"}, "provider": [], "need_decision": "bad"},
            {
                "selection": {
                    "selected_skills": [
                        {"name": "code-review-risk"},
                        {"name": "code-review-risk"},
                    ]
                },
                "provider": {"used": "fake"},
                "confidence": {},
            },
        )
        for payload in malformed_inputs:
            with self.subTest(payload=payload):
                first = v3_compatibility_report(payload)
                second = v3_compatibility_report(payload)
                self.assertEqual(first, second)
                for version in ("v2", "v1"):
                    losses = first[version]["losses"]
                    self.assertEqual(losses, sorted(set(losses)))


if __name__ == "__main__":
    unittest.main()
