import dataclasses
import importlib
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
    source_supports_release_readiness,
    validate_intent_evidence,
)
from onecode_skill_sanitizer.intent_dependencies import infer_intent_relations


class IntentTest(unittest.TestCase):
    def test_release_readiness_proposition_parser_contract(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions

        positive_cases = (
            "Prepare a repository release packet for review, but do not publish it.",
            "Do not publish it yet, but prepare a repository release checklist.",
            "Audit unauthorized access and prepare a repository release packet.",
            "Prepare an npm release packet.",
            "Draft a Docker image release checklist.",
            "Review the release checklist for v1.0.",
            "Prepare a maintainer-ready release packet for a CLI project.",
            "Prepare package release readiness checks.",
            "Prepare a content-management repository release packet.",
            "Prepare a model-serving repository release packet.",
            "Prepare a repository release packet for talent-platform maintainers.",
            "Prepare a repository content-management release packet.",
            "Prepare a software model-serving release packet.",
            "Prepare an npm content-management release packet.",
            "Prepare a content-management release packet for the repository.",
            "Prepare a model-serving release packet for the software repository.",
            "Prepare a content management release packet for the repository.",
            "Prepare a model serving release packet for the software repository.",
            "Prepare a content–management release packet for the repository.",
            "Prepare a content－management release packet for the repository.",
            "Prepare a model−serving release packet for the software repository.",
            "Prepare a content-management release packet for 仓库.",
            "Prepare a model-serving release packet for 代码库.",
            "Prepare a repository-and-CLI content-management release packet.",
            "Prepare a repository－and－CLI content-management release packet.",
            "Prepare a content-management release packet for our repository.",
            "Prepare a content-management release packet for an internal repository.",
            "Prepare a content-management release packet for GitHub repository "
            "maintainers.",
            "Prepare a content-management release packet for the package maintainers.",
            "Prepare a content-management release packet for maintainers.",
            "Prepare a content-management release packet for the maintainers.",
            "Prepare a content-management release packet for code artifacts.",
            "Prepare a content-management release packet for the code artifacts.",
            "Prepare a content-management release packet for main repository.",
            "Prepare a content-management release packet for upstream repository.",
            "Prepare a content-management release packet for project repository.",
            "Prepare a content-management release packet for Acme's repository.",
            "Prepare a content-management release packet for GitLab repository.",
            "Prepare a content-management release packet for Python package "
            "maintainers.",
            "Prepare a content-management release packet for project maintainers.",
            "Prepare a content-management release packet for repositories.",
            "Prepare a content-management release packet for repos.",
            "Prepare a content-management release packet for codebases.",
            "Prepare a content-management release packet for this project's "
            "repository.",
            "Prepare a content-management release packet for the project's repository.",
            "Prepare a content-management release packet for github repository.",
            "Prepare a content-management release packet for external repository.",
            "Prepare a content-management release packet for Python package.",
            "Prepare a content-management release packet for Python packages.",
            "Prepare a content-management release packet for GitHub packages.",
            "Prepare a content-management release packet for GitLab package.",
            "Prepare a content-management release packet for npm package.",
            "Prepare a content-management release packet for npm packages.",
            "Prepare a content-management release packet for software package.",
            "Prepare a content-management release packet for software packages.",
            "Prepare a content-management release packet for open-source package.",
            "Prepare a content-management release packet for open-source packages.",
            "Review content notes. Prepare a release checklist for v1.0.",
            "release checklist",
            "发布清单",
        )
        for source in positive_cases:
            with self.subTest(source=source):
                propositions = parse(source)
                positive = [
                    item
                    for item in propositions
                    if item.polarity == "positive"
                    and item.discourse_role == "request"
                ]
                self.assertEqual(len(positive), 1)
                item = positive[0]
                self.assertGreaterEqual(item.start, 0)
                self.assertGreater(item.end, item.start)
                self.assertLessEqual(item.end, len(source))
                self.assertTrue(item.action)
                self.assertTrue(item.object_text)
                self.assertIn(item.object_text, source[item.start : item.end])

    def test_release_readiness_proposition_parser_rejects_references_and_negation(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        rejected_cases = (
            "Can't prepare a repository release packet.",
            "Cannot prepare a repository release packet.",
            "No need to prepare a repository release packet.",
            "Not authorized to prepare a repository release packet.",
            "Mustn't prepare a repository release packet.",
            "Should not prepare a repository release checklist.",
            '"Prepare a repository release packet"',
            "# Prepare a repository release checklist",
            "> Prepare a repository release checklist",
            "- [ ] Prepare a repository release checklist",
            "<h2>Prepare a repository release checklist</h2>",
            "Label: Prepare a repository release checklist",
            "Title: Prepare a repository release checklist",
            "Navigation: Prepare a repository release checklist",
            "release-checklist.json",
            "README: prepare a repository release checklist",
            "Prepare a talent release packet for a photo shoot",
            "Prepare a model release packet for the photographer",
            "Prepare a content release packet for the campaign",
            "Prepare a talent release packet for repository maintainers.",
            "Prepare a model release packet for a software repository.",
            "Prepare a talent authorization release packet for repository "
            "maintainers.",
            "Prepare a model photography release packet for a software repository.",
            "Prepare a content licensing release packet for a software repository.",
            "Prepare a model's release packet for a software repository.",
            "Prepare a content package release packet for a campaign.",
            "Prepare a talent package release packet for repository maintainers.",
            "Review repository code and prepare a talent release packet for a v1.0 "
            "campaign.",
            "Prepare a talent authorization document for repository maintainers and "
            "review a model release packet for v1.0.",
            "Review repo code and prepare a content licensing release packet for "
            "v1.0.",
            "Prepare a content-management release packet for a campaign package.",
            "Prepare a model-serving release packet for a photography package.",
            "Prepare a talent research-and-review release packet for v1.0.",
            "Prepare a content drafting-and-review release packet for a software "
            "repository.",
            "Prepare a content-management release packet for a campaign package "
            "while reviewing repository code.",
            "Prepare a model-serving release packet for a photography package "
            "while auditing software code.",
            "Prepare a content-management release packet for a campaign package "
            "after reviewing repository code.",
            "Prepare a content-management release packet for a campaign package "
            "before reviewing repository code.",
            "Prepare a content-management release packet for a campaign package "
            "during repository code review.",
            "Prepare a content-management release packet for a campaign package "
            "when reviewing repository code.",
            "Prepare a content-management release packet for a campaign package "
            "as repository code is reviewed.",
            "Prepare a content-management release packet for a campaign package "
            "with repository code under review.",
            "Prepare a content-management release packet for a campaign package "
            "alongside repository code review.",
            "Prepare a content-management release packet for a campaign package "
            "because repository code passed review.",
            "Prepare a content-management release packet for campaign material "
            "following repository code review.",
            "Prepare a content-management release packet for campaign material "
            "once repository code review passes.",
            "Prepare a content-management release packet for campaign material "
            "since repository code passed review.",
            "Prepare a content-management release packet for campaign material "
            "upon repository code review.",
            "Prepare a content-management release packet for campaign material "
            "if repository code passes review.",
            "Prepare a content-management release packet for campaign material "
            "despite repository code review.",
            "Prepare a content-management release packet for Following repository "
            "code review.",
            "Prepare a content-management release packet for Python package "
            "campaign.",
            "Prepare a content-management release packet for the Python package "
            "campaign.",
            "Prepare a content-management release packet for GitLab package "
            "promotion.",
            "Prepare a content-management release packet for GitHub package "
            "photography campaign.",
        )
        for source in rejected_cases:
            with self.subTest(source=source):
                self.assertFalse(
                    any(
                        item.polarity == "positive"
                        and item.discourse_role == "request"
                        for item in parse(source)
                    )
                )

    def test_release_actions_require_proposition_anchored_request_grammar(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        requests = (
            "Prepare a repository release checklist.",
            "Please prepare a repository release checklist.",
            "Kindly review the release checklist for v1.0.",
            "We need to prepare a repository release checklist.",
            "I should review the release checklist for v1.0.",
            "You must prepare a repository release checklist.",
            "The team wants to review the release checklist for v1.0.",
            "Maintainers need to prepare a repository release checklist.",
            "Could you prepare a repository release checklist?",
            "Would you kindly review the release checklist for v1.0?",
            "Can you please prepare a repository release checklist?",
            "For v1.0, prepare a repository release checklist.",
            "Before publishing, review the repository release checklist.",
            "Use the audit report to prepare a repository release checklist.",
            "After reviewing the report, prepare a repository release checklist.",
            "Before updating the documentation, prepare a repository release checklist.",
            "Use the guide to review the repository release checklist.",
            "First, prepare a repository release checklist.",
            "Next, review the release checklist for v1.0.",
            "Now prepare a repository release checklist.",
            "Let’s prepare a repository release checklist.",
            "I would like to prepare a repository release checklist.",
            "We plan to prepare a repository release checklist.",
            "Make sure to prepare a repository release checklist.",
            "Please help prepare a repository release checklist.",
            "麻烦准备一个仓库发布清单。",
            "请帮忙准备详细的仓库发布清单。",
            "我们计划准备仓库发布清单。",
            "接下来准备仓库发布清单。",
            "请准备仓库发布清单。",
            "请你审查仓库发布清单。",
            "我们需要准备仓库发布清单。",
            "维护者应审查仓库发布清单。",
            "团队要准备仓库发布清单。",
            "并行处理两项交付：审计提示词注入、工具权限与输出护栏；同时准备"
            "开源仓库的许可证、供应链与发布清单，分别给出证据。",
        )
        for source in requests:
            with self.subTest(source=source):
                self.assertTrue(
                    any(
                        item.polarity == "positive"
                        and item.discourse_role == "request"
                        for item in parse(source)
                    )
                )

        controls = (
            "Under no circumstances prepare a repository release checklist.",
            "We are unable to prepare a repository release checklist.",
            "It is forbidden to prepare a repository release checklist.",
            "I cannot bring myself to prepare a repository release checklist.",
            "Review everything other than the repository release checklist.",
            "The report states that maintainers should prepare a repository release checklist.",
            "The report recommends that maintainers prepare a repository release checklist.",
            "According to the report, prepare a repository release checklist.",
            "The guide instructs maintainers to prepare a repository release checklist.",
            "Documentation requires us to prepare a repository release checklist.",
            "We do not plan to prepare a repository release checklist.",
            "The report plans to prepare a repository release checklist.",
        )
        for source in controls:
            with self.subTest(source=source):
                self.assertFalse(
                    any(
                        item.polarity == "positive"
                        and item.discourse_role == "request"
                        for item in parse(source)
                    )
                )

        boundaries = (
            (
                "According to the report, prepare a repository release packet; "
                "prepare a repository release checklist.",
                ("reference", "request"),
            ),
            (
                "Use the audit report to prepare a repository release packet; "
                "according to the guide, review the release checklist for v1.0.",
                ("request", "reference"),
            ),
        )
        for source, expected in boundaries:
            with self.subTest(source=source):
                self.assertEqual(
                    tuple(item.discourse_role for item in parse(source)),
                    expected,
                )

    def test_release_readiness_proposition_parser_binds_local_action_and_object(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        variants = (
            "Prepare a repository release packet, but do not publish it.",
            "Do not publish it, but prepare a repository release packet.",
            "Do not publish it; prepare a repository release packet.",
            "Prepare a repository release packet; do not publish it.",
        )
        for source in variants:
            with self.subTest(source=source):
                propositions = parse(source)
                readiness = [
                    item
                    for item in propositions
                    if item.object_text.casefold().endswith("release packet")
                ]
                self.assertEqual(len(readiness), 1)
                self.assertEqual(readiness[0].action, "prepare")
                self.assertEqual(readiness[0].polarity, "positive")
                self.assertEqual(readiness[0].discourse_role, "request")

    def test_release_readiness_propositions_do_not_cross_sentence_boundaries(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        negative = "Cannot prepare a repository release packet"
        positive = "Prepare a repository release checklist"
        matrices = (
            (f"{negative}. {positive}.", ("negative", "positive")),
            (f"{positive}. {negative}.", ("positive", "negative")),
            (f"{negative}? {positive}!", ("negative", "positive")),
            (f"{positive}!! {negative}??", ("positive", "negative")),
        )

        for source, expected_polarities in matrices:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(
                    tuple(item.polarity for item in propositions),
                    expected_polarities,
                )
                self.assertEqual(
                    tuple(item.discourse_role for item in propositions),
                    tuple(
                        "request" if polarity == "positive" else "reference"
                        for polarity in expected_polarities
                    ),
                )
                for item in propositions:
                    span = source[item.start : item.end]
                    self.assertEqual(item.action, "prepare")
                    self.assertTrue(span.casefold().startswith("prepare"))
                    self.assertIn(item.object_text, span)

    def test_release_readiness_structural_roles_are_proposition_local(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        reference = "Example: prepare a repository release packet"
        request = "Prepare a repository release checklist"
        matrices = (
            (f"{reference}. {request}.", ("reference", "request")),
            (f"{request}. {reference}.", ("request", "reference")),
            (f"{reference}! {request}?", ("reference", "request")),
        )

        for source, expected_roles in matrices:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(
                    tuple(item.discourse_role for item in propositions),
                    expected_roles,
                )
                self.assertEqual(
                    sum(
                        item.polarity == "positive"
                        and item.discourse_role == "request"
                        for item in propositions
                    ),
                    1,
                )

    def test_release_sentence_boundaries_preserve_versions_files_and_abbreviations(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        cases = (
            "Review the release checklist for v1.0.",
            "Use e.g. repository metadata to prepare a repository release checklist.",
        )
        for source in cases:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].discourse_role, "request")
                self.assertEqual(propositions[0].polarity, "positive")

        controls = (
            "README.md describes a release checklist.",
            "The v1.0.release-checklist.json filename is documented.",
        )
        for source in controls:
            with self.subTest(source=source):
                self.assertFalse(
                    any(
                        item.discourse_role == "request"
                        for item in parse(source)
                    )
                )

    def test_release_action_polarity_is_token_aware_and_local(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        negative_cases = (
            "They asked you not to prepare a repository release packet.",
            "Not prepare a repository release packet.",
            "Won't prepare a repository release packet.",
            "Won’t prepare a repository release packet.",
            "Will not prepare a repository release packet.",
            "Cannot prepare a repository release packet.",
            "Can't prepare a repository release packet.",
            "No need to immediately prepare a repository release packet.",
            "Not authorized to carefully prepare a repository release packet.",
            "Do not immediately prepare a repository release packet.",
            "Review the repository, not the release checklist for v1.0.",
            "不要立即准备仓库发布清单。",
            "不会准备仓库发布清单。",
            "不可准备仓库发布清单。",
            "无需立即准备仓库发布清单。",
        )
        for source in negative_cases:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertFalse(
                    any(
                        item.polarity == "positive"
                        and item.discourse_role == "request"
                        for item in propositions
                    )
                )

        coordinated = (
            "Do not review the repository release packet, but prepare a "
            "repository release checklist.",
            "Prepare a repository release checklist, but do not review the "
            "repository release packet.",
        )
        for source in coordinated:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(
                    sorted(item.polarity for item in propositions),
                    ["negative", "positive"],
                )

    def test_release_negation_attachment_exempts_positive_obligations(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        positive_cases = (
            "Do not forget to prepare a repository release packet.",
            "Don't forget to prepare a repository release packet.",
            "Do not fail to prepare a repository release checklist.",
            "Do not neglect to prepare a repository release packet.",
            "Please do not hesitate to prepare a repository release checklist.",
            "Not only prepare a repository release packet, but also document it.",
        )
        for source in positive_cases:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].polarity, "positive")
                self.assertEqual(propositions[0].discourse_role, "request")

        negative_cases = (
            "Do not plan to prepare a repository release packet.",
            "Don't intend to prepare a repository release checklist.",
            "Will not currently plan to prepare a repository release packet.",
            "Asked you not to immediately prepare a repository release packet.",
            "Do not automatically prepare a repository release checklist.",
        )
        for source in negative_cases:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].polarity, "negative")

    def test_release_negation_accepts_grammatical_adverb_tokens_only(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        unseen_adverbs = (
            "quickly",
            "accidentally",
            "inadvertently",
            "unexpectedly",
            "swiftly",
            "surprisingly",
        )
        templates = (
            "Do not {adverb} prepare a repository release packet.",
            "Won't {adverb} review the release checklist for v1.0.",
        )
        for adverb in unseen_adverbs:
            for template in templates:
                source = template.format(adverb=adverb)
                with self.subTest(source=source):
                    propositions = parse(source)
                    self.assertEqual(len(propositions), 1)
                    self.assertEqual(propositions[0].polarity, "negative")

            positive = (
                f"{adverb.title()} prepare a repository release packet."
            )
            with self.subTest(source=positive):
                propositions = parse(positive)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].polarity, "positive")

        controls = (
            ("Do not want to prepare a repository release packet.", "negative"),
            ("Do not plan to prepare a repository release packet.", "negative"),
            ("Don't intend to review the release checklist for v1.0.", "negative"),
            (
                "Do not quickly forget to prepare a repository release packet.",
                "positive",
            ),
            (
                "Do not accidentally fail to prepare a repository release checklist.",
                "positive",
            ),
            (
                "Do not inadvertently neglect to prepare a repository release packet.",
                "positive",
            ),
        )
        for source, expected in controls:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].polarity, expected)

    def test_release_parser_covers_explicit_prohibition_grammar(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        prohibited = (
            "I am not going to prepare a repository release packet.",
            "The team is not going to review the release checklist for v1.0.",
            "We are not going to prepare a repository release packet.",
            "Not to prepare a repository release packet.",
            "We have no plans to prepare a repository release checklist.",
            "You are not to review the release checklist for v1.0.",
            "请勿准备仓库发布清单。",
            "不会准备仓库发布清单。",
            "不打算准备仓库发布清单。",
            "禁止审查软件包发布清单。",
            "不可准备仓库发布清单。",
            "无需准备仓库发布清单。",
        )
        for source in prohibited:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertFalse(
                    any(
                        item.polarity == "positive"
                        and item.discourse_role == "request"
                        for item in propositions
                    )
                )

        coordinated = (
            "I am not going to prepare a repository release packet, but "
            "prepare a repository release checklist.",
            "请勿准备仓库发布清单；然后 prepare a repository release packet.",
        )
        for source in coordinated:
            with self.subTest(source=source):
                self.assertEqual(
                    sorted(item.polarity for item in parse(source)),
                    ["negative", "positive"],
                )

    def test_release_parser_covers_refusal_and_object_exclusion_grammar(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        prohibited = (
            "I refuse to prepare a repository release packet.",
            "They refused to review the release checklist for v1.0.",
            "We decline to prepare a repository release checklist.",
            "The maintainer declined to review the release checklist for v1.0.",
            "You are not permitted to prepare a repository release packet.",
            "We are not allowed to review the release checklist for v1.0.",
            "There is no requirement to prepare a repository release checklist.",
            "There is no need to prepare a repository release packet.",
            "There is no plan to review the release checklist for v1.0.",
            "Review the repository rather than the release checklist for v1.0.",
            "Review the repository instead of the release checklist for v1.0.",
            "Review the repository, excluding a release checklist for v1.0.",
            "Review the repository except a release checklist for v1.0.",
        )
        for source in prohibited:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].polarity, "negative")

        coordinated = (
            "I refuse to prepare a repository release packet, but prepare a "
            "repository release checklist.",
            "Review the repository rather than the release checklist for v1.0; "
            "prepare a repository release packet.",
        )
        for source in coordinated:
            with self.subTest(source=source):
                self.assertEqual(
                    tuple(item.polarity for item in parse(source)),
                    ("negative", "positive"),
                )

        separate_negated_clause = (
            "There is no requirement to delay the repository review; prepare "
            "a repository release checklist."
        )
        self.assertEqual(
            tuple(item.polarity for item in parse(separate_negated_clause)),
            ("positive",),
        )

    def test_release_structural_scanner_fails_closed_for_unclosed_containers(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        unclosed = (
            "```text\nPrepare a repository release checklist",
            "`Prepare a repository release packet",
            '"Prepare a repository release packet',
            "“Prepare a repository release checklist",
            "'Prepare a repository release packet",
            "    Prepare a repository release checklist",
        )
        for source in unclosed:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].discourse_role, "reference")

        escaped = (
            '"Prepare a repository release packet with \\"quoted\\" metadata"'
        )
        self.assertEqual(parse(escaped)[0].discourse_role, "reference")

        closed = (
            "`Prepare a repository release packet` "
            "Prepare a repository release checklist."
        )
        self.assertEqual(
            tuple(item.discourse_role for item in parse(closed)),
            ("reference", "request"),
        )

    def test_release_tilde_fences_are_global_and_bounded(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        references = (
            "~~~\nPrepare a repository release checklist\n~~~",
            "~~~text\nPrepare a repository release packet\n~~~",
            "~~~ python\nPrepare a repository release checklist",
        )
        for source in references:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].discourse_role, "reference")

        mixed = (
            "~~~text\nPrepare a repository release packet\n~~~\n"
            "Prepare a repository release checklist."
        )
        self.assertEqual(
            tuple(item.discourse_role for item in parse(mixed)),
            ("reference", "request"),
        )
        saturated = (
            ("~~~x~~~ " * 256)
            + "Prepare a repository release checklist."
        )
        self.assertFalse(
            any(item.discourse_role == "request" for item in parse(saturated))
        )

    def test_release_chinese_morphology_is_exact(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        controls = (
            "准备仓库发布清单化。",
            "准备度发布清单。",
            "审查度软件包发布清单。",
            "仓库发布清单准备完成。",
            "准备工作涉及仓库发布清单。",
            "准备阶段包含仓库发布清单。",
            "仓库准备性发布清单。",
            "仓库准备项发布清单。",
            "审查仓库未发布清单。",
            "准备仓库不发布清单。",
            "审查仓库发布清单项。",
            "审查仓库发布清单条目。",
            "审查仓库发布清单字段。",
            "审查仓库发布清单记录。",
            "仓库准备流程和发布清单。",
            "仓库准备事项和发布清单。",
            "记录仓库已发布清单。",
            "仓库审查报告包含发布清单。",
            "仓库记录中的发布清单。",
        )
        for source in controls:
            with self.subTest(source=source):
                self.assertEqual(parse(source), ())

        positives = (
            "准备仓库发布清单。",
            "审查软件包发布清单。",
            "生成维护者发布清单。",
        )
        for source in positives:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].polarity, "positive")
                self.assertEqual(propositions[0].discourse_role, "request")

    def test_release_reporting_discourse_applies_to_whole_sentence(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        references = (
            "The example says to prepare a repository release packet and review "
            "the release checklist for v1.0.",
            "The documentation tells us to prepare a repository release packet, "
            "then review the release checklist for v1.0.",
            "The docs ask us to prepare a repository release packet and review "
            "the release checklist for v1.0.",
            "The guide asks you to prepare a repository release packet and review "
            "the release checklist for v1.0.",
            "E.g., prepare a repository release packet and review the release "
            "checklist for v1.0.",
            "I.e., prepare a repository release packet and review the release "
            "checklist for v1.0.",
        )
        for source in references:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 2)
                self.assertTrue(
                    all(item.discourse_role == "reference" for item in propositions)
                )

        source = references[0] + " Prepare a repository release checklist."
        self.assertEqual(
            tuple(item.discourse_role for item in parse(source)),
            ("reference", "reference", "request"),
        )
        ordinary_docs_request = (
            "Prepare a repository release checklist and write the documentation."
        )
        self.assertEqual(
            tuple(item.discourse_role for item in parse(ordinary_docs_request)),
            ("request",),
        )

    def test_reported_speech_reference_is_proposition_local(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        references = (
            "The report says to prepare a repository release checklist.",
            "Instruction says prepare a repository release checklist.",
            "The report tells us to review the release checklist for v1.0.",
            'The report says "Prepare a repository release checklist."',
            '"Prepare a repository release checklist," the report says.',
        )
        for source in references:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].discourse_role, "reference")

        independent = (
            "The report says tests passed; prepare a repository release checklist.",
            "The report says tests passed; so prepare a repository release "
            "checklist.",
            "The report says tests passed. So prepare a repository release "
            "checklist.",
            "The report says tests passed; therefore prepare a repository release "
            "checklist.",
            "Prepare a repository release checklist; the report says tests passed.",
            "The report says tests passed, but prepare a repository release "
            "checklist.",
            "Prepare a repository release checklist, and the report says tests "
            "passed.",
            "The report says tests passed, so prepare a repository release "
            "checklist.",
            "The report says tests passed and now prepare a repository release "
            "checklist.",
            "According to the report, tests passed, so prepare a repository release "
            "checklist.",
            "The report says code review passed, so prepare a repository release "
            "checklist.",
            "The report says to prepare a migration plan, so prepare a repository "
            "release checklist.",
        )
        for source in independent:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].polarity, "positive")
                self.assertEqual(propositions[0].discourse_role, "request")

        invalid_governed_candidates = (
            "The report says to review a talent release packet, so prepare a "
            "repository release checklist.",
            "The report says not to prepare a repository release packet, so prepare "
            "a repository release checklist.",
            "The report says `prepare a repository release packet`, so prepare a "
            "repository release checklist.",
            "The report says to review a model release packet, therefore review the "
            "release checklist for v1.0.",
            "The report says to review a talent release packet, so inspect assets, "
            "and now prepare a repository release checklist.",
            "The report says to prepare a repository release packet, so inspect "
            "assets, and now prepare a repository release checklist.",
            "The report says to review a talent release packet for repository "
            "maintainers, so prepare a repository release checklist.",
            "The report says to review a content release packet for a software "
            "repository, therefore prepare a repository release checklist.",
            "The report says to review a talent authorization release packet for "
            "repository maintainers, so prepare a repository release checklist.",
            "The report says to review a model photography release packet for a "
            "software repository, therefore prepare a repository release checklist.",
            "The report says to review a content licensing release packet for a "
            "software repository, so prepare a repository release checklist.",
            "The report says to review a model's release packet for a software "
            "repository, therefore prepare a repository release checklist.",
            "The report says to review a content package release packet for a "
            "campaign, so prepare a repository release checklist.",
            "The report says to review a talent package release packet for "
            "repository maintainers, therefore prepare a repository release "
            "checklist.",
            "The report says to review repository code and review a talent release "
            "packet for v1.0, so prepare a repository release checklist.",
            "The report says to review a content-management release packet for a "
            "campaign package while reviewing repository code, so prepare a "
            "repository release checklist.",
            "The report says to review a model-serving release packet for a "
            "photography package while auditing software code, so prepare a "
            "repository release checklist.",
            "The report says to review a content-management release packet for a "
            "campaign package after reviewing repository code, so prepare a "
            "repository release checklist.",
            "The report says to review a content-management release packet for "
            "campaign material following repository code review, so prepare a "
            "repository release checklist.",
            "The report says to review a content-management release packet for "
            "Python package campaign, so prepare a repository release checklist.",
        )
        for source in invalid_governed_candidates:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 2)
                self.assertEqual(
                    tuple(item.discourse_role for item in propositions),
                    ("reference", "request"),
                )

        quoted_then_request = (
            'The report says "Prepare a repository release packet"; review the '
            "release checklist for v1.0."
        )
        self.assertEqual(
            tuple(item.discourse_role for item in parse(quoted_then_request)),
            ("reference", "request"),
        )

    def test_reported_instruction_spans_cover_only_governed_coordinates(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        governed = (
            "The report says to prepare a repository release packet and review "
            "the release checklist for v1.0.",
            "The report says to prepare a repository release packet and now review "
            "the release checklist for v1.0.",
            "The report says to prepare a repository release packet, and now review "
            "the release checklist for v1.0.",
            "The report says to prepare a repository release packet, then review "
            "the release checklist for v1.0.",
            "The documentation tells maintainers to prepare a repository release "
            "packet, then review the release checklist and audit repository "
            "release readiness.",
            "The report says that maintainers should prepare a repository release "
            "packet and review the release checklist for v1.0.",
            "The report says prepare a repository release packet and review the "
            "release checklist for v1.0.",
            "Instruction says prepare a repository release packet, then review "
            "the release checklist for v1.0.",
            "The instruction tells maintainers prepare a repository release "
            "packet, then review the release checklist for v1.0.",
            "The docs ask prepare a repository release packet and audit repository "
            "release readiness.",
            "The report states that maintainers should prepare a repository release "
            "packet and review the release checklist for v1.0.",
            "The report recommends that maintainers prepare a repository release "
            "packet and review the release checklist for v1.0.",
            "According to the report, prepare a repository release packet and review "
            "the release checklist for v1.0.",
            "The guide instructs maintainers to prepare a repository release packet "
            "and review the release checklist for v1.0.",
            "According to the report, the team should prepare a repository release "
            "packet and review the release checklist for v1.0.",
            "The report states that the team should prepare a repository release "
            "packet and review the release checklist for v1.0.",
            "The report recommends that the maintainers prepare a repository release "
            "packet and review the release checklist for v1.0.",
            "The guide instructs the team to prepare a repository release packet and "
            "review the release checklist for v1.0.",
            "Documentation requires the maintainers to prepare a repository release "
            "packet and review the release checklist for v1.0.",
            "The report says that the release team should prepare a repository "
            "release packet and review the release checklist for v1.0.",
            "The docs ask the maintainers to prepare a repository release packet and "
            "review the release checklist for v1.0.",
        )
        for source in governed:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertIn(len(propositions), (2, 3))
                self.assertTrue(
                    all(item.discourse_role == "reference" for item in propositions)
                )

        boundaries = (
            (
                "The report says to prepare a repository release packet; "
                "independently prepare a repository release checklist.",
                ("reference", "request"),
            ),
            (
                "The report says to prepare a repository release packet, but "
                "prepare an actual maintainer release checklist.",
                ("reference", "request"),
            ),
            (
                "The report says to prepare a repository release packet; however, "
                "prepare a maintainer release checklist.",
                ("reference", "request"),
            ),
            (
                "The report says to prepare a repository release packet，但是准备"
                "仓库发布清单。",
                ("reference", "request"),
            ),
            (
                "The report says prepare a repository release packet; prepare a "
                "maintainer release checklist.",
                ("reference", "request"),
            ),
            (
                "The instruction tells maintainers prepare a repository release "
                "packet, but review the actual maintainer release checklist.",
                ("reference", "request"),
            ),
            (
                "The report states that maintainers should prepare a repository "
                "release packet; prepare a maintainer release checklist.",
                ("reference", "request"),
            ),
            (
                "The guide instructs maintainers to prepare a repository release "
                "packet, but review the actual maintainer release checklist.",
                ("reference", "request"),
            ),
            (
                "The report states that the team should prepare a repository release "
                "packet; prepare a maintainer release checklist.",
                ("reference", "request"),
            ),
            (
                "The report states that the senior release engineering team should "
                "prepare a repository release packet; prepare a maintainer release "
                "checklist.",
                ("reference", "request"),
            ),
            (
                "The guide instructs the senior release engineering team to prepare "
                "a repository release packet, but review the actual maintainer "
                "release checklist.",
                ("reference", "request"),
            ),
            (
                "The report states that the senior release engineering team should "
                "prepare a repository release packet. Prepare a maintainer release "
                "checklist.",
                ("reference", "request"),
            ),
        )
        for source, expected in boundaries:
            with self.subTest(source=source):
                self.assertEqual(
                    tuple(item.discourse_role for item in parse(source)),
                    expected,
                )

        overlong = (
            "The report states that the senior release engineering team should "
            "prepare a repository release packet and review the release checklist "
            "for v1.0.",
            "The guide instructs the senior release engineering team to prepare a "
            "repository release packet and review the release checklist for v1.0.",
        )
        for source in overlong:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 2)
                self.assertTrue(
                    all(item.discourse_role == "reference" for item in propositions)
                )
                spans = module._narrative_instruction_reference_spans(
                    source, module._sentence_boundaries(source)
                )
                self.assertEqual(len(spans), 1)
                self.assertLessEqual(spans[0][1], len(source))

    def test_release_sentence_discourse_role_covers_coordinated_propositions(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        references = (
            "Example: prepare a repository release packet and review the "
            "release checklist for v1.0.",
            "For example, prepare a repository release packet, then review "
            "the release checklist for v1.0.",
            "Reference: prepare a repository release packet but review the "
            "release checklist for v1.0.",
            "We discussed whether to prepare a repository release packet and "
            "review the release checklist for v1.0.",
            "Hypothetically, prepare a repository release packet and review "
            "the release checklist for v1.0.",
            "If authorized, prepare a repository release packet and review "
            "the release checklist for v1.0.",
            "# Prepare a repository release packet and review the release "
            "checklist for v1.0.",
            "> Prepare a repository release packet and review the release "
            "checklist for v1.0.",
        )
        for source in references:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 2)
                self.assertTrue(
                    all(item.discourse_role == "reference" for item in propositions)
                )

        request = (
            "Prepare a repository release packet and review the release "
            "checklist for v1.0."
        )
        self.assertTrue(
            all(item.discourse_role == "request" for item in parse(request))
        )

    def test_release_structural_reference_spans_are_global_and_bounded(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        references = (
            '"Prepare a repository\nrelease packet"',
            "“Prepare a repository\nrelease checklist”",
            "'Prepare a repository\nrelease packet'",
            "`Prepare a repository release packet`",
            "```text\nPrepare a repository release checklist\n```",
            "[Prepare a repository release checklist]",
            "[Prepare a repository release packet](docs/release.md)",
            "<h2>Prepare a repository release checklist</h2>",
            "<code>Prepare a repository release packet</code>",
            "<pre>Prepare a repository release checklist</pre>",
            "<pre class=\"example\">Prepare a repository release checklist",
        )
        for source in references:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 1)
                self.assertEqual(propositions[0].discourse_role, "reference")

        mixed = (
            '"Prepare a repository release packet." Prepare a repository '
            "release checklist."
        )
        self.assertEqual(
            tuple(item.discourse_role for item in parse(mixed)),
            ("reference", "request"),
        )
        link_target = (
            "[instructions](prepare-a-repository-release-packet) and prepare "
            "a repository release checklist."
        )
        self.assertEqual(
            sum(item.discourse_role == "request" for item in parse(link_target)),
            1,
        )
        saturated = (
            ("`x` " * 256)
            + "Prepare a repository release checklist."
        )
        self.assertFalse(
            any(item.discourse_role == "request" for item in parse(saturated))
        )
        pre_mixed = (
            "<pre>Prepare a repository release packet</pre> "
            "Prepare a repository release checklist."
        )
        self.assertEqual(
            tuple(item.discourse_role for item in parse(pre_mixed)),
            ("reference", "request"),
        )
        overlapping_pre = (
            "<pre>`Prepare a repository release packet`</pre> "
            "Prepare a repository release checklist."
        )
        self.assertEqual(
            tuple(item.discourse_role for item in parse(overlapping_pre)),
            ("reference", "request"),
        )
        saturated_pre = (
            ("<pre>x</pre>" * 256)
            + "Prepare a repository release checklist."
        )
        self.assertFalse(
            any(item.discourse_role == "request" for item in parse(saturated_pre))
        )

    def test_release_tokens_are_unicode_exact_and_fullwidth_boundaries_are_hard(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        controls = (
            "Prepare a repository xrelease checklist.",
            "Prepare a repository release checklist_legacy.",
            "Prepare a repository αrelease checklist.",
            "Prepare a repository release checklist界.",
        )
        for source in controls:
            with self.subTest(source=source):
                self.assertEqual(parse(source), ())

        source = (
            "Cannot prepare a repository release packet！"
            "Prepare a repository release checklist？"
        )
        self.assertEqual(
            tuple(item.polarity for item in parse(source)),
            ("negative", "positive"),
        )
        no_space = (
            "Cannot prepare a repository release packet."
            "Prepare a repository release checklist."
        )
        self.assertEqual(
            tuple(item.polarity for item in parse(no_space)),
            ("negative", "positive"),
        )

    def test_chinese_full_stops_are_hard_release_sentence_boundaries(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        references = (
            "前置说明。Example: prepare a repository release packet; review "
            "the release checklist for v1.0。",
            "前置说明。。Example: prepare a repository release packet; review "
            "the release checklist for v1.0。。",
            "前置说明。Example: 准备仓库发布清单; review the repository release "
            "checklist for v1.0。",
        )
        for source in references:
            with self.subTest(source=source):
                propositions = parse(source)
                self.assertEqual(len(propositions), 2)
                self.assertTrue(
                    all(item.discourse_role == "reference" for item in propositions)
                )

        true_requests = (
            references[0] + " Prepare a repository release checklist.",
            references[0] + "准备仓库发布清单。",
        )
        for source in true_requests:
            with self.subTest(source=source):
                self.assertEqual(
                    tuple(item.discourse_role for item in parse(source)),
                    ("reference", "reference", "request"),
                )

    def test_release_readiness_proposition_parser_is_bounded_and_total(self):
        module = importlib.import_module(
            "onecode_skill_sanitizer.release_propositions"
        )
        parse = module.parse_release_readiness_propositions
        proposition_type = module.ReleaseReadinessProposition
        command = "Prepare a repository release packet."

        self.assertEqual(parse("x" * 20_000 + command), ())
        exact = "x" * (20_000 - len(command)) + command
        self.assertEqual(len(parse(exact)), 1)
        repeated = " ".join([command] * 256)
        self.assertEqual(len(parse(repeated)), 128)
        for source in ("", "\u0000", "“", "'", "release", "发布"):
            with self.subTest(source=source):
                self.assertIsInstance(parse(source), tuple)

        proposition = proposition_type(0, 1, "prepare", "x", "positive", "request")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            proposition.action = "review"

    def test_release_readiness_evidence_accepts_explicit_packet_requests(self):
        cases = (
            (
                "Prepare a maintainer-ready release packet for a CLI project, "
                "including reproducible checks, provenance, and an explicit "
                "go/no-go decision.",
                ("release",),
            ),
            (
                "Release readiness has two independent evidence streams: "
                "licensed media provenance and a sensitive-history repository audit.",
                ("release",),
            ),
        )

        for source, matched_signals in cases:
            with self.subTest(source=source):
                self.assertTrue(
                    source_supports_release_readiness(source, matched_signals)
                )

    def test_release_readiness_evidence_rejects_non_request_noun_contexts(self):
        cases = (
            ("release.md", ("release",)),
            ("Navigation heading: Public Release", ("release",)),
            ("Review the talent release for a model", ("release",)),
            (
                '"Prepare a repository release packet" is quoted reference text.',
                ("release",),
            ),
            ("Example: prepare a repository release packet.", ("release",)),
            (
                "Hypothetically, prepare a release packet for the repository.",
                ("release",),
            ),
            ("An unauthorized repository release packet is attached.", ("release",)),
            ("A stale maintainer-ready release packet claims approval.", ("release",)),
            (
                "Must not publish a repository release packet.",
                ("release",),
            ),
            (
                "Security audit text mentions a repository release packet; inspect only.",
                ("release",),
            ),
        )

        for source, matched_signals in cases:
            with self.subTest(source=source):
                self.assertFalse(
                    source_supports_release_readiness(source, matched_signals)
                )

    def test_release_readiness_context_is_scoped_to_its_local_segment(self):
        cases = (
            "Audit unauthorized access; prepare a repository release packet.",
            "Prepare a repository release packet; audit unauthorized access.",
            "Audit unauthorized access and prepare a repository release packet.",
            "Prepare a repository release packet and audit unauthorized access.",
            "Remove stale cache, then prepare a maintainer-ready release packet.",
            "Remove stale cache, and then prepare a maintainer-ready release packet.",
            "Prepare package release readiness checks, then remove stale cache.",
            "Must not delete old artifacts; prepare a repository release checklist.",
            "清理过期缓存；然后 prepare a repository release packet.",
            "Prepare a repository release packet。然后清理过期缓存。",
            "Prepare a repository release packet documenting stale artifacts.",
            "Prepare a repository release packet without publishing it.",
        )

        for source in cases:
            with self.subTest(source=source):
                self.assertTrue(
                    source_supports_release_readiness(source, ("release",))
                )

    def test_release_readiness_rejects_locally_negated_actions(self):
        cases = (
            "Must not prepare a repository release packet.",
            "Mustn't approve a repository release packet.",
            "Should not prepare a repository release checklist.",
            "Shouldn't approve package release readiness.",
            "Do not release the repository release readiness packet.",
            "Don't prepare a release checklist.",
            "Never prepare a maintainer-ready release packet.",
            "Do not claim release readiness.",
            "Release readiness is not approved.",
        )

        for source in cases:
            with self.subTest(source=source):
                self.assertFalse(
                    source_supports_release_readiness(
                        source, ("release",), polarity="negative"
                    )
                )

    def test_release_readiness_uses_syntax_and_software_context_controls(self):
        negative_cases = (
            '"Prepare a repository release packet"',
            "'Prepare a repository release packet'",
            "“Prepare a repository release checklist”",
            "# Release readiness",
            "> Release readiness",
            "- [ ] Prepare a repository release checklist",
            "<h2>Release checklist</h2>",
            "Navigation: Release readiness",
            "Title: Release readiness",
            "Release readiness.md",
            "release_packet.yaml",
            "release-checklist.json",
            "Example: prepare a repository release checklist",
            "- Release checklist",
            "Prepare a talent release packet for a photo shoot",
            "Prepare a model release packet for the photographer",
            "Prepare a content release packet for the campaign",
        )
        positive_cases = (
            "Prepare a repository release checklist.",
            "Prepare package release readiness checks.",
            "Prepare a maintainer-ready release packet.",
            "Prepare a release packet for the CLI repository.",
        )

        for source in negative_cases:
            with self.subTest(source=source):
                self.assertFalse(
                    source_supports_release_readiness(source, ("release",))
                )
        for source in positive_cases:
            with self.subTest(source=source):
                self.assertTrue(
                    source_supports_release_readiness(source, ("release",))
                )

    def test_standalone_bare_release_actions_are_canonical(self):
        for task in ("release", "publish", "push", "发布", "上线", "推送"):
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertEqual(
                    [intent.task_type for intent in graph.intents],
                    ["open_source_release"],
                )
                self.assertEqual(graph.intent_evidence[0].release_mode, "action")
                self.assertEqual(graph.validate(), [])

    def test_negated_bare_release_actions_remain_nonaction(self):
        for task in ("do not release", "不要发布"):
            with self.subTest(task=task):
                graph = decompose_task(task)
                self.assertNotIn(
                    "open_source_release",
                    [intent.task_type for intent in graph.intents],
                )
                self.assertFalse(
                    any(
                        item.release_mode == "action"
                        for item in graph.intent_evidence
                    )
                )

    def test_nonempty_evidence_requires_exact_nonblank_source_and_provenance(self):
        class StringSubclass(str):
            pass

        evidence = IntentEvidence(
            "general", "action", "positive", "none", "single", (), 0
        )
        invalid_sources = (None, [], 1, {}, "", " ", StringSubclass("task"))
        invalid_provenance = (
            None,
            [],
            1,
            {},
            "",
            " ",
            StringSubclass("provenance"),
        )

        for source in invalid_sources:
            with self.subTest(source=source):
                errors = validate_intent_evidence(
                    (dataclasses.replace(evidence, provenance="valid"),),
                    ("general",),
                    source,
                )
                self.assertTrue(any("source" in error for error in errors), errors)
        for provenance in invalid_provenance:
            with self.subTest(provenance=provenance):
                errors = validate_intent_evidence(
                    (dataclasses.replace(evidence, provenance=provenance),),
                    ("general",),
                    "general task",
                )
                self.assertTrue(
                    any("provenance" in error for error in errors), errors
                )

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

    def test_canonical_relations_reject_injection_deletion_and_reason_changes(self):
        plain = decompose_task("code review + analyze a spreadsheet")
        injected_relation = IntentRelation(
            "i1", "i2", "explicit_sequence", False
        )
        injected = dataclasses.replace(
            plain,
            intents=(
                plain.intents[0],
                dataclasses.replace(plain.intents[1], depends_on=("i1",)),
            ),
            dependency_relations=(injected_relation,),
            intent_evidence=bind_intent_evidence(
                plain.intent_evidence, plain.evidence_source
            ),
        )
        injected_release = dataclasses.replace(
            plain,
            intents=(
                plain.intents[0],
                dataclasses.replace(plain.intents[1], depends_on=("i1",)),
            ),
            dependency_relations=(
                IntentRelation("i1", "i2", "release_gate", True),
            ),
        )

        sequence = decompose_task("code review then build a website")
        deleted = dataclasses.replace(
            sequence,
            intents=(
                sequence.intents[0],
                dataclasses.replace(sequence.intents[1], depends_on=()),
            ),
            dependency_relations=(),
        )
        changed = dataclasses.replace(
            sequence,
            dependency_relations=(
                IntentRelation("i1", "i2", "before", False),
            ),
        )
        release_sequence = decompose_task(
            "code review then build a website then publish update"
        )
        duplicated = dataclasses.replace(
            release_sequence,
            dependency_relations=(
                *release_sequence.dependency_relations,
                release_sequence.dependency_relations[0],
            ),
        )
        reordered = dataclasses.replace(
            release_sequence,
            dependency_relations=tuple(
                reversed(release_sequence.dependency_relations)
            ),
        )

        for graph in (
            injected,
            injected_release,
            deleted,
            changed,
            duplicated,
            reordered,
        ):
            with self.subTest(relations=graph.dependency_relations):
                self.assertTrue(graph.validate())

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

    def test_normalize_task_strips_padding_but_preserves_indented_code(self):
        self.assertEqual(
            normalize_task("  audit the skill router  \n").current,
            "audit the skill router",
        )
        self.assertEqual(
            normalize_task(
                "    Prepare a repository release checklist  \n"
            ).current,
            "    Prepare a repository release checklist",
        )

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
