import copy
import dataclasses
import json
from pathlib import Path
from types import MappingProxyType
import unittest
from unittest.mock import patch

from onecode_skill_sanitizer.compiler import compile_execution_graph
from onecode_skill_sanitizer.composer import ScenarioComposition, ScenarioSelection
from onecode_skill_sanitizer.intent import Intent, IntentGraph, decompose_task
from onecode_skill_sanitizer.intent_dependencies import IntentRelation
from onecode_skill_sanitizer.intent_evidence import IntentEvidence


ROOT = Path(__file__).resolve().parents[1]
COMPOUND_TASK = "构建官网，同时审计 skill 路由器，验证通过后发布更新"


class CompilerTest(unittest.TestCase):
    def test_release_packet_readiness_compiles_at_single_and_multi_intent_boundaries(self):
        cases = (
            (
                "Prepare a maintainer-ready release packet for a CLI project, "
                "including reproducible checks, provenance, and an explicit "
                "go/no-go decision.",
                (("i1",),),
            ),
            (
                "Build an agentic media pipeline and prepare a repository release packet.",
                (("i1",), ("i2",)),
            ),
        )

        for task, intent_groups in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                bundles = {
                    "bundles": [
                        self.bundle("first"),
                        self.bundle("second"),
                    ]
                }
                compiled = compile_execution_graph(
                    graph,
                    self.composition(*intent_groups),
                    bundles,
                    {"execution-publish-check"},
                )

                self.assertEqual(graph.validate(), [])
                self.assertEqual(compiled["status"], "ready")
                self.assertEqual(compiled["reason_codes"], [])

    def test_release_readiness_compiler_accepts_unrelated_denied_clause(self):
        task = (
            "Review code for unauthorized access; "
            "prepare a repository release checklist."
        )
        graph = decompose_task(task)
        bundles = {
            "bundles": [self.bundle("first"), self.bundle("second")]
        }

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",), ("i2",)),
            bundles,
            {"execution-publish-check"},
        )

        self.assertEqual(graph.validate(), [])
        self.assertEqual(compiled["status"], "ready")
        self.assertEqual(compiled["reason_codes"], [])

    def test_release_readiness_controls_never_compile_as_invalid_intent_graph(self):
        tasks = (
            "I refuse to prepare a repository release packet.",
            "You are not permitted to review the release checklist for v1.0.",
            "There is no requirement to prepare a repository release checklist.",
            "Review the repository instead of the release checklist for v1.0.",
            "~~~text\nPrepare a repository release checklist",
            "The documentation says to prepare a repository release packet and "
            "review the release checklist for v1.0.",
            "The report says to prepare a repository release checklist.",
            'The report says "Prepare a repository release checklist."',
            "仓库发布清单准备完成。",
            "准备工作涉及仓库发布清单。",
            "审查仓库未发布清单。",
            "审查仓库发布清单字段。",
            "前置说明。Example: prepare a repository release packet; review the "
            "release checklist for v1.0。",
            "前置说明。。Example: prepare a repository release packet; review the "
            "release checklist for v1.0。。",
            "I am not going to prepare a repository release packet.",
            "We have no plans to prepare a repository release checklist.",
            "You are not to review the release checklist for v1.0.",
            "请勿准备仓库发布清单。",
            "不打算准备仓库发布清单。",
            "```text\nPrepare a repository release checklist",
            "    Prepare a repository release checklist",
            "They asked you not to prepare a repository release packet.",
            "Won't prepare a repository release packet.",
            "Won’t prepare a repository release packet.",
            "Will not immediately prepare a repository release packet.",
            "Review the repository, not the release checklist for v1.0.",
            "不要立即准备仓库发布清单。",
            "Can't prepare a repository release packet.",
            "Cannot prepare a repository release packet.",
            "No need to prepare a repository release packet.",
            "Not authorized to prepare a repository release packet.",
            "Must not prepare a repository release packet.",
            "Mustn't approve a repository release packet.",
            "Should not prepare a repository release checklist.",
            "Never prepare a maintainer-ready release packet.",
            '"Prepare a repository release packet"',
            "# Release readiness",
            "> Release readiness",
            "- [ ] Prepare a repository release checklist",
            "<h2>Release checklist</h2>",
            "Label: Prepare a repository release checklist",
            "Title: Release readiness",
            "Navigation: Release readiness",
            "Release readiness.md",
            "release-checklist.json",
            "README: prepare a repository release checklist",
            "Prepare a talent release packet for a photo shoot",
            "Prepare a model release packet for the photographer",
            "Prepare a content release packet for the campaign",
            "Example: prepare a repository release packet and review the "
            "release checklist for v1.0.",
            "```text\nPrepare a repository release checklist\n```",
            "[Prepare a repository release packet](docs/release.md)",
        )

        for task in tasks:
            with self.subTest(task=task):
                graph = decompose_task(task)
                intent_ids = tuple(intent.id for intent in graph.intents)
                compiled = compile_execution_graph(
                    graph,
                    self.composition(intent_ids),
                    {"bundles": [self.bundle("first")]},
                    {"execution-publish-check"},
                )

                self.assertEqual(graph.validate(), [])
                self.assertFalse(
                    any(
                        item.task_type == "open_source_release"
                        for item in graph.intent_evidence
                    )
                )
                self.assertNotIn(
                    "invalid_intent_graph", compiled["reason_codes"]
                )

    def test_release_precondition_compiles_without_cycle(self):
        graph = decompose_task("Before PR approval, publish update")
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("code-review-hardening", ("i1",), 1.0, 10),
                ScenarioSelection("open-source-release", ("i2",), 1.0, 10),
            ),
            uncovered_intents=(),
            status="complete",
        )

        compiled = compile_execution_graph(
            graph, composition, self.bundles_index, self.trusted_skill_names
        )

        self.assertEqual(compiled["status"], "ready")
        self.assertTrue(compiled["acyclic"])

    def test_standalone_bare_release_compiles_ready(self):
        graph = decompose_task("release")
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("open-source-release", ("i1",), 1.0, 10),
            ),
            uncovered_intents=(),
            status="complete",
        )

        compiled = compile_execution_graph(
            graph, composition, self.bundles_index, self.trusted_skill_names
        )

        self.assertEqual(compiled["status"], "ready")
        self.assertTrue(compiled["acyclic"])

    def test_approval_release_compiles_ready_with_verification_anchor(self):
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("code-review-hardening", ("i1",), 1.0, 10),
                ScenarioSelection("open-source-release", ("i2",), 1.0, 10),
            ),
            uncovered_intents=(),
            status="complete",
        )

        for task in (
            "在 PR 审批通过后发布",
            "After the PR is approved, release",
        ):
            with self.subTest(task=task):
                graph = decompose_task(task)
                compiled = compile_execution_graph(
                    graph,
                    composition,
                    self.bundles_index,
                    self.trusted_skill_names,
                )

                self.assertEqual(compiled["status"], "ready")
                self.assertTrue(compiled["acyclic"])

    def test_canonical_summary_forgery_blocks_compilation(self):
        graph = decompose_task(
            "After completing code review, build a website"
        )
        graph = dataclasses.replace(
            graph,
            intents=(
                dataclasses.replace(
                    graph.intents[0], summary="After verifying code review"
                ),
                graph.intents[1],
            ),
        )

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",), ("i2",)),
            {"bundles": [self.bundle("first"), self.bundle("second")]},
            {"execution-publish-check"},
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])

    def test_malformed_internal_intent_evidence_blocks_compilation(self):
        valid = IntentEvidence(
            "code_review", "action", "positive", "none", "single", (), 2
        )
        graph = IntentGraph(
            (self.intent("i1"),),
            (),
            intent_evidence=(dataclasses.replace(valid, context="bad"),),
        )

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",)),
            {"bundles": [self.bundle("first")]},
            {"execution-publish-check"},
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])

    def test_semantically_forged_readiness_evidence_blocks_compilation(self):
        graph = IntentGraph(
            (
                self.intent("i1"),
                self.intent(
                    "i2",
                    depends_on=("i1",),
                    task_type="open_source_release",
                    summary="publish update",
                ),
            ),
            (),
            dependency_relations=(
                IntentRelation("i1", "i2", "release_gate", True),
            ),
            intent_evidence=(
                IntentEvidence(
                    "code_review", "action", "positive", "none", "enumeration", (), 2
                ),
                IntentEvidence(
                    "open_source_release",
                    "action",
                    "positive",
                    "readiness",
                    "enumeration",
                    ("release checklist",),
                    4,
                ),
            ),
        )

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",), ("i2",)),
            {
                "bundles": [
                    self.bundle("first"),
                    self.bundle("second"),
                ]
            },
            {"execution-publish-check"},
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])

    @classmethod
    def setUpClass(cls):
        cls.bundles_index = json.loads(
            (ROOT / "bundles" / "index.json").read_text(encoding="utf-8")
        )
        catalog_index = json.loads(
            (ROOT / "catalog" / "index.json").read_text(encoding="utf-8")
        )
        cls.trusted_skill_names = {
            skill["name"]
            for skill in catalog_index["skills"]
            if skill.get("status") == "trusted"
        }

    def test_compiles_valid_compound_dag_with_release_dependencies_from_both_paths(self):
        graph = decompose_task(COMPOUND_TASK)
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("website-build-launch", ("i1",), 1.0, 10),
                ScenarioSelection("skill-router-quality-review", ("i2",), 1.0, 10),
                ScenarioSelection("open-source-release", ("i3",), 1.0, 10),
            ),
            uncovered_intents=(),
            status="complete",
        )

        compiled = compile_execution_graph(
            graph, composition, self.bundles_index, self.trusted_skill_names
        )

        self.assertEqual(compiled["schema_version"], 2)
        self.assertEqual(compiled["status"], "ready")
        self.assertTrue(compiled["acyclic"])
        self.assertEqual(compiled["reason_codes"], [])
        release_root = self.root_node(compiled, "i3")
        incoming_verification = {
            edge["from"]
            for edge in compiled["edges"]
            if edge["to"] == release_root
            and edge["type"] == "intent_verification_dependency"
        }
        self.assertEqual(
            incoming_verification,
            {
                self.terminal_verification_node(compiled, "i1"),
                self.terminal_verification_node(compiled, "i2"),
            },
        )
        incoming_nodes = {
            node["id"]: node
            for node in compiled["nodes"]
            if node["id"] in incoming_verification
        }
        self.assertEqual(
            {node["stage"] for node in incoming_nodes.values()}, {"verification"}
        )
        incoming_completion = {
            edge["from"]
            for edge in compiled["edges"]
            if edge["to"] == release_root
            and edge["type"] == "intent_completion_dependency"
        }
        self.assertEqual(
            incoming_completion,
            {self.terminal_node(compiled, "i1"), self.terminal_node(compiled, "i2")},
        )
        node = compiled["nodes"][0]
        self.assertEqual(
            set(node),
            {"id", "intent_ids", "scenario_ids", "skill", "stage", "host_action"},
        )
        self.assertEqual(node["host_action"], node["skill"].startswith("execution-"))

    def test_constructed_cyclic_intent_graph_is_blocked_without_fallback(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1", depends_on=("i2",)),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=(),
        )
        composition = self.composition(("i1",), ("i2",))
        bundles = {"bundles": [self.bundle("first"), self.bundle("second")]}

        compiled = compile_execution_graph(
            graph, composition, bundles, {"execution-publish-check"}
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertFalse(compiled["acyclic"])
        self.assertEqual(
            compiled["reason_codes"], ["dependency_cycle", "invalid_intent_graph"]
        )
        self.assertEqual(
            compiled["details"],
            ["intent dependency cycle detected: i1 -> i2 -> i1"],
        )
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])
        self.assertNotIn("fallback_reason", compiled)

    def test_node_and_edge_ordering_is_deterministic_for_reordered_inputs(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=(),
        )
        composition = ScenarioComposition(
            selections=(
                ScenarioSelection("second", ("i2",), 1.0, 1),
                ScenarioSelection("first", ("i1",), 1.0, 1),
            ),
            uncovered_intents=(),
            status="complete",
        )
        bundles = {
            "bundles": [
                self.bundle("second", ["skill-c", "execution-browser-check", "skill-d"]),
                self.bundle("first", ["skill-a", "execution-publish-check", "skill-b"]),
            ]
        }
        before = copy.deepcopy(bundles)

        first = compile_execution_graph(graph, composition, bundles, self.skill_names(bundles))
        second = compile_execution_graph(
            graph,
            ScenarioComposition(
                selections=tuple(reversed(composition.selections)),
                uncovered_intents=(),
                status="complete",
            ),
            {"bundles": list(reversed(bundles["bundles"]))},
            self.skill_names(bundles),
        )

        self.assertEqual(first, second)
        self.assertEqual(
            [node["id"] for node in first["nodes"]],
            [
                "skill:i1:skill-a",
                "skill:i1:execution-publish-check",
                "skill:i1:skill-b",
                "skill:i2:skill-c",
                "skill:i2:execution-browser-check",
                "skill:i2:skill-d",
            ],
        )
        self.assertEqual(bundles, before)

    def test_missing_scenario_bundle_is_blocked_with_reason_code(self):
        graph = IntentGraph((self.intent("i1"),), ())
        composition = self.composition(("i1",))

        compiled = compile_execution_graph(graph, composition, {"bundles": []}, set())

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["missing_scenario_bundle"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])

    def test_empty_execution_order_is_blocked_with_reason_code(self):
        graph = IntentGraph((self.intent("i1"),), ())
        composition = self.composition(("i1",))
        bundles = {"bundles": [self.bundle("first", [])]}

        compiled = compile_execution_graph(graph, composition, bundles, set())

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["empty_execution_order"])

    def test_duplicate_dependencies_do_not_create_duplicate_edges(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i2", depends_on=("i1", "i1")),
            ),
            unresolved_dependencies=(),
        )
        composition = self.composition(("i1",), ("i2",))
        bundles = {"bundles": [self.bundle("first"), self.bundle("second")]}

        compiled = compile_execution_graph(
            graph, composition, bundles, {"execution-publish-check"}
        )

        edge_keys = [(edge["from"], edge["to"], edge["type"]) for edge in compiled["edges"]]
        self.assertEqual(len(edge_keys), len(set(edge_keys)))

    def test_forged_composition_cannot_select_untrusted_bundle_or_skill(self):
        graph = IntentGraph((self.intent("i1"),), ())
        composition = self.composition(("i1",))
        quarantined = {"bundles": [{**self.bundle("first"), "status": "quarantined"}]}

        untrusted_bundle = compile_execution_graph(
            graph, composition, quarantined, {"execution-publish-check"}
        )
        untrusted_skill = compile_execution_graph(
            graph,
            composition,
            {"bundles": [self.bundle("first")]},
            set(),
        )

        self.assertEqual(untrusted_bundle["reason_codes"], ["untrusted_scenario"])
        self.assertEqual(untrusted_skill["reason_codes"], ["untrusted_scenario"])
        self.assertEqual(untrusted_bundle["status"], "blocked")
        self.assertEqual(untrusted_skill["status"], "blocked")

    def test_incomplete_unknown_duplicate_and_malformed_inputs_return_reason_codes(self):
        graph = IntentGraph((self.intent("i1"),), ())
        incomplete = ScenarioComposition((), ("i1",), "incomplete")
        unknown = ScenarioComposition(
            (ScenarioSelection("first", ("i9",), 1.0, 1),), (), "complete"
        )
        duplicate_bundle = {
            "bundles": [
                self.bundle(
                    "first", ["execution-publish-check", "execution-publish-check"]
                )
            ]
        }
        malformed_graph = IntentGraph((self.intent("i1", depends_on=None),), ())

        cases = [
            (
                compile_execution_graph(graph, incomplete, {"bundles": []}, set()),
                "incomplete_composition",
            ),
            (
                compile_execution_graph(
                    graph,
                    unknown,
                    {"bundles": [self.bundle("first")]},
                    {"execution-publish-check"},
                ),
                "unknown_intent_id",
            ),
            (
                compile_execution_graph(
                    graph,
                    self.composition(("i1",)),
                    duplicate_bundle,
                    {"execution-publish-check"},
                ),
                "duplicate_skill_name",
            ),
            (
                compile_execution_graph(
                    malformed_graph,
                    self.composition(("i1",)),
                    {"bundles": [self.bundle("first")]},
                    {"execution-publish-check"},
                ),
                "malformed_intent_dependency",
            ),
        ]

        for compiled, reason_code in cases:
            with self.subTest(reason_code=reason_code):
                self.assertEqual(compiled["status"], "blocked")
                self.assertIn(reason_code, compiled["reason_codes"])

    def test_ordinary_dependency_without_verification_uses_completion_anchor(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=(),
        )
        composition = self.composition(("i1",), ("i2",))
        bundles = {
            "bundles": [
                self.bundle("first", ["skill-a"]),
                self.bundle("second", ["execution-publish-check"]),
            ]
        }

        compiled = compile_execution_graph(
            graph, composition, bundles, {"skill-a", "execution-publish-check"}
        )

        self.assertEqual(compiled["status"], "ready")
        self.assertEqual(compiled["reason_codes"], [])
        self.assertIn(
            {
                "from": "skill:i1:skill-a",
                "to": "skill:i2:execution-publish-check",
                "type": "intent_completion_dependency",
            },
            compiled["edges"],
        )

    def test_release_dependency_without_verification_anchor_is_blocked(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent(
                    "i2", depends_on=("i1",), task_type="open_source_release"
                ),
            ),
            unresolved_dependencies=(),
        )
        bundles = {
            "bundles": [
                self.bundle("first", ["skill-a"]),
                self.bundle("second", ["execution-publish-check"]),
            ]
        }

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",), ("i2",)),
            bundles,
            {"skill-a", "execution-publish-check"},
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["missing_intent_verification"])

    def test_trusted_contract_stage_map_supplies_release_verification_anchor(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent(
                    "i2", depends_on=("i1",), task_type="open_source_release"
                ),
            ),
            unresolved_dependencies=(),
        )
        bundles = {
            "bundles": [
                self.bundle("first", ["research-source-check"]),
                self.bundle("second", ["execution-publish-check"]),
            ]
        }
        trusted = {"research-source-check", "execution-publish-check"}

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",), ("i2",)),
            bundles,
            trusted,
            stage_by_skill={
                "research-source-check": "verification",
                "execution-publish-check": "verification",
            },
        )

        self.assertEqual(compiled["status"], "ready")
        self.assertTrue(compiled["acyclic"])
        self.assertEqual(compiled["reason_codes"], [])
        self.assertIn(
            {
                "from": "skill:i1:research-source-check",
                "to": "skill:i2:execution-publish-check",
                "type": "intent_verification_dependency",
            },
            compiled["edges"],
        )
        self.assertEqual(compiled["nodes"][0]["stage"], "verification")

    def test_contract_stage_map_boundary_rejects_malformed_or_untrusted_entries(self):
        graph = IntentGraph((self.intent("i1"),), ())
        bundles = {"bundles": [self.bundle("first", ["research-source-check"])]}
        trusted = {"research-source-check"}
        cases = [
            True,
            [],
            {},
            {"research-source-check": True},
            {"research-source-check": "unknown-stage"},
            {"untrusted-source-check": "verification"},
            {"": "verification"},
        ]

        for stage_by_skill in cases:
            with self.subTest(stage_by_skill=stage_by_skill):
                compiled = compile_execution_graph(
                    graph,
                    self.composition(("i1",)),
                    bundles,
                    trusted,
                    stage_by_skill=stage_by_skill,
                )

                self.assertEqual(compiled["status"], "blocked")
                self.assertEqual(compiled["reason_codes"], ["invalid_stage_map"])
                self.assertEqual(compiled["nodes"], [])
                self.assertEqual(compiled["edges"], [])

    def test_explicit_empty_stage_map_is_invalid_even_without_trusted_skills(self):
        graph = IntentGraph((self.intent("i1"),), ())
        composition = self.composition(("i1",))

        for stage_by_skill in ({}, MappingProxyType({})):
            with self.subTest(stage_by_skill=stage_by_skill):
                compiled = compile_execution_graph(
                    graph,
                    composition,
                    {"bundles": []},
                    set(),
                    stage_by_skill=stage_by_skill,
                )
                self.assertEqual(compiled["reason_codes"], ["invalid_stage_map"])
                self.assertEqual(compiled["nodes"], [])
                self.assertEqual(compiled["edges"], [])

        legacy = compile_execution_graph(
            graph,
            composition,
            {"bundles": []},
            set(),
            stage_by_skill=None,
        )
        self.assertEqual(legacy["reason_codes"], ["missing_scenario_bundle"])
        self.assertNotIn("invalid_stage_map", legacy["reason_codes"])

    def test_release_target_rejects_false_internal_verification_metadata(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent(
                    "i2", depends_on=("i1",), task_type="open_source_release"
                ),
            ),
            unresolved_dependencies=(),
            dependency_relations=(
                IntentRelation("i1", "i2", "release_gate", False),
            ),
        )
        bundles = {
            "bundles": [
                self.bundle("first", ["skill-a"]),
                self.bundle("second", ["execution-publish-check"]),
            ]
        }

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",), ("i2",)),
            bundles,
            {"skill-a", "execution-publish-check"},
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])

    def test_semantically_inconsistent_relation_metadata_is_invalid(self):
        cases = [
            IntentRelation("i1", "i2", "verification_gate", False),
            IntentRelation("i1", "i2", "completion_gate", True),
            IntentRelation("i1", "i2", "explicit_sequence", True),
            IntentRelation("i1", "i2", "semicolon_workflow", True),
        ]
        bundles = {
            "bundles": [
                self.bundle("first", ["skill-a"]),
                self.bundle("second", ["execution-publish-check"]),
            ]
        }

        for relation in cases:
            with self.subTest(relation=relation):
                graph = IntentGraph(
                    intents=(
                        self.intent("i1"),
                        self.intent("i2", depends_on=("i1",)),
                    ),
                    unresolved_dependencies=(),
                    dependency_relations=(relation,),
                )

                compiled = compile_execution_graph(
                    graph,
                    self.composition(("i1",), ("i2",)),
                    bundles,
                    {"skill-a", "execution-publish-check"},
                )

                self.assertEqual(compiled["status"], "blocked")
                self.assertEqual(
                    compiled["reason_codes"], ["invalid_intent_graph"]
                )
                self.assertEqual(compiled["nodes"], [])
                self.assertEqual(compiled["edges"], [])

    def test_manual_graph_without_metadata_does_not_reparse_gate_summary(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent(
                    "i2",
                    depends_on=("i1",),
                    summary="After verification is complete, review the result",
                ),
            ),
            unresolved_dependencies=(),
        )
        bundles = {
            "bundles": [
                self.bundle("first", ["skill-a"]),
                self.bundle("second", ["execution-publish-check"]),
            ]
        }

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",), ("i2",)),
            bundles,
            {"skill-a", "execution-publish-check"},
        )

        self.assertEqual(compiled["status"], "ready")
        self.assertEqual(compiled["reason_codes"], [])

    def test_source_side_verification_gate_without_anchor_is_blocked(self):
        bundles = {
            "bundles": [
                self.bundle("first", ["skill-a"]),
                self.bundle("second", ["execution-publish-check"]),
            ]
        }

        for task in [
            "Once the PR is verified, build the website",
            "PR 验证通过后，构建官网",
            "After the PR is approved, build the website",
            "PR 审批通过后，构建官网",
        ]:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.task_type for intent in graph.intents],
                    ["code_review", "website_build"],
                )
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents],
                    [(), ("i1",)],
                )

                compiled = compile_execution_graph(
                    graph,
                    self.composition(("i1",), ("i2",)),
                    bundles,
                    {"skill-a", "execution-publish-check"},
                )

                self.assertEqual(compiled["status"], "blocked")
                self.assertEqual(
                    compiled["reason_codes"], ["missing_intent_verification"]
                )

    def test_semicolon_and_target_first_verification_metadata_block_without_anchor(self):
        bundles = {
            "bundles": [
                self.bundle("first", ["skill-a"]),
                self.bundle("second", ["execution-publish-check"]),
            ]
        }
        cases = [
            ("After verifying the PR; build the website", ("i1",), ("i2",)),
            ("PR 验证通过后；构建官网", ("i1",), ("i2",)),
            ("Build the website after verification of the PR", ("i2",), ("i1",)),
            ("Build the website after approval of the PR", ("i2",), ("i1",)),
            ("Build the website after the PR is approved", ("i2",), ("i1",)),
            ("构建官网在 PR 审批通过后", ("i2",), ("i1",)),
            ("构建官网在PR审批通过后", ("i2",), ("i1",)),
            ("构建官网在拉取请求审批通过后", ("i2",), ("i1",)),
        ]

        for task, source_ids, target_ids in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(len(graph.intents), 2)
                self.assertTrue(graph.dependency_relations[0].requires_verification)

                compiled = compile_execution_graph(
                    graph,
                    self.composition(source_ids, target_ids),
                    bundles,
                    {"skill-a", "execution-publish-check"},
                )

                self.assertEqual(compiled["status"], "blocked")
                self.assertEqual(
                    compiled["reason_codes"], ["missing_intent_verification"]
                )

    def test_source_side_completion_gate_without_anchor_uses_completion_edge(self):
        bundles = {
            "bundles": [
                self.bundle("first", ["skill-a"]),
                self.bundle("second", ["execution-publish-check"]),
            ]
        }

        for task in [
            "After completing the PR review, build the website",
            "PR 审查完成后，构建官网",
        ]:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.task_type for intent in graph.intents],
                    ["code_review", "website_build"],
                )
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents],
                    [(), ("i1",)],
                )

                compiled = compile_execution_graph(
                    graph,
                    self.composition(("i1",), ("i2",)),
                    bundles,
                    {"skill-a", "execution-publish-check"},
                )

                self.assertEqual(compiled["status"], "ready")
                self.assertEqual(compiled["reason_codes"], [])
                self.assertIn(
                    {
                        "from": "skill:i1:skill-a",
                        "to": "skill:i2:execution-publish-check",
                        "type": "intent_completion_dependency",
                    },
                    compiled["edges"],
                )
                self.assertNotIn(
                    "intent_verification_dependency",
                    {edge["type"] for edge in compiled["edges"]},
                )

    def test_verification_followed_by_review_adds_evidence_and_completion_edges(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=(),
        )
        bundles = {
            "bundles": [
                self.bundle(
                    "first",
                    ["execution-publish-check", "content-editorial-review"],
                ),
                self.bundle("second", ["execution-browser-check"]),
            ]
        }

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",), ("i2",)),
            bundles,
            self.skill_names(bundles),
        )

        dependent_root = self.root_node(compiled, "i2")
        incoming = {
            (edge["from"], edge["type"])
            for edge in compiled["edges"]
            if edge["to"] == dependent_root
        }
        self.assertEqual(
            incoming,
            {
                (
                    "skill:i1:execution-publish-check",
                    "intent_verification_dependency",
                ),
                (
                    "skill:i1:content-editorial-review",
                    "intent_completion_dependency",
                ),
            },
        )

    def test_boundary_invalid_graph_returns_empty_nodes_and_edges(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=("unresolved release",),
        )
        bundles = {
            "bundles": [
                self.bundle("first"),
                self.bundle("second"),
            ]
        }

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",), ("i2",)),
            bundles,
            self.skill_names(bundles),
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
        self.assertEqual(compiled["nodes"], [])
        self.assertEqual(compiled["edges"], [])

    def test_malformed_dependency_relation_metadata_is_blocked_without_raising(self):
        base_relation = IntentRelation("i1", "i2", "before", False)
        for relations in [None, "bad", [base_relation], (object(),)]:
            with self.subTest(relations=relations):
                graph = IntentGraph(
                    intents=(
                        self.intent("i1"),
                        self.intent("i2", depends_on=("i1",)),
                    ),
                    unresolved_dependencies=(),
                    dependency_relations=relations,
                )

                compiled = compile_execution_graph(
                    graph,
                    self.composition(("i1",), ("i2",)),
                    {
                        "bundles": [
                            self.bundle("first", ["skill-a"]),
                            self.bundle("second", ["execution-publish-check"]),
                        ]
                    },
                    {"skill-a", "execution-publish-check"},
                )

                self.assertEqual(compiled["status"], "blocked")
                self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
                self.assertEqual(compiled["nodes"], [])
                self.assertEqual(compiled["edges"], [])

    def test_malformed_validate_return_fails_closed(self):
        graph = IntentGraph((self.intent("i1"),), ())

        for malformed in [
            None,
            "issue",
            ["valid", 3],
            [""],
            [" "],
            ("valid", None),
        ]:
            with self.subTest(malformed=malformed):
                with patch.object(IntentGraph, "validate", return_value=malformed):
                    compiled = compile_execution_graph(
                        graph,
                        self.composition(("i1",)),
                        {"bundles": [self.bundle("first")]},
                        {"execution-publish-check"},
                    )

                self.assertEqual(compiled["status"], "blocked")
                self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
                self.assertEqual(compiled["nodes"], [])
                self.assertEqual(compiled["edges"], [])
                self.assertIn("malformed intent graph validation result", compiled["details"])

    def test_malformed_unresolved_dependencies_fail_closed(self):
        graph = IntentGraph((self.intent("i1"),), ())

        for malformed in [None, "issue", ("valid", 3), ("",), (" ",)]:
            with self.subTest(malformed=malformed):
                object.__setattr__(graph, "unresolved_dependencies", malformed)
                compiled = compile_execution_graph(
                    graph,
                    self.composition(("i1",)),
                    {"bundles": [self.bundle("first")]},
                    {"execution-publish-check"},
                )

                self.assertEqual(compiled["status"], "blocked")
                self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
                self.assertEqual(compiled["nodes"], [])
                self.assertEqual(compiled["edges"], [])
                self.assertIn(
                    "unresolved_dependencies must be a list or tuple of nonempty strings",
                    compiled["details"],
                )

    def test_intent_graph_validation_issues_and_unresolved_dependencies_block(self):
        graph = IntentGraph(
            intents=(self.intent("i1"),),
            unresolved_dependencies=("release target unresolved", "artifact unresolved"),
        )

        compiled = compile_execution_graph(
            graph,
            self.composition(("i1",)),
            {"bundles": [self.bundle("first")]},
            {"execution-publish-check"},
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
        self.assertEqual(
            compiled["details"],
            [
                "unresolved dependency: artifact unresolved",
                "unresolved dependency: release target unresolved",
            ],
        )

    def test_compiler_boundary_rejects_invalid_intent_id_pattern(self):
        graph = IntentGraph((self.intent("intent-1"),), ())
        composition = ScenarioComposition(
            (ScenarioSelection("first", ("intent-1",), 1.0, 1),), (), "complete"
        )

        compiled = compile_execution_graph(
            graph,
            composition,
            {"bundles": [self.bundle("first")]},
            {"execution-publish-check"},
        )

        self.assertEqual(compiled["status"], "blocked")
        self.assertEqual(compiled["reason_codes"], ["invalid_intent_graph"])
        self.assertEqual(compiled["details"], ["invalid intent id: intent-1"])

    def test_reason_codes_and_details_are_sorted_independent_of_selection_order(self):
        graph = IntentGraph(
            intents=(self.intent("i1"), self.intent("i2")),
            unresolved_dependencies=(),
        )
        selections = (
            ScenarioSelection("missing-z", ("i2",), 1.0, 1),
            ScenarioSelection("", ("i1",), 1.0, 1),
        )

        first = compile_execution_graph(
            graph,
            ScenarioComposition(selections, (), "complete"),
            {"bundles": []},
            set(),
        )
        second = compile_execution_graph(
            graph,
            ScenarioComposition(tuple(reversed(selections)), (), "complete"),
            {"bundles": []},
            set(),
        )

        self.assertEqual(first, second)
        self.assertEqual(
            first["reason_codes"],
            ["malformed_scenario_id", "missing_scenario_bundle"],
        )
        self.assertNotIn("details", first)

    @staticmethod
    def intent(intent_id, depends_on=(), task_type="code_review", summary="test intent"):
        return Intent(
            id=intent_id,
            summary=summary,
            task_type=task_type,
            required_artifacts=(),
            risk_flags=(),
            depends_on=depends_on,
            source="deterministic",
            confidence=1.0,
        )

    @staticmethod
    def bundle(bundle_id, execution_order=None):
        order = ["execution-publish-check"] if execution_order is None else execution_order
        return {
            "id": bundle_id,
            "name": bundle_id,
            "scenario": bundle_id,
            "status": "trusted",
            "task_signals": [],
            "required_capabilities": [],
            "execution_order": order,
            "skills": list(dict.fromkeys(order)),
            "expected_output": [],
            "safety_boundary": "method only",
        }

    @staticmethod
    def composition(*intent_ids):
        selections = tuple(
            ScenarioSelection(
                "first" if index == 0 else "second", ids, 1.0, 1
            )
            for index, ids in enumerate(intent_ids)
        )
        return ScenarioComposition(selections, (), "complete")

    @staticmethod
    def skill_names(bundles):
        return {
            skill_name
            for bundle in bundles["bundles"]
            for skill_name in bundle["execution_order"]
        }

    @staticmethod
    def root_node(compiled, intent_id):
        return next(
            node["id"] for node in compiled["nodes"] if node["intent_ids"] == [intent_id]
        )

    @staticmethod
    def terminal_node(compiled, intent_id):
        node_ids = [
            node["id"] for node in compiled["nodes"] if node["intent_ids"] == [intent_id]
        ]
        return next(
            node_id
            for node_id in reversed(node_ids)
            if not any(
                edge["from"] == node_id and edge["type"] == "scenario_order"
                for edge in compiled["edges"]
            )
        )

    @staticmethod
    def terminal_verification_node(compiled, intent_id):
        verification_ids = [
            node["id"]
            for node in compiled["nodes"]
            if node["intent_ids"] == [intent_id] and node["stage"] == "verification"
        ]
        return next(
            node_id
            for node_id in reversed(verification_ids)
            if not any(
                edge["from"] == node_id
                and edge["to"] in verification_ids
                and edge["type"] == "scenario_order"
                for edge in compiled["edges"]
            )
        )


if __name__ == "__main__":
    unittest.main()
