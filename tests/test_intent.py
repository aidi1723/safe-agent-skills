import dataclasses
import json
from pathlib import Path
import unittest

from onecode_skill_sanitizer.intent import (
    Intent,
    IntentGraph,
    IntentRelation,
    TaskDecomposition,
    decompose_task,
    normalize_task,
    split_task_clauses,
)
from onecode_skill_sanitizer.intent_evidence import (
    IntentEvidence,
    bind_intent_evidence,
)
from onecode_skill_sanitizer.intent_dependencies import infer_intent_relations


class IntentTest(unittest.TestCase):
    def test_internal_intent_evidence_is_frozen_validated_and_nonserialized(self):
        graph = decompose_task("代码审查 + 老板简报 + 发布清单")

        self.assertEqual(graph.validate(), [])
        self.assertTrue(graph.intent_evidence)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            graph.intent_evidence[0].task_type = "general"
        self.assertNotIn("intent_evidence", graph.to_json())
        self.assertEqual(
            IntentGraph((self.intent("i1"),), ()).validate(),
            [],
        )

    def test_internal_intent_evidence_rejects_malformed_records(self):
        intent = self.intent("i1")
        valid = IntentEvidence(
            "general", "action", "positive", "none", "single", (), 0
        )
        malformed_cases = [
            (None, "intent evidence must be a tuple"),
            ([valid], "intent evidence must be a tuple"),
            ((object(),), "must be an IntentEvidence"),
            (
                (dataclasses.replace(valid, task_type="code_review"),),
                "task type does not match intent",
            ),
            ((dataclasses.replace(valid, context="bad"),), "invalid context"),
            ((dataclasses.replace(valid, polarity="bad"),), "invalid polarity"),
            ((dataclasses.replace(valid, release_mode="bad"),), "invalid release mode"),
            ((dataclasses.replace(valid, relation_mode="bad"),), "invalid relation mode"),
            ((dataclasses.replace(valid, matched_signals=[]),), "invalid matched signals"),
            ((dataclasses.replace(valid, matched_score=True),), "invalid matched score"),
        ]

        for evidence, expected in malformed_cases:
            with self.subTest(expected=expected):
                graph = IntentGraph((intent,), (), intent_evidence=evidence)
                self.assertTrue(
                    any(expected in error for error in graph.validate()),
                    graph.validate(),
                )

    def test_internal_intent_evidence_enforces_release_semantics(self):
        cases = [
            (
                self.intent("i1"),
                IntentEvidence(
                    "general", "action", "positive", "action", "single", (), 0
                ),
                "non-release intent cannot carry release mode",
            ),
            (
                dataclasses.replace(self.intent("i1"), task_type="code_review"),
                IntentEvidence(
                    "code_review",
                    "action",
                    "positive",
                    "readiness",
                    "single",
                    ("release checklist",),
                    2,
                ),
                "non-release intent cannot carry release mode",
            ),
            (
                dataclasses.replace(
                    self.intent("i1"),
                    task_type="open_source_release",
                    summary="publish update",
                ),
                IntentEvidence(
                    "open_source_release",
                    "action",
                    "positive",
                    "none",
                    "single",
                    ("publish update",),
                    4,
                ),
                "release intent must declare release mode",
            ),
            (
                dataclasses.replace(
                    self.intent("i1"),
                    task_type="open_source_release",
                    summary="publish update",
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
                "readiness evidence is not supported by source",
            ),
            (
                dataclasses.replace(
                    self.intent("i1"),
                    task_type="open_source_release",
                    summary="prepare a checklist",
                ),
                IntentEvidence(
                    "open_source_release",
                    "action",
                    "positive",
                    "readiness",
                    "enumeration",
                    ("checklist",),
                    2,
                ),
                "readiness evidence is not supported by source",
            ),
            (
                dataclasses.replace(
                    self.intent("i1"),
                    task_type="open_source_release",
                    summary="release checklist",
                ),
                IntentEvidence(
                    "open_source_release",
                    "descriptive",
                    "positive",
                    "action",
                    "single",
                    ("release checklist",),
                    2,
                ),
                "release action evidence requires action context",
            ),
            (
                dataclasses.replace(
                    self.intent("i1"),
                    task_type="open_source_release",
                    summary="unrelated source",
                ),
                IntentEvidence(
                    "open_source_release",
                    "action",
                    "positive",
                    "action",
                    "single",
                    ("publish update",),
                    4,
                ),
                "release action evidence requires action context",
            ),
            (
                dataclasses.replace(
                    self.intent("i1"),
                    task_type="open_source_release",
                    summary="release checklist",
                ),
                IntentEvidence(
                    "open_source_release",
                    "action",
                    "negative",
                    "readiness",
                    "single",
                    ("release checklist",),
                    4,
                ),
                "readiness evidence requires positive context",
            ),
        ]

        for intent, evidence, expected in cases:
            with self.subTest(expected=expected):
                graph = IntentGraph((intent,), (), intent_evidence=(evidence,))
                self.assertTrue(
                    any(expected in error for error in graph.validate()),
                    graph.validate(),
                )

    def test_suppressed_general_evidence_has_canonical_empty_payload(self):
        generated = decompose_task(
            "The description mentions code review + executive brief + release checklist"
        )
        evidence = generated.intent_evidence[0]

        self.assertEqual(evidence.task_type, "general")
        self.assertEqual(evidence.context, "descriptive")
        self.assertEqual(evidence.release_mode, "none")
        self.assertEqual(evidence.matched_signals, ())
        self.assertEqual(evidence.matched_score, 0)
        self.assertEqual(generated.validate(), [])

        malformed = dataclasses.replace(evidence, matched_signals=("code review",))
        graph = IntentGraph(
            (self.intent("i1"),), (), intent_evidence=(malformed,)
        )
        self.assertTrue(
            any(
                "suppressed general evidence must have empty matches" in error
                for error in graph.validate()
            ),
            graph.validate(),
        )

    def test_intent_evidence_validation_is_total_for_arbitrary_field_types(self):
        intent = self.intent("i1")
        valid = IntentEvidence(
            "general", "action", "positive", "none", "single", (), 0
        )
        mutations = {
            "task_type": [None, [], {}],
            "context": [None, [], {}],
            "polarity": [None, [], {}],
            "release_mode": [None, [], {}],
            "relation_mode": [None, [], {}],
            "gate_mode": [None, [], {}],
            "matched_signals": [None, [], (1,), ("ok", None)],
            "matched_score": [True, "2", float("nan"), float("inf"), -1, 513],
        }

        for field, values in mutations.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    evidence = dataclasses.replace(valid, **{field: value})
                    graph = IntentGraph((intent,), (), intent_evidence=(evidence,))
                    errors = graph.validate()
                    self.assertTrue(errors)
                    self.assertTrue(all(isinstance(error, str) for error in errors))

    def test_intent_evidence_rejects_source_bound_forgery(self):
        cases = [
            (
                dataclasses.replace(
                    self.intent("i1"),
                    task_type="open_source_release",
                    summary="do not push to GitHub",
                ),
                IntentEvidence(
                    "open_source_release",
                    "action",
                    "positive",
                    "action",
                    "explicit_sequence",
                    ("push to github",),
                    999,
                ),
            ),
            (
                dataclasses.replace(
                    self.intent("i1"), task_type="code_review", summary="code review"
                ),
                IntentEvidence(
                    "code_review",
                    "action",
                    "positive",
                    "none",
                    "single",
                    ("website",),
                    0,
                ),
            ),
        ]

        for intent, evidence in cases:
            with self.subTest(summary=intent.summary):
                graph = IntentGraph(
                    (intent,),
                    (),
                    intent_evidence=(evidence,),
                    evidence_source=intent.summary,
                )
                self.assertTrue(graph.validate())

    def test_intent_evidence_rejects_valid_typed_field_forgery(self):
        graph = decompose_task("code review + analyze a spreadsheet")
        original = graph.intent_evidence[0]
        mutations = {
            "context": "descriptive",
            "polarity": "negative",
            "relation_mode": "explicit_sequence",
            "gate_mode": "verification",
            "matched_signals": ("website",),
            "matched_score": original.matched_score + 1,
        }

        for field, value in mutations.items():
            with self.subTest(field=field):
                forged = dataclasses.replace(original, **{field: value})
                rebound = bind_intent_evidence(
                    (forged, *graph.intent_evidence[1:]),
                    graph.evidence_source,
                )
                forged_graph = dataclasses.replace(
                    graph,
                    intent_evidence=rebound,
                )
                self.assertTrue(forged_graph.validate())

    def test_negated_release_cannot_forge_positive_action_with_valid_binding(self):
        intent = dataclasses.replace(
            self.intent("i1"),
            task_type="open_source_release",
            summary="do not push to GitHub",
        )
        source = intent.summary
        forged = bind_intent_evidence(
            (
                IntentEvidence(
                    "open_source_release",
                    "action",
                    "positive",
                    "action",
                    "single",
                    ("push to github",),
                    4,
                ),
            ),
            source,
        )
        graph = IntentGraph(
            (intent,),
            (),
            intent_evidence=forged,
            evidence_source=source,
        )

        self.assertTrue(graph.validate())

    def test_canonical_summary_forgery_fails_closed_without_changing_gate(self):
        source = "After completing code review, build a website"
        graph = decompose_task(source)
        forged_intents = (
            dataclasses.replace(
                graph.intents[0], summary="After verifying code review"
            ),
            graph.intents[1],
        )
        forged_graph = dataclasses.replace(graph, intents=forged_intents)

        self.assertTrue(forged_graph.validate())
        self.assertEqual(
            infer_intent_relations(
                source, forged_intents, graph.intent_evidence
            ),
            (IntentRelation("i1", "i2", "completion_gate", False),),
        )

    def test_canonical_evidence_carries_source_gate_semantics(self):
        completion = decompose_task(
            "After completing code review, build a website"
        )
        verification = decompose_task(
            "After verifying code review, build a website"
        )

        self.assertEqual(completion.intent_evidence[0].gate_mode, "completion")
        self.assertEqual(
            verification.intent_evidence[0].gate_mode, "verification"
        )

    def test_explicit_sequences_create_dependency_chains(self):
        cases = [
            (
                "first analyze the spreadsheet, then write the SEO article",
                [(), ("i1",)],
            ),
            (
                "先做短视频脚本，再接入 agentic media workflow",
                [(), ("i1",)],
            ),
            (
                "Review the PR; build the website; prepare an open-source release",
                [(), ("i1",), ("i1", "i2")],
            ),
            (
                "Govern the role library before planning the multi-agent workflow",
                [(), ("i1",)],
            ),
        ]

        for task, expected_dependencies in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.depends_on for intent in graph.intents],
                    expected_dependencies,
                )

    def test_parallel_and_plain_enumerations_do_not_create_dependencies(self):
        cases = [
            "In parallel: review code, analyze the spreadsheet, and draft an SEO article",
            "同时做 UI 设计、代码审查和表格分析",
            "review code, analyze the spreadsheet, and draft an SEO article",
            "做 UI 设计、代码审查和表格分析",
        ]

        for task in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertTrue(graph.intents)
                self.assertTrue(all(not intent.depends_on for intent in graph.intents))

    def test_plain_plus_readiness_enumerations_do_not_create_release_gates(self):
        cases = [
            (
                "代码审查 + 老板简报 + 发布清单",
                ["code_review", "data_analysis", "open_source_release"],
            ),
            (
                "code review ＋ management brief ＋ release checklist",
                ["code_review", "data_analysis", "open_source_release"],
            ),
            (
                "代码审查 + 一份发布清单",
                ["code_review", "open_source_release"],
            ),
            (
                "代码审查 + 发布清单草案",
                ["code_review", "open_source_release"],
            ),
            (
                "code review + draft release checklist",
                ["code_review", "open_source_release"],
            ),
            (
                "code review + a release checklist",
                ["code_review", "open_source_release"],
            ),
            (
                "code review + the draft release checklist",
                ["code_review", "open_source_release"],
            ),
            (
                "代码审查 + 发布清单 草案",
                ["code_review", "open_source_release"],
            ),
        ]

        for task, expected_task_types in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.task_type for intent in graph.intents],
                    expected_task_types,
                )
                self.assertTrue(all(not intent.depends_on for intent in graph.intents))
                self.assertEqual(graph.dependency_relations, ())

    def test_release_actions_and_explicit_readiness_sequences_keep_dependencies(self):
        cases = [
            "code review + publish update",
            "code review + then release checklist",
            "先代码审查，再发布清单",
            "After code review + release checklist",
        ]

        for task in cases:
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(graph.intents[-1].task_type, "open_source_release")
                self.assertTrue(graph.intents[-1].depends_on)
                self.assertTrue(
                    any(
                        relation.target_id == graph.intents[-1].id
                        for relation in graph.dependency_relations
                    )
                )

    def test_order_lead_in_plus_enumeration_creates_complete_source_chain(self):
        graph = decompose_task(
            "执行顺序：代码审查 + 老板简报 + 发布清单"
        )

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["code_review", "data_analysis", "open_source_release"],
        )
        self.assertEqual(
            [intent.depends_on for intent in graph.intents],
            [(), ("i1",), ("i1", "i2")],
        )
        self.assertIn(
            IntentRelation("i1", "i2", "explicit_sequence", False),
            graph.dependency_relations,
        )

    def test_then_marker_in_plus_enumeration_creates_complete_source_chain(self):
        graph = decompose_task(
            "代码审查 + 然后老板简报 + 发布清单"
        )

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["code_review", "data_analysis", "open_source_release"],
        )
        self.assertEqual(
            [intent.depends_on for intent in graph.intents],
            [(), ("i1",), ("i1", "i2")],
        )

    def test_decompose_task_remains_graph_only_compatibility_wrapper(self):
        graph = decompose_task("审计 skill router")

        self.assertIsInstance(graph, IntentGraph)
        self.assertNotIsInstance(graph, TaskDecomposition)

    def test_normalize_task_preserves_structured_context(self):
        normalized = normalize_task(
            "历史：之前在写官网\n当前任务：审计 skill 路由器\n过期上下文：发布旧版本"
        )

        self.assertEqual(normalized.current, "审计 skill 路由器")
        self.assertEqual(normalized.history, "之前在写官网")
        self.assertEqual(normalized.stale, "发布旧版本")
        self.assertEqual(normalized.stale_policy, "ignore_for_routing")

    def test_stale_context_is_ignored_for_routing(self):
        graph = decompose_task(
            "历史：之前在写官网\n当前任务：审计 skill 路由器\n过期上下文：发布旧版本"
        )

        self.assertEqual([intent.task_type for intent in graph.intents], ["skill_router_review"])

    def test_decompose_compound_release_task(self):
        graph = decompose_task("构建官网，同时审计 skill 路由器，验证通过后发布更新")

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["website_build", "skill_router_review", "open_source_release"],
        )
        self.assertEqual(graph.intents[2].depends_on, ("i1", "i2"))
        self.assertEqual(graph.intents[2].required_artifacts, ("release_record",))
        self.assertEqual(graph.intents[2].risk_flags, ("public_release",))
        self.assertEqual(graph.validate(), [])

    def test_release_boundary_without_object_depends_on_website_build(self):
        graph = decompose_task("构建官网，验证通过后发布")

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["website_build", "open_source_release"],
        )
        self.assertEqual(graph.intents[1].depends_on, ("i1",))

    def test_test_passed_go_live_boundary_creates_release_dependency(self):
        graph = decompose_task("完成测试，测试通过后上线")

        self.assertEqual(len(graph.intents), 2)
        self.assertEqual(graph.intents[1].task_type, "open_source_release")
        self.assertEqual(graph.intents[1].depends_on, ("i1",))

    def test_completed_build_push_boundary_creates_release_dependency(self):
        graph = decompose_task("完成构建，完成后推送")

        self.assertEqual(len(graph.intents), 2)
        self.assertEqual(graph.intents[1].task_type, "open_source_release")
        self.assertEqual(graph.intents[1].depends_on, ("i1",))

    def test_does_not_over_split_code_review_lifecycle(self):
        graph = decompose_task("审查代码并补强测试后合并 PR")

        self.assertEqual(len(graph.intents), 1)
        self.assertEqual(graph.intents[0].task_type, "code_review")

    def test_lifecycle_exception_applies_per_candidate_clause(self):
        graph = decompose_task("审查代码并补强测试后合并 PR，同时构建官网")

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["code_review", "website_build"],
        )

    def test_mixed_lifecycle_release_depends_on_prior_intents(self):
        graph = decompose_task("审查代码并补强测试后合并 PR，同时构建官网；发布更新")

        self.assertEqual(
            [intent.task_type for intent in graph.intents],
            ["code_review", "website_build", "open_source_release"],
        )
        self.assertEqual(graph.intents[2].depends_on, ("i1", "i2"))

    def test_numbered_steps_create_release_dependencies(self):
        graph = decompose_task("1. 分析数据\n2. 生成报告\n3. 发布结果")

        self.assertEqual(len(graph.intents), 3)
        self.assertEqual(graph.intents[2].depends_on, ("i1", "i2"))

    def test_release_detection_rejects_negation_preconditions_and_nouns(self):
        cases = [
            (
                "不要发布，只审计 skill 路由器",
                "skill_router_review",
                ("skill_pack", "catalog", "router_report"),
                ("tool_overload", "policy_fragmentation", "misrouting"),
            ),
            (
                "发布前先审计 skill 路由器",
                "skill_router_review",
                ("skill_pack", "catalog", "router_report"),
                ("tool_overload", "policy_fragmentation", "misrouting"),
            ),
            ("生成 release notes", "general", (), ()),
            ("publishable package audit", "general", (), ()),
        ]

        for task, expected_task_type, expected_artifacts, expected_risks in cases:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertEqual(intent.task_type, expected_task_type)
                self.assertEqual(intent.required_artifacts, expected_artifacts)
                self.assertEqual(intent.risk_flags, expected_risks)

    def test_release_detection_accepts_explicit_actions(self):
        for task in [
            "发布更新",
            "发布结果",
            "publish update",
            "release the package",
            "推送 GitHub",
            "push to GitHub",
            "push the repository",
        ]:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertEqual(intent.task_type, "open_source_release")
                self.assertEqual(intent.required_artifacts, ("release_record",))
                self.assertEqual(intent.risk_flags, ("public_release",))

    def test_push_release_detection_rejects_negation_and_preconditions(self):
        for task in [
            "不要推送 GitHub",
            "do not push to GitHub",
            "never push to GitHub",
            "before pushing to GitHub",
            "推送 GitHub 前",
        ]:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertNotEqual(intent.task_type, "open_source_release")
                self.assertNotEqual(intent.required_artifacts, ("release_record",))

    def test_natural_push_phrases_reject_negation_and_preconditions(self):
        for task in [
            "不要推送到 GitHub",
            "推送到 GitHub 前",
            "do not push changes to GitHub",
            "before pushing changes to GitHub",
            "do not push the repository to GitHub",
            "before pushing the repository to GitHub",
        ]:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertNotEqual(intent.task_type, "open_source_release")
                self.assertNotEqual(intent.required_artifacts, ("release_record",))

    def test_natural_push_phrases_accept_explicit_actions(self):
        for task in [
            "推送到 GitHub",
            "push changes to GitHub",
            "push the repository to GitHub",
        ]:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertEqual(intent.task_type, "open_source_release")
                self.assertEqual(intent.required_artifacts, ("release_record",))

    def test_mixed_release_polarity_is_evaluated_per_adversative_segment(self):
        for task in [
            "Do not push to GitHub, but publish the update",
            "Publish the update, but do not push to GitHub",
            "不要推送 GitHub，但是发布更新",
            "发布更新，但要不推送 GitHub",
        ]:
            with self.subTest(task=task):
                intent = decompose_task(task).intents[0]
                self.assertEqual(intent.task_type, "open_source_release")
                self.assertEqual(intent.required_artifacts, ("release_record",))

    def test_ambiguous_english_and_phrases_remain_single_intents(self):
        for task in [
            "Research and Development roadmap",
            "AT&T and Verizon data",
            "command and control risks",
        ]:
            with self.subTest(task=task):
                self.assertEqual(len(decompose_task(task).intents), 1)

    def test_clear_english_then_sequence_splits(self):
        graph = decompose_task("audit the skill router then publish update")

        self.assertEqual(len(graph.intents), 2)
        self.assertEqual(graph.intents[1].task_type, "open_source_release")
        self.assertEqual(graph.intents[1].depends_on, ("i1",))

    def test_models_are_frozen_and_convert_tuples_to_json_arrays(self):
        normalized = normalize_task("构建官网")
        graph = decompose_task("构建官网，同时发布更新")

        with self.assertRaises(dataclasses.FrozenInstanceError):
            normalized.current = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            graph.intents[0].summary = "changed"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            graph.intents = ()

        payload = graph.to_json()
        self.assertIsInstance(payload["intents"], list)
        self.assertIsInstance(payload["intents"][0]["required_artifacts"], list)
        self.assertIsInstance(payload["intents"][0]["risk_flags"], list)
        self.assertIsInstance(payload["intents"][1]["depends_on"], list)
        json.dumps(payload)

    def test_internal_dependency_relations_do_not_change_json_shape(self):
        graph = decompose_task("Once the PR is verified, build the website")

        self.assertTrue(graph.dependency_relations)
        self.assertEqual(
            set(graph.to_json()), {"intents", "unresolved_dependencies"}
        )

    def test_validate_reports_unknown_dependencies(self):
        graph = IntentGraph(
            intents=(self.intent("i1", depends_on=("i9",)),),
            unresolved_dependencies=(),
        )

        self.assertEqual(graph.validate(), ["intent i1 depends on unknown intent i9"])

    def test_validate_rejects_malformed_dependency_relation_collections(self):
        valid_relation = IntentRelation("i1", "i2", "before", False)
        for relations in [None, "bad", [valid_relation]]:
            with self.subTest(relations=relations):
                graph = IntentGraph(
                    intents=(self.intent("i1"), self.intent("i2", ("i1",))),
                    unresolved_dependencies=(),
                    dependency_relations=relations,
                )

                self.assertIn(
                    "dependency_relations must be a tuple of IntentRelation records",
                    graph.validate(),
                )

    def test_validate_rejects_malformed_dependency_relation_records(self):
        cases = [
            ((object(),), "dependency relation must be an IntentRelation"),
            (
                (IntentRelation([], "i2", "before", False),),
                "dependency relation has invalid source id: []",
            ),
            (
                (IntentRelation("bad", "i2", "before", False),),
                "dependency relation has invalid source id: bad",
            ),
            (
                (IntentRelation("i9", "i2", "before", False),),
                "dependency relation has unknown source id: i9",
            ),
            (
                (IntentRelation("i1", "i9", "before", False),),
                "dependency relation has unknown target id: i9",
            ),
            (
                (IntentRelation("i1", "i1", "before", False),),
                "dependency relation cannot be self-referential: i1",
            ),
            (
                (IntentRelation("i2", "i1", "before", False),),
                "dependency relation i2 -> i1 is not represented by depends_on",
            ),
            (
                (IntentRelation("i1", "i2", "unsupported", False),),
                "dependency relation has unsupported reason: unsupported",
            ),
            (
                (IntentRelation("i1", "i2", [], False),),
                "dependency relation has unsupported reason: []",
            ),
            (
                (IntentRelation("i1", "i2", "before", 1),),
                "dependency relation requires_verification must be bool",
            ),
        ]

        for relations, expected in cases:
            with self.subTest(expected=expected):
                graph = IntentGraph(
                    intents=(self.intent("i1"), self.intent("i2", ("i1",))),
                    unresolved_dependencies=(),
                    dependency_relations=relations,
                )
                self.assertIn(expected, graph.validate())

    def test_validate_rejects_duplicate_and_conflicting_relation_metadata(self):
        for relations in [
            (
                IntentRelation("i1", "i2", "before", False),
                IntentRelation("i1", "i2", "before", False),
            ),
            (
                IntentRelation("i1", "i2", "before", False),
                IntentRelation("i1", "i2", "verification_gate", True),
            ),
        ]:
            with self.subTest(relations=relations):
                graph = IntentGraph(
                    intents=(self.intent("i1"), self.intent("i2", ("i1",))),
                    unresolved_dependencies=(),
                    dependency_relations=relations,
                )
                self.assertIn(
                    "duplicate dependency relation metadata: i1 -> i2",
                    graph.validate(),
                )

    def test_validate_rejects_reason_verification_semantic_mismatches(self):
        cases = [
            ("verification_gate", False),
            ("release_gate", False),
            ("completion_gate", True),
            ("explicit_sequence", True),
            ("semicolon_workflow", True),
            ("before", True),
            ("first_then", True),
            ("semicolon_sequence", True),
        ]

        for reason, requires_verification in cases:
            with self.subTest(
                reason=reason, requires_verification=requires_verification
            ):
                graph = IntentGraph(
                    intents=(self.intent("i1"), self.intent("i2", ("i1",))),
                    unresolved_dependencies=(),
                    dependency_relations=(
                        IntentRelation(
                            "i1", "i2", reason, requires_verification
                        ),
                    ),
                )

                self.assertIn(
                    "dependency relation verification requirement mismatches "
                    f"reason: {reason}",
                    graph.validate(),
                )

    def test_decomposed_relation_reason_semantics_validate(self):
        for task in [
            "After verifying the PR, build the website",
            "After completing the PR review, build the website",
            "Review the PR before building the website",
            "Review the PR; build the website; prepare an open-source release",
        ]:
            with self.subTest(task=task):
                self.assertEqual(decompose_task(task).validate(), [])

    def test_validate_requires_complete_metadata_when_any_record_is_present(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i2", ("i1",)),
                self.intent("i3", ("i2",)),
            ),
            unresolved_dependencies=(),
            dependency_relations=(
                IntentRelation("i1", "i2", "before", False),
            ),
        )

        self.assertIn(
            "dependency relation metadata missing for edge: i2 -> i3",
            graph.validate(),
        )

    def test_validate_rejects_duplicate_ids_before_dependency_analysis(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1"),
                self.intent("i1", depends_on=("i9",)),
            ),
            unresolved_dependencies=(),
        )

        self.assertEqual(graph.validate(), ["duplicate intent id: i1"])

    def test_validate_reports_cycles(self):
        graph = IntentGraph(
            intents=(
                self.intent("i1", depends_on=("i2",)),
                self.intent("i2", depends_on=("i1",)),
            ),
            unresolved_dependencies=(),
        )

        self.assertEqual(graph.validate(), ["intent dependency cycle detected: i1 -> i2 -> i1"])

    def test_validate_rejects_empty_graph_and_invalid_intent_fields(self):
        invalid_intent = Intent(
            id="bad-id",
            summary=" ",
            task_type="",
            required_artifacts=("",),
            risk_flags=("",),
            depends_on=("bad-dependency",),
            source="model",
            confidence=1.1,
        )

        self.assertEqual(IntentGraph(intents=(), unresolved_dependencies=()).validate(), ["intent graph is empty"])
        self.assertEqual(
            IntentGraph(intents=(invalid_intent,), unresolved_dependencies=("",)).validate(),
            [
                "invalid intent id: bad-id",
                "intent bad-id summary must be nonempty",
                "intent bad-id task_type must be nonempty",
                "intent bad-id required_artifacts must contain nonempty strings",
                "intent bad-id risk_flags must contain nonempty strings",
                "intent bad-id has invalid dependency id: bad-dependency",
                "intent bad-id depends on unknown intent bad-dependency",
                "intent bad-id has invalid source: model",
                "intent bad-id confidence must be between 0 and 1",
                "unresolved_dependencies must contain nonempty strings",
            ],
        )

    def test_validate_reports_malformed_collection_fields_without_raising(self):
        invalid_intent = Intent(
            id="i1",
            summary="audit",
            task_type="code_review",
            required_artifacts=None,
            risk_flags="risk",
            depends_on=None,
            source="deterministic",
            confidence=True,
        )

        self.assertEqual(
            IntentGraph(intents=(invalid_intent,), unresolved_dependencies=None).validate(),
            [
                "intent i1 required_artifacts must contain nonempty strings",
                "intent i1 risk_flags must contain nonempty strings",
                "intent i1 depends_on must contain valid intent IDs",
                "intent i1 confidence must be between 0 and 1",
                "unresolved_dependencies must contain nonempty strings",
            ],
        )

    def test_numbered_and_bulleted_lists_preserve_continuation_lines(self):
        self.assertEqual(
            split_task_clauses("1. 分析数据\n   包含季度趋势\n2. 发布结果"),
            ["分析数据 包含季度趋势", "发布结果"],
        )
        self.assertEqual(
            split_task_clauses("- 审计 skill 路由器\n  检查依赖图\n- 构建官网"),
            ["审计 skill 路由器 检查依赖图", "构建官网"],
        )

    def test_schema_uses_2020_12_and_strict_intent_objects(self):
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "intent-graph.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        intent_schema = schema["properties"]["intents"]["items"]

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["intents"]["minItems"], 1)
        self.assertEqual(set(schema["required"]), {"intents", "unresolved_dependencies"})
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(intent_schema["required"]),
            {
                "id",
                "summary",
                "task_type",
                "required_artifacts",
                "risk_flags",
                "depends_on",
                "source",
                "confidence",
            },
        )
        self.assertFalse(intent_schema["additionalProperties"])
        self.assertEqual(intent_schema["properties"]["id"]["pattern"], "^i[1-9][0-9]*$")
        self.assertEqual(intent_schema["properties"]["summary"]["minLength"], 1)
        self.assertEqual(intent_schema["properties"]["task_type"]["minLength"], 1)
        self.assertEqual(
            intent_schema["properties"]["required_artifacts"]["items"]["minLength"],
            1,
        )
        self.assertEqual(intent_schema["properties"]["risk_flags"]["items"]["minLength"], 1)
        self.assertEqual(
            schema["properties"]["unresolved_dependencies"]["items"]["minLength"],
            1,
        )
        self.assertEqual(
            intent_schema["properties"]["source"]["enum"],
            ["deterministic", "semantic", "hybrid"],
        )
        self.assertEqual(intent_schema["properties"]["confidence"]["minimum"], 0)
        self.assertEqual(intent_schema["properties"]["confidence"]["maximum"], 1)

    def test_generated_payload_matches_required_schema_shape(self):
        payload = decompose_task("构建官网，同时发布更新").to_json()
        self.assertEqual(set(payload), {"intents", "unresolved_dependencies"})
        self.assertGreaterEqual(len(payload["intents"]), 1)
        for intent in payload["intents"]:
            self.assertEqual(
                set(intent),
                {
                    "id",
                    "summary",
                    "task_type",
                    "required_artifacts",
                    "risk_flags",
                    "depends_on",
                    "source",
                    "confidence",
                },
            )
            self.assertRegex(intent["id"], r"^i[1-9][0-9]*$")
            self.assertTrue(intent["summary"].strip())
            self.assertTrue(intent["task_type"].strip())
            self.assertIn(intent["source"], {"deterministic", "semantic", "hybrid"})
            self.assertGreaterEqual(intent["confidence"], 0)
            self.assertLessEqual(intent["confidence"], 1)
            for field in ["required_artifacts", "risk_flags", "depends_on"]:
                self.assertIsInstance(intent[field], list)
                self.assertTrue(all(isinstance(value, str) and value for value in intent[field]))

    @staticmethod
    def intent(intent_id, depends_on=()):
        return Intent(
            id=intent_id,
            summary=intent_id,
            task_type="general",
            required_artifacts=(),
            risk_flags=(),
            depends_on=depends_on,
            source="deterministic",
            confidence=1.0,
        )


if __name__ == "__main__":
    unittest.main()
