import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


LABELING = {
    "method": "manual_review",
    "reviewer_role": "independent_dataset_review",
    "generated_from_router": False,
    "reviewed_at": "2026-07-10",
}


def case(case_id: str, category: str = "normal") -> dict:
    return {
        "id": case_id,
        "category": category,
        "task": f"Task {case_id}",
        "expected_intents": ["research"],
        "expected_scenarios": ["scenario-one"],
        "required_dependency_edges": [],
        "forbidden_scenarios": [],
    }


def canonical_sha256(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


class SuiteFixture:
    def __init__(self, root: Path, cases: list[dict] | None = None):
        self.root = root
        self.cases = cases or [case("normal-001")]
        self.shard_payload = {"cases": self.cases}
        self.shard_path = root / "normal.json"
        self.shard_path.write_text(json.dumps(self.shard_payload), encoding="utf-8")
        self.index_payload = {
            "schema_version": 1,
            "suite_id": "router-production-v1",
            "labeling": LABELING,
            "case_count": len(self.cases),
            "shards": [
                {
                    "path": "normal.json",
                    "case_count": len(self.cases),
                    "sha256": canonical_sha256(self.shard_payload),
                }
            ],
        }
        self.index_path = root / "index.json"
        self.write_index()

    def write_index(self) -> None:
        self.index_path.write_text(json.dumps(self.index_payload), encoding="utf-8")

    def review_payload(self, identity: dict) -> dict:
        return {
            "schema_version": 1,
            "suite_id": identity["suite_id"],
            "suite_sha256": identity["suite_sha256"],
            "reviewed_commit": "c" * 40,
            "rule_author_id": "routing-author",
            "reviewer_id": "independent-reviewer",
            "reviewer_role": "independent_dataset_review",
            "reviewed_at": "2026-07-11T00:00:00Z",
            "decision": "accepted",
            "independence_attestation": True,
            "reviewed_case_ids": [item["id"] for item in self.cases],
            "exceptions": [],
        }


class RouterEvalSuiteTests(unittest.TestCase):
    def load(self, path: Path):
        from onecode_skill_sanitizer.router_eval_review import load_eval_suite

        return load_eval_suite(path, {"scenario-one"})

    def test_missing_index_and_shard_are_rejected(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(DatasetValidationError):
                self.load(root / "missing.json")
            fixture = SuiteFixture(root)
            fixture.shard_path.unlink()
            with self.assertRaises(DatasetValidationError):
                self.load(fixture.index_path)

    def test_strict_index_and_shard_shapes_reject_unknown_or_invalid_fields(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        mutations = (
            lambda fixture: fixture.index_payload.update(extra=True),
            lambda fixture: fixture.index_payload.update(schema_version=2),
            lambda fixture: fixture.index_payload.update(schema_version=True),
            lambda fixture: fixture.index_payload["shards"][0].update(extra=True),
            lambda fixture: fixture.index_payload["shards"][0].update(case_count=True),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                mutate(fixture)
                fixture.write_index()
                with self.assertRaises(DatasetValidationError):
                    self.load(fixture.index_path)

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            fixture.shard_payload["extra"] = True
            fixture.shard_path.write_text(json.dumps(fixture.shard_payload), encoding="utf-8")
            fixture.index_payload["shards"][0]["sha256"] = canonical_sha256(fixture.shard_payload)
            fixture.write_index()
            with self.assertRaises(DatasetValidationError):
                self.load(fixture.index_path)

    def test_strict_parser_rejects_duplicate_keys_and_nonstandard_constants(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            raw_index = json.dumps(fixture.index_payload).replace(
                '"schema_version": 1',
                '"schema_version": 1, "schema_version": 2',
                1,
            )
            fixture.index_path.write_text(raw_index, encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "duplicate"):
                self.load(fixture.index_path)

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            raw_shard = json.dumps(fixture.shard_payload).replace(
                '"id": "normal-001"',
                '"id": "normal-001", "id": "conflicting-id"',
                1,
            )
            fixture.shard_path.write_text(raw_shard, encoding="utf-8")
            with self.assertRaisesRegex(DatasetValidationError, "duplicate"):
                self.load(fixture.index_path)

        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                raw_index = json.dumps(fixture.index_payload).replace(
                    '"case_count": 1',
                    f'"case_count": {constant}',
                    1,
                )
                fixture.index_path.write_text(raw_index, encoding="utf-8")
                with self.assertRaises(DatasetValidationError):
                    self.load(fixture.index_path)

    def test_deep_json_is_normalized_to_dataset_validation_error(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        invalid_documents = (
            "[" * 10_000 + "0" + "]" * 10_000,
            '{"schema_version":' + "1" * 10_000 + "}",
        )
        for document in invalid_documents:
            with self.subTest(prefix=document[:20]), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "index.json"
                path.write_text(document, encoding="utf-8")
                with self.assertRaises(DatasetValidationError):
                    self.load(path)

    def test_shard_paths_must_be_safe_known_relative_files(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        for unsafe in ("../normal.json", "/tmp/normal.json", "unknown.json", "./normal.json"):
            with self.subTest(path=unsafe), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                fixture.index_payload["shards"][0]["path"] = unsafe
                fixture.write_index()
                with self.assertRaises(DatasetValidationError):
                    self.load(fixture.index_path)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlink_and_special_shards_are_rejected(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            target = fixture.root / "target.json"
            fixture.shard_path.rename(target)
            fixture.shard_path.symlink_to(target)
            with self.assertRaises(DatasetValidationError):
                self.load(fixture.index_path)

        if hasattr(os, "mkfifo"):
            with tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                fixture.shard_path.unlink()
                os.mkfifo(fixture.shard_path)
                with self.assertRaises(DatasetValidationError):
                    self.load(fixture.index_path)

    def test_hash_counts_duplicate_ids_and_categories_are_validated(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            fixture.index_payload["shards"][0]["sha256"] = f"sha256:{'0' * 64}"
            fixture.write_index()
            with self.assertRaisesRegex(DatasetValidationError, "hash"):
                self.load(fixture.index_path)

        for count_field in ("case_count", "shard_case_count"):
            with self.subTest(count_field=count_field), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                if count_field == "case_count":
                    fixture.index_payload["case_count"] += 1
                else:
                    fixture.index_payload["shards"][0]["case_count"] += 1
                fixture.write_index()
                with self.assertRaisesRegex(DatasetValidationError, "count"):
                    self.load(fixture.index_path)

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp), [case("duplicate"), case("duplicate")])
            with self.assertRaisesRegex(DatasetValidationError, "duplicate"):
                self.load(fixture.index_path)

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp), [case("bad", "compound")])
            with self.assertRaises(DatasetValidationError):
                self.load(fixture.index_path)

    def test_suite_case_ids_reject_edge_and_control_whitespace(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        for invalid_id in (" leading", "trailing ", "line\nbreak", "tab\tinside"):
            with self.subTest(case_id=invalid_id), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp), [case(invalid_id)])
                with self.assertRaises(DatasetValidationError):
                    self.load(fixture.index_path)

    def test_suite_identifier_runtime_matches_strict_schema(self):
        from jsonschema import Draft202012Validator
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        schema = json.loads(Path("schemas/router-eval-suite.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        for invalid_id in ("suite\nname", "suite\tname", "suite\n"):
            with self.subTest(suite_id=invalid_id), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                fixture.index_payload["suite_id"] = invalid_id
                fixture.write_index()
                self.assertTrue(list(validator.iter_errors(fixture.index_payload)))
                with self.assertRaises(DatasetValidationError):
                    self.load(fixture.index_path)

    def test_declared_order_and_canonical_identity_bind_index_and_shards(self):
        from onecode_skill_sanitizer.router_eval_review import canonical_suite_sha256

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp), [case("normal-002"), case("normal-001")])
            loaded = self.load(fixture.index_path)

            self.assertEqual([item["id"] for item in loaded["cases"]], ["normal-002", "normal-001"])
            identity = loaded["identity"]
            self.assertEqual(identity["suite_id"], "router-production-v1")
            self.assertEqual(identity["case_count"], 2)
            self.assertEqual(identity["suite_sha256"], canonical_suite_sha256(fixture.index_path))
            self.assertRegex(identity["suite_sha256"], r"^sha256:[0-9a-f]{64}$")
            self.assertRegex(identity["dataset_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_suite_schema_is_valid_and_strict(self):
        from jsonschema import Draft202012Validator

        schema = json.loads(Path("schemas/router-eval-suite.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.assertEqual(schema["properties"]["schema_version"]["type"], "integer")
        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            Draft202012Validator(schema).validate(fixture.index_payload)
            invalid = json.loads(json.dumps(fixture.index_payload))
            invalid["shards"][0]["extra"] = True
            self.assertTrue(list(Draft202012Validator(schema).iter_errors(invalid)))


class RouterEvalReviewTests(unittest.TestCase):
    def load_review(self, path: Path, identity: dict):
        from onecode_skill_sanitizer.router_eval_review import load_review_record

        return load_review_record(path, identity)

    def test_valid_review_returns_only_gate_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
            payload = fixture.review_payload(identity)
            path = fixture.root / "review.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            projection = self.load_review(path, identity)

            self.assertNotIn("reviewed_case_ids", projection)
            self.assertNotIn("exceptions", projection)
            self.assertEqual(projection["reviewed_case_count"], 1)
            self.assertEqual(projection["exceptions_count"], 0)
            self.assertEqual(set(projection), {
                "suite_id", "suite_sha256", "reviewed_commit", "rule_author_id",
                "reviewer_id", "reviewer_role", "reviewed_at", "decision",
                "independence_attestation", "reviewed_case_count", "exceptions_count",
            })

    def test_missing_review_and_strict_schema_failures_are_rejected(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
            with self.assertRaises(DatasetValidationError):
                self.load_review(fixture.root / "missing.json", identity)
            payload = fixture.review_payload(identity)
            payload["unknown"] = True
            path = fixture.root / "review.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(DatasetValidationError):
                self.load_review(path, identity)

            payload = fixture.review_payload(identity)
            payload["schema_version"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(DatasetValidationError):
                self.load_review(path, identity)

    def test_review_parser_rejects_conflicting_and_nested_duplicate_keys_and_constants(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        replacements = (
            ('"decision": "accepted"', '"decision": "accepted", "decision": "rejected"'),
            (
                '"case_id": "normal-001"',
                '"case_id": "normal-001", "case_id": "conflicting-id"',
            ),
        )
        for original, replacement in replacements:
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
                payload = fixture.review_payload(identity)
                payload["exceptions"] = [{"case_id": "normal-001", "reason": "Noted"}]
                raw = json.dumps(payload).replace(original, replacement, 1)
                path = fixture.root / "review.json"
                path.write_text(raw, encoding="utf-8")
                with self.assertRaisesRegex(DatasetValidationError, "duplicate"):
                    self.load_review(path, identity)

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
            raw = json.dumps(fixture.review_payload(identity)).replace(
                '"schema_version": 1',
                '"schema_version": NaN',
                1,
            )
            path = fixture.root / "review.json"
            path.write_text(raw, encoding="utf-8")
            with self.assertRaises(DatasetValidationError):
                self.load_review(path, identity)

    def test_exception_reason_schema_and_runtime_reject_control_whitespace(self):
        from jsonschema import Draft202012Validator
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        schema = json.loads(Path("schemas/router-eval-review.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        for reason in ("Noted\tinside", "Noted\ninside", "Noted\n"):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
                payload = fixture.review_payload(identity)
                payload["exceptions"] = [{"case_id": "normal-001", "reason": reason}]
                self.assertTrue(list(validator.iter_errors(payload)))
                path = fixture.root / "review.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(DatasetValidationError):
                    self.load_review(path, identity)

        valid = [{"case_id": "normal-001", "reason": "Accepted wording caveat"}]
        payload["exceptions"] = valid
        validator.validate(payload)

    def test_malformed_suite_identity_is_rejected_with_contract_error(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
            payload = fixture.review_payload(identity)
            path = fixture.root / "review.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            invalid_identities = (
                None,
                {**identity, "extra": True},
                {**identity, "case_count": True},
                {**identity, "case_ids": ["normal-001", "normal-001"]},
            )
            for invalid in invalid_identities:
                with self.subTest(identity=invalid), self.assertRaises(DatasetValidationError):
                    self.load_review(path, invalid)

    def test_review_acceptance_and_suite_binding_are_fail_closed(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        mutations = {
            "same author": lambda p: p.update(reviewer_id=p["rule_author_id"]),
            "false attestation": lambda p: p.update(independence_attestation=False),
            "rejected": lambda p: p.update(decision="rejected"),
            "suite id": lambda p: p.update(suite_id="expired-suite"),
            "suite hash": lambda p: p.update(suite_sha256=f"sha256:{'0' * 64}"),
            "bad commit": lambda p: p.update(reviewed_commit="abc"),
            "bad timestamp": lambda p: p.update(reviewed_at="2026-07-11"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
                payload = fixture.review_payload(identity)
                mutate(payload)
                path = fixture.root / "review.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(DatasetValidationError):
                    self.load_review(path, identity)

    def test_review_loader_cross_checks_trusted_source_identity_when_provided(self):
        from onecode_skill_sanitizer.router_eval_review import load_review_record
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
            payload = fixture.review_payload(identity)
            path = fixture.root / "review.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            source = {"reviewed_commit": "c" * 40, "rule_author_id": "routing-author"}

            load_review_record(path, identity, source)
            for mismatch in (
                {**source, "reviewed_commit": "d" * 40},
                {**source, "rule_author_id": "different-author"},
                None,
            ):
                with self.subTest(source=mismatch), self.assertRaises(DatasetValidationError):
                    load_review_record(path, identity, mismatch)

    def test_reviewed_case_ids_require_exact_full_unique_coverage(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        reviewed_ids = (["normal-001", "normal-001"], ["unknown"], [])
        for ids in reviewed_ids:
            with self.subTest(ids=ids), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
                payload = fixture.review_payload(identity)
                payload["reviewed_case_ids"] = ids
                path = fixture.root / "review.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(DatasetValidationError):
                    self.load_review(path, identity)

    def test_exceptions_have_a_strict_case_bound_contract(self):
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        invalid = (
            ["free form"],
            [{"case_id": "unknown", "reason": "Label wording noted"}],
            [{"case_id": "normal-001", "reason": ""}],
            [{"case_id": "normal-001", "reason": "Noted", "extra": True}],
        )
        for exceptions in invalid:
            with self.subTest(exceptions=exceptions), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
                payload = fixture.review_payload(identity)
                payload["exceptions"] = exceptions
                path = fixture.root / "review.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(DatasetValidationError):
                    self.load_review(path, identity)

    def test_valid_exception_is_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
            payload = fixture.review_payload(identity)
            payload["exceptions"] = [{"case_id": "normal-001", "reason": "Accepted wording caveat"}]
            path = fixture.root / "review.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(self.load_review(path, identity)["exceptions_count"], 1)

    def test_review_schema_is_valid_and_strict(self):
        from jsonschema import Draft202012Validator

        schema = json.loads(Path("schemas/router-eval-review.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.assertEqual(schema["properties"]["schema_version"]["type"], "integer")
        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp))
            identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
            payload = fixture.review_payload(identity)
            Draft202012Validator(schema).validate(payload)
            payload["unknown"] = True
            self.assertTrue(list(Draft202012Validator(schema).iter_errors(payload)))

    def test_review_identifier_runtime_matches_strict_schema(self):
        from jsonschema import Draft202012Validator
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        schema = json.loads(Path("schemas/router-eval-review.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        mutations = (
            lambda payload: payload.update(rule_author_id="author\nname"),
            lambda payload: payload.update(reviewer_id="reviewer\tname"),
            lambda payload: payload.update(reviewed_case_ids=["normal-001\nextra"]),
            lambda payload: payload.update(reviewed_case_ids=["normal-001\n"]),
            lambda payload: payload.update(
                exceptions=[{"case_id": "normal-001\tother", "reason": "Noted"}]
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate), tempfile.TemporaryDirectory() as tmp:
                fixture = SuiteFixture(Path(tmp))
                identity = RouterEvalSuiteTests().load(fixture.index_path)["suite_identity"]
                payload = fixture.review_payload(identity)
                mutate(payload)
                self.assertTrue(list(validator.iter_errors(payload)))
                path = fixture.root / "review.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(DatasetValidationError):
                    self.load_review(path, identity)


class RouterEvalV2ArgumentTests(unittest.TestCase):
    def parse(self, *arguments: str):
        from onecode_skill_sanitizer.cli import build_parser

        return build_parser().parse_args(["router-eval-v2", *arguments])

    def test_eval_or_suite_is_required_and_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            self.parse()
        with self.assertRaises(SystemExit):
            self.parse("--eval", "one.json", "--suite", "index.json")
        self.assertEqual(self.parse("--eval", "one.json").eval, "one.json")
        self.assertEqual(self.parse("--suite", "index.json").suite, "index.json")

    def test_review_requires_suite(self):
        from onecode_skill_sanitizer.commands import _validate_router_eval_v2_inputs

        legacy = self.parse("--eval", "one.json", "--review", "review.json")
        with self.assertRaises(ValueError):
            _validate_router_eval_v2_inputs(legacy)
        parsed = self.parse("--suite", "index.json", "--review", "review.json")
        _validate_router_eval_v2_inputs(parsed)
        self.assertEqual(parsed.review, "review.json")

    def test_blank_or_padded_suite_and_review_paths_fail_as_structured_json(self):
        root = Path(__file__).resolve().parents[1]
        invalid_commands = (
            ("--suite", ""),
            ("--suite", "   "),
            ("--suite", " index.json "),
            ("--suite", "missing.json", "--review", ""),
            ("--suite", "missing.json", "--review", "  "),
            ("--suite", "missing.json", "--review", " review.json "),
            ("--eval", "evals/multi-intent-gold.json", "--review", "review.json"),
            ("--eval", "evals/multi-intent-gold.json", "--review", ""),
        )
        for arguments in invalid_commands:
            with self.subTest(arguments=arguments):
                completed = subprocess.run(
                    [sys.executable, "-m", "onecode_skill_sanitizer", "router-eval-v2", *arguments],
                    cwd=root,
                    env={**os.environ, "PYTHONPATH": str(root / "src")},
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 2)
                self.assertNotIn("Traceback", completed.stderr)
                report = json.loads(completed.stdout)
                self.assertEqual(report["status"], "error")

    def test_deep_suite_json_returns_structured_error_without_traceback(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            suite_path = Path(tmp) / "index.json"
            suite_path.write_text("[" * 10_000 + "0" + "]" * 10_000, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "onecode_skill_sanitizer",
                    "router-eval-v2",
                    "--suite",
                    str(suite_path),
                ],
                cwd=root,
                env={**os.environ, "PYTHONPATH": str(root / "src")},
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "error")


class RouterSourceIdentityTests(unittest.TestCase):
    def git(self, repository: Path, *arguments: str, env: dict[str, str] | None = None):
        return subprocess.run(
            ["git", "-C", str(repository), *arguments],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )

    def repository(self, root: Path) -> tuple[str, str]:
        self.git(root, "init", "--quiet")
        self.git(root, "config", "user.name", "Routing Author")
        self.git(root, "config", "user.email", "routing-author@example.com")
        tracked = root / "router.py"
        tracked.write_text("ROUTER = 1\n", encoding="utf-8")
        self.git(root, "add", "router.py")
        self.git(root, "commit", "--quiet", "-m", "router source")
        commit = self.git(root, "rev-parse", "HEAD").stdout.strip()
        return commit, "routing-author@example.com"

    def test_source_identity_uses_current_commit_author_and_ignores_untracked_files(self):
        from onecode_skill_sanitizer.router_eval_review import load_router_source_identity

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            commit, author = self.repository(root)
            (root / "uv.lock").write_text("untracked\n", encoding="utf-8")

            identity = load_router_source_identity(root)

        self.assertEqual(identity, {"reviewed_commit": commit, "rule_author_id": author})

    def test_source_identity_rejects_dirty_tracked_worktree_and_missing_git(self):
        from onecode_skill_sanitizer.router_eval_review import load_router_source_identity
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.repository(root)
            (root / "router.py").write_text("ROUTER = 2\n", encoding="utf-8")
            with self.assertRaises(DatasetValidationError):
                load_router_source_identity(root)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"PATH": tmp}):
            with self.assertRaises(DatasetValidationError):
                load_router_source_identity(Path(tmp))

    def test_source_identity_normalizes_timeout_command_error_invalid_head_and_empty_author(self):
        from onecode_skill_sanitizer.router_eval_review import load_router_source_identity
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        failures = (
            subprocess.TimeoutExpired(["git"], 5),
            subprocess.CalledProcessError(1, ["git"], stderr="failed"),
        )
        for failure in failures:
            with self.subTest(failure=failure), mock.patch(
                "onecode_skill_sanitizer.router_eval_review.subprocess.run",
                side_effect=failure,
            ):
                with self.assertRaises(DatasetValidationError):
                    load_router_source_identity(Path("repo"))

        invalid_sequences = (
            [
                subprocess.CompletedProcess(["git"], 0, stdout="not-a-commit\n", stderr=""),
            ],
            [
                subprocess.CompletedProcess(["git"], 0, stdout="c" * 40 + "\n", stderr=""),
                subprocess.CompletedProcess(["git"], 0, stdout="", stderr=""),
                subprocess.CompletedProcess(["git"], 0, stdout="\n", stderr=""),
            ],
        )
        for sequence in invalid_sequences:
            with self.subTest(sequence=sequence), mock.patch(
                "onecode_skill_sanitizer.router_eval_review.subprocess.run",
                side_effect=sequence,
            ) as run:
                with self.assertRaises(DatasetValidationError):
                    load_router_source_identity(Path("repo"))
                if run.call_args:
                    self.assertIsInstance(run.call_args.args[0], list)
                    self.assertIs(run.call_args.kwargs["shell"], False)

    def test_source_identity_rejects_head_or_tracked_state_changes_during_validation(self):
        from onecode_skill_sanitizer.router_eval_review import load_router_source_identity
        from onecode_skill_sanitizer.router_eval_v2 import DatasetValidationError

        stable_commit = "c" * 40
        sequences = (
            [stable_commit + "\n", "", "author@example.com\n", "d" * 40 + "\n", ""],
            [stable_commit + "\n", "", "author@example.com\n", stable_commit + "\n", " M router.py\n"],
        )
        for outputs in sequences:
            completed = [
                subprocess.CompletedProcess(["git"], 0, stdout=output, stderr="")
                for output in outputs
            ]
            with self.subTest(outputs=outputs), mock.patch(
                "onecode_skill_sanitizer.router_eval_review.subprocess.run",
                side_effect=completed,
            ):
                with self.assertRaises(DatasetValidationError):
                    load_router_source_identity(Path("repo"))

    def test_suite_without_review_evaluates_but_strict_mode_returns_two(self):
        root = Path(__file__).resolve().parents[1]
        payload = json.loads((root / "evals/multi-intent-gold.json").read_text(encoding="utf-8"))
        category_map = {
            "compound": "multi_intent",
            "sequential": "multi_intent",
            "vague_context": "ambiguous",
            "negative": "negative",
            "multilingual_typo_paraphrase": "multilingual_typo_paraphrase",
            "safety_sensitive": "safety_sensitive",
        }
        cases = [{**item, "category": category_map[item["category"]]} for item in payload["cases"]]
        with tempfile.TemporaryDirectory() as tmp:
            fixture = SuiteFixture(Path(tmp), cases)
            base = [
                sys.executable,
                "-m",
                "onecode_skill_sanitizer",
                "router-eval-v2",
                "--suite",
                str(fixture.index_path),
                "--registry",
                str(root / "catalog"),
                "--bundles",
                str(root / "bundles/index.json"),
            ]
            normal = subprocess.run(
                base,
                cwd=root,
                env={**os.environ, "PYTHONPATH": str(root / "src")},
                capture_output=True,
                text=True,
                check=False,
            )
            strict = subprocess.run(
                [*base, "--require-production-ready"],
                cwd=root,
                env={**os.environ, "PYTHONPATH": str(root / "src")},
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(normal.returncode, 0, normal.stderr)
        self.assertEqual(strict.returncode, 2, strict.stderr)
        self.assertEqual(normal.stdout, strict.stdout)
        report = json.loads(normal.stdout)
        self.assertFalse(report["quality_gate"]["production_ready"])
        self.assertIsNone(report["quality_gate"]["review_identity"])
        self.assertIn("independent_label_review", report["quality_gate"]["missing_gates"])
        self.assertEqual(report["quality_gate"]["dataset_identity"]["suite_id"], "router-production-v1")


if __name__ == "__main__":
    unittest.main()
