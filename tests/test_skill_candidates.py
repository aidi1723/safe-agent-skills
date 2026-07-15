from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from onecode_skill_sanitizer.intent import NormalizedTask, normalize_task
from onecode_skill_sanitizer.need_gate import decide_skill_need
from onecode_skill_sanitizer.skill_candidates import (
    HIGH_FREQUENCY_ENTRY_NAMES,
    HIGH_FREQUENCY_SKILL_NAMES,
    RoutingExampleError,
    load_cohort_profiles,
    load_routing_examples,
    retrieve_skill_candidates,
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

    def test_profiles_come_only_from_trusted_catalog_sources(self):
        profiles = load_cohort_profiles(ROOT / "catalog")

        self.assertEqual(tuple(profiles), HIGH_FREQUENCY_SKILL_NAMES)
        self.assertTrue(all(profile["status"] == "trusted" for profile in profiles.values()))
        self.assertTrue(all(profile["description"].startswith("Use when") for profile in profiles.values()))
        self.assertTrue(all(profile["capabilities"] for profile in profiles.values()))

    def test_profile_loader_rejects_unsafe_or_non_normalized_registry_paths(self):
        cases = {
            "empty": "",
            "absolute": "/tmp/code-review-risk",
            "traversal": "../outside",
            "dot component": "./code/code-review-risk",
            "parent component": "code/temporary/../code-review-risk",
            "wrong basename": "code/review-risk",
        }
        for label, registry_path in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                catalog, index = self._copy_cohort_catalog(temp_dir)
                self._cohort_entry(index, "code-review-risk")["registry_path"] = registry_path
                self._write_json(catalog / "index.json", index)

                self._assert_routing_error(
                    lambda: load_cohort_profiles(catalog),
                    r"code-review-risk.*registry_path",
                )

    def test_profile_loader_rejects_only_symlinks_that_escape_catalog(self):
        for source_name in ("skill directory", "skill.json", "SKILL.md"):
            with self.subTest(source_name=source_name), tempfile.TemporaryDirectory() as temp_dir:
                catalog, _ = self._copy_cohort_catalog(temp_dir)
                skill_dir = catalog / "code/code-review-risk"
                outside = Path(temp_dir) / "outside"
                outside.mkdir()
                if source_name == "skill directory":
                    shutil.copytree(skill_dir, outside / "skill")
                    shutil.rmtree(skill_dir)
                    skill_dir.symlink_to(outside / "skill", target_is_directory=True)
                else:
                    shutil.copy2(skill_dir / source_name, outside / source_name)
                    (skill_dir / source_name).unlink()
                    (skill_dir / source_name).symlink_to(outside / source_name)

                self._assert_routing_error(
                    lambda: load_cohort_profiles(catalog),
                    r"code-review-risk.*(?:path|source)",
                )

        for source_name in ("skill.json", "SKILL.md"):
            with self.subTest(internal_source=source_name), tempfile.TemporaryDirectory() as temp_dir:
                catalog, _ = self._copy_cohort_catalog(temp_dir)
                skill_dir = catalog / "code/code-review-risk"
                alias_dir = catalog / "aliases"
                alias_dir.mkdir()
                shutil.copy2(skill_dir / source_name, alias_dir / source_name)
                (skill_dir / source_name).unlink()
                (skill_dir / source_name).symlink_to(alias_dir / source_name)

                self.assertEqual(
                    load_cohort_profiles(catalog)["code-review-risk"]["name"],
                    "code-review-risk",
                )

    def test_profile_loader_cross_checks_index_manifest_and_frontmatter_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            catalog, index = self._copy_cohort_catalog(temp_dir)
            index["skills"].append(json.loads(json.dumps(self._cohort_entry(index, "code-review-risk"))))
            self._write_json(catalog / "index.json", index)
            self._assert_routing_error(
                lambda: load_cohort_profiles(catalog),
                r"duplicate.*code-review-risk",
            )

        index_cases = {
            "untrusted index": ("status", "review_required"),
            "other cohort directory": ("registry_path", "code/code-test-regression"),
        }
        for label, (field, value) in index_cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                catalog, index = self._copy_cohort_catalog(temp_dir)
                self._cohort_entry(index, "code-review-risk")[field] = value
                self._write_json(catalog / "index.json", index)
                self._assert_routing_error(
                    lambda: load_cohort_profiles(catalog),
                    r"code-review-risk.*(?:trusted|registry_path)",
                )

        manifest_cases = {
            "manifest name": ("name", "safe-agent-router"),
            "manifest status": ("status", "review_required"),
        }
        for label, (field, value) in manifest_cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                catalog, _ = self._copy_cohort_catalog(temp_dir)
                manifest_path = catalog / "code/code-review-risk/skill.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest[field] = value
                self._write_json(manifest_path, manifest)
                self._assert_routing_error(
                    lambda: load_cohort_profiles(catalog),
                    rf"code-review-risk.*manifest.*{field}",
                )

        for frontmatter_name in ("safe-agent-router", None):
            with self.subTest(frontmatter_name=frontmatter_name), tempfile.TemporaryDirectory() as temp_dir:
                catalog, _ = self._copy_cohort_catalog(temp_dir)
                skill_path = catalog / "code/code-review-risk/SKILL.md"
                lines = skill_path.read_text(encoding="utf-8").splitlines()
                lines = [
                    f"name: {frontmatter_name}" if line.startswith("name:") else line
                    for line in lines
                    if frontmatter_name is not None or not line.startswith("name:")
                ]
                skill_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                self._assert_routing_error(
                    lambda: load_cohort_profiles(catalog),
                    r"code-review-risk.*frontmatter.*name",
                )

        for description in ("", None):
            with self.subTest(description=description), tempfile.TemporaryDirectory() as temp_dir:
                catalog, _ = self._copy_cohort_catalog(temp_dir)
                skill_path = catalog / "code/code-review-risk/SKILL.md"
                lines = skill_path.read_text(encoding="utf-8").splitlines()
                lines = [
                    f"description: {description or ''}" if line.startswith("description:") else line
                    for line in lines
                    if description is not None or not line.startswith("description:")
                ]
                skill_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                self._assert_routing_error(
                    lambda: load_cohort_profiles(catalog),
                    r"code-review-risk.*frontmatter.*description",
                )

    def test_profile_loader_rejects_malformed_index_and_manifest_contracts(self):
        index_cases = (
            ("index object", []),
            ("index skills", {"skills": "not-a-list"}),
            ("index entry", {"skills": ["not-an-object"]}),
        )
        for label, payload in index_cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                catalog, _ = self._copy_cohort_catalog(temp_dir)
                self._write_json(catalog / "index.json", payload)
                self._assert_routing_error(
                    lambda: load_cohort_profiles(catalog),
                    r"index",
                )

        manifest_cases = (
            ("manifest object", (), []),
            ("taxonomy object", ("taxonomy",), []),
            ("taxonomy task_intent", ("taxonomy", "task_intent"), " "),
            ("taxonomy subcategory", ("taxonomy", "subcategory"), 1),
            ("contract object", ("contract",), []),
            ("contract schema bool", ("contract", "schema_version"), True),
            ("contract schema version", ("contract", "schema_version"), 1),
            ("capability list", ("contract", "capability_vector"), "code.review"),
            ("capability empty", ("contract", "capability_vector"), []),
            ("capability blank", ("contract", "capability_vector"), [" "]),
            ("capability duplicate", ("contract", "capability_vector"), ["code.review", "code.review"]),
        )
        for label, path, value in manifest_cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                catalog, _ = self._copy_cohort_catalog(temp_dir)
                manifest_path = catalog / "code/code-review-risk/skill.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if path:
                    target = manifest
                    for part in path[:-1]:
                        target = target[part]
                    target[path[-1]] = value
                else:
                    manifest = value
                self._write_json(manifest_path, manifest)
                self._assert_routing_error(
                    lambda: load_cohort_profiles(catalog),
                    r"code-review-risk.*manifest",
                )

        optional_fields = (
            "requires_context",
            "produces_artifacts",
            "produces_evidence",
            "requires_after",
            "conflicts_with",
            "excludes",
        )
        for field in optional_fields:
            for value in ("not-a-list", [""], ["duplicate", "duplicate"]):
                with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as temp_dir:
                    catalog, _ = self._copy_cohort_catalog(temp_dir)
                    manifest_path = catalog / "code/code-review-risk/skill.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest["contract"][field] = value
                    self._write_json(manifest_path, manifest)
                    self._assert_routing_error(
                        lambda: load_cohort_profiles(catalog),
                        rf"code-review-risk.*{field}",
                    )

        with tempfile.TemporaryDirectory() as temp_dir:
            catalog, _ = self._copy_cohort_catalog(temp_dir)
            manifest_path = catalog / "code/code-review-risk/skill.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for field in optional_fields:
                manifest["contract"].pop(field, None)
            self._write_json(manifest_path, manifest)
            profile = load_cohort_profiles(catalog)["code-review-risk"]
            self.assertTrue(all(profile[field] == [] for field in optional_fields))

    def test_profile_loader_wraps_missing_and_invalid_source_files(self):
        cases = ("index invalid JSON", "index missing", "manifest invalid JSON", "manifest missing", "skill missing")
        for label in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                catalog, _ = self._copy_cohort_catalog(temp_dir)
                if label == "index invalid JSON":
                    (catalog / "index.json").write_text("{", encoding="utf-8")
                elif label == "index missing":
                    (catalog / "index.json").unlink()
                elif label == "manifest invalid JSON":
                    (catalog / "code/code-review-risk/skill.json").write_text("{", encoding="utf-8")
                elif label == "manifest missing":
                    (catalog / "code/code-review-risk/skill.json").unlink()
                else:
                    (catalog / "code/code-review-risk/SKILL.md").unlink()

                self._assert_routing_error(
                    lambda: load_cohort_profiles(catalog),
                    r"(?:index|code-review-risk.*(?:manifest|SKILL\.md))",
                )

    def test_retrieval_returns_top_three_with_decomposed_evidence(self):
        task = normalize_task("review this patch and add a regression test")
        need = decide_skill_need(task)
        candidates = retrieve_skill_candidates(
            task,
            need,
            load_cohort_profiles(ROOT / "catalog"),
            load_routing_examples(EXAMPLES),
            top_k=3,
        )

        self.assertEqual([item["skill"] for item in candidates[:2]], ["code-review-risk", "code-test-regression"])
        self.assertTrue(all(0 <= item["deterministic_score"] <= 1 for item in candidates))
        self.assertTrue(all(item["positive_evidence"] for item in candidates[:2]))
        self.assertIn("code.review", candidates[0]["matched_capabilities"])

    def test_near_miss_and_explicit_exclusion_cannot_win(self):
        task = normalize_task("Do not critique design; run the existing UI flow in a browser")
        need = decide_skill_need(task)
        candidates = retrieve_skill_candidates(
            task,
            need,
            load_cohort_profiles(ROOT / "catalog"),
            load_routing_examples(EXAMPLES),
            top_k=3,
        )
        by_name = {item["skill"]: item for item in candidates}

        self.assertEqual(candidates[0]["skill"], "execution-browser-check")
        self.assertTrue(by_name["design-ui-review"]["excluded"])
        self.assertIn("explicit_exclusion", by_name["design-ui-review"]["reason_codes"])

    def test_retrieval_rejects_malformed_normalized_task_and_profile_mapping(self):
        task, need, profiles, examples = self._valid_retrieval_inputs()
        malformed_task = NormalizedTask(
            raw="review this patch",
            current=[],
            history="",
            stale="",
            stale_policy="",
        )
        self._assert_routing_error(
            lambda: retrieve_skill_candidates(malformed_task, need, profiles, examples),
            r"normalized\.current",
        )

        mapping_cases = ("not object", "missing", "extra")
        for label in mapping_cases:
            with self.subTest(label=label):
                changed = json.loads(json.dumps(profiles))
                if label == "not object":
                    changed = []
                elif label == "missing":
                    changed.pop("code-review-risk")
                else:
                    changed["safe-agent-router"] = json.loads(
                        json.dumps(changed["code-review-risk"])
                    )
                self._assert_routing_error(
                    lambda: retrieve_skill_candidates(task, need, changed, examples),
                    r"profiles.*fixed cohort",
                )

        profile_cases = (
            ("profile object", (), []),
            ("embedded identity", ("name",), "safe-agent-router"),
            ("status", ("status",), "review_required"),
            ("path escape", ("registry_path",), "../code-review-risk"),
            ("path identity", ("registry_path",), "code/code-test-regression"),
            ("description", ("description",), " "),
            ("task intent", ("task_intent",), 1),
            ("capability type", ("capabilities",), "code.review"),
            ("capability empty", ("capabilities",), []),
            ("capability blank", ("capabilities",), [" "]),
            ("capability duplicate", ("capabilities",), ["code.review", "code.review"]),
            ("capability unknown", ("capabilities",), ["safe-agent-router"]),
        )
        for label, path, value in profile_cases:
            with self.subTest(label=label):
                changed = json.loads(json.dumps(profiles))
                if path:
                    changed["code-review-risk"][path[0]] = value
                else:
                    changed["code-review-risk"] = value
                self._assert_routing_error(
                    lambda: retrieve_skill_candidates(task, need, changed, examples),
                    r"profile code-review-risk",
                )

    def test_retrieval_rejects_malformed_need_contract_but_allows_constraint_overlap(self):
        task, need, profiles, examples = self._valid_retrieval_inputs()
        cases = (
            ("need object", (), []),
            ("required missing", ("required_capabilities",), DELETE),
            ("required type", ("required_capabilities",), "code.review"),
            ("required blank", ("required_capabilities",), [" "]),
            ("required duplicate", ("required_capabilities",), ["code.review", "code.review"]),
            ("required unknown", ("required_capabilities",), ["unknown.capability"]),
            ("explicit type", ("explicit_skills",), "code-review-risk"),
            ("explicit unknown", ("explicit_skills",), ["safe-agent-router"]),
            ("excluded blank", ("excluded_skills",), [" "]),
            ("excluded duplicate", ("excluded_skills",), ["code-review-risk", "code-review-risk"]),
            ("excluded unknown", ("excluded_skills",), ["safe-agent-router"]),
        )
        for label, path, value in cases:
            with self.subTest(label=label):
                changed = json.loads(json.dumps(need))
                if path:
                    if value is DELETE:
                        del changed[path[0]]
                    else:
                        changed[path[0]] = value
                else:
                    changed = value
                self._assert_routing_error(
                    lambda: retrieve_skill_candidates(task, changed, profiles, examples),
                    r"need",
                )

        overlap = json.loads(json.dumps(need))
        overlap["explicit_skills"] = ["code-review-risk"]
        overlap["excluded_skills"] = ["code-review-risk"]
        by_name = {
            item["skill"]: item
            for item in retrieve_skill_candidates(task, overlap, profiles, examples)
        }
        self.assertTrue(by_name["code-review-risk"]["excluded"])

    def test_retrieval_revalidates_caller_supplied_reviewed_examples(self):
        task, need, profiles, examples = self._valid_retrieval_inputs()
        self._assert_routing_error(
            lambda: retrieve_skill_candidates(task, need, profiles, {}),
            r"routing examples must be a list",
        )
        provenance_cases = {
            "status": "draft",
            "reviewer_role": "automated_router",
            "source_classification": "router_output",
            "generated_from_router": True,
        }
        for field, value in provenance_cases.items():
            with self.subTest(field=field):
                changed = json.loads(json.dumps(examples))
                changed[0]["review"][field] = value
                self._assert_routing_error(
                    lambda: retrieve_skill_candidates(task, need, profiles, changed),
                    r"example\[0\]",
                )

    def test_candidate_audit_evidence_is_local_and_reconstructable(self):
        task, need, profiles, examples = self._valid_retrieval_inputs()
        candidates = retrieve_skill_candidates(task, need, profiles, examples)
        by_name = {item["skill"]: item for item in candidates}
        review = by_name["code-review-risk"]
        unrelated = by_name["research-source-check"]

        self.assertEqual(review["matched_intents"], review["matched_capabilities"])
        self.assertEqual(unrelated["matched_capabilities"], ())
        self.assertEqual(unrelated["matched_intents"], ())

        positive = next(
            item for item in review["positive_evidence"] if item["type"] == "reviewed_example"
        )
        penalty = next(item for item in review["penalties"] if item["type"] == "near_miss")
        self.assertEqual(positive["value"], review["matched_examples"][0])
        self.assertEqual(
            positive["contribution"],
            round(positive["weight"] * positive["similarity"], 6),
        )
        self.assertEqual(
            penalty["contribution"],
            round(penalty["weight"] * penalty["similarity"], 6),
        )
        self.assertGreater(positive["similarity"], 0)
        self.assertGreater(penalty["similarity"], 0)

    def test_excluded_zero_score_candidates_sort_after_eligible_ties(self):
        task = normalize_task("别用code-review-risk")
        need = decide_skill_need(task)
        candidates = retrieve_skill_candidates(
            task,
            need,
            load_cohort_profiles(ROOT / "catalog"),
            load_routing_examples(EXAMPLES),
        )
        excluded_position = next(
            index for index, item in enumerate(candidates) if item["skill"] == "code-review-risk"
        )

        self.assertTrue(candidates[excluded_position]["excluded"])
        self.assertGreater(excluded_position, 0)
        self.assertTrue(all(not item["excluded"] for item in candidates[:excluded_position]))

    def _assert_payload_rejected(self, payload):
        with self.assertRaises(RoutingExampleError):
            self._load_temporary_payload(payload)

    def _assert_routing_error(self, callback, pattern):
        try:
            callback()
        except Exception as error:
            self.assertIsInstance(error, RoutingExampleError)
            self.assertRegex(str(error), pattern)
        else:
            self.fail("expected RoutingExampleError")

    def _copy_cohort_catalog(self, temp_dir):
        source_index = json.loads((ROOT / "catalog/index.json").read_text(encoding="utf-8"))
        source_entries = {
            item["name"]: item
            for item in source_index["skills"]
            if item["name"] in HIGH_FREQUENCY_SKILL_NAMES
        }
        index = {
            "skills": [
                json.loads(json.dumps(source_entries[name]))
                for name in HIGH_FREQUENCY_SKILL_NAMES
            ]
        }
        catalog = Path(temp_dir) / "catalog"
        catalog.mkdir()
        for entry in index["skills"]:
            shutil.copytree(
                ROOT / "catalog" / entry["registry_path"],
                catalog / entry["registry_path"],
            )
        self._write_json(catalog / "index.json", index)
        return catalog, index

    @staticmethod
    def _cohort_entry(index, name):
        return next(item for item in index["skills"] if item["name"] == name)

    @staticmethod
    def _write_json(path, payload):
        path.write_text(json.dumps(payload), encoding="utf-8")

    def _load_temporary_payload(self, payload):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "routing-examples.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return load_routing_examples(path)

    @staticmethod
    def _valid_retrieval_inputs():
        task = normalize_task("review this patch and add a regression test")
        return (
            task,
            decide_skill_need(task),
            load_cohort_profiles(ROOT / "catalog"),
            load_routing_examples(EXAMPLES),
        )


if __name__ == "__main__":
    unittest.main()
