import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path


from onecode_skill_sanitizer.cli import load_router_eval
from onecode_skill_sanitizer.cli import main



class RouterEvalCliTest(unittest.TestCase):
    def test_router_eval_passes_expected_scenario_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "router-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_count": 3,
                        "cases": [
                            {
                                "id": "website-launch",
                                "task": "build a product website and prepare launch checks",
                                "router": "scenario",
                                "expected_scenario": "website-build-launch",
                                "expected_task_type": "website_build",
                            },
                            {
                                "id": "skill-router-review",
                                "task": "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标",
                                "router": "mesh",
                                "expected_scenario": "skill-router-quality-review",
                                "expected_task_type": "skill_router_review",
                            },
                            {
                                "id": "unsupported-vague-task",
                                "task": "帮我看一下这个事情是否合理",
                                "router": "scenario",
                                "expected_scenario": "",
                                "expected_task_type": "general",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            eval_out = io.StringIO()
            with contextlib.redirect_stdout(eval_out):
                eval_code = main(
                    [
                        "router-eval",
                        "--eval",
                        str(eval_path),
                        "--registry",
                        "catalog",
                        "--bundles",
                        "bundles/index.json",
                    ]
                )

            self.assertEqual(eval_code, 0)
            result = json.loads(eval_out.getvalue())
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["passed_count"], 3)
            self.assertEqual(result["failed_count"], 0)

    def test_router_eval_fails_unexpected_scenario_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "router-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_count": 1,
                        "cases": [
                            {
                                "id": "bad-expectation",
                                "task": "build a product website and prepare launch checks",
                                "router": "scenario",
                                "expected_scenario": "rag-agent-knowledge-app",
                                "expected_task_type": "website_build",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            eval_out = io.StringIO()
            with contextlib.redirect_stdout(eval_out):
                eval_code = main(
                    [
                        "router-eval",
                        "--eval",
                        str(eval_path),
                        "--registry",
                        "catalog",
                        "--bundles",
                        "bundles/index.json",
                    ]
                )

            self.assertEqual(eval_code, 2)
            result = json.loads(eval_out.getvalue())
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["cases"][0]["status"], "failed")

    def test_router_eval_reports_quality_summary_by_scenario_task_type_and_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "router-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_count": 2,
                        "cases": [
                            {
                                "id": "website-ok",
                                "task": "build a product website and prepare launch checks",
                                "router": "scenario",
                                "expected_scenario": "website-build-launch",
                                "expected_task_type": "website_build",
                            },
                            {
                                "id": "website-bad-scenario",
                                "task": "build a product website and prepare launch checks",
                                "router": "scenario",
                                "expected_scenario": "rag-agent-knowledge-app",
                                "expected_task_type": "website_build",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            eval_out = io.StringIO()
            with contextlib.redirect_stdout(eval_out):
                eval_code = main(
                    [
                        "router-eval",
                        "--eval",
                        str(eval_path),
                        "--registry",
                        "catalog",
                        "--bundles",
                        "bundles/index.json",
                    ]
                )

            self.assertEqual(eval_code, 2)
            result = json.loads(eval_out.getvalue())
            summary = result["quality_summary"]
            self.assertEqual(summary["case_count"], 2)
            self.assertEqual(summary["passed_count"], 1)
            self.assertEqual(summary["failed_count"], 1)
            self.assertEqual(
                summary["by_expected_scenario"]["website-build-launch"],
                {"case_count": 1, "passed_count": 1, "failed_count": 0},
            )
            self.assertEqual(
                summary["by_expected_scenario"]["rag-agent-knowledge-app"],
                {"case_count": 1, "passed_count": 0, "failed_count": 1},
            )
            self.assertEqual(
                summary["by_actual_scenario"]["website-build-launch"],
                {"case_count": 2, "passed_count": 1, "failed_count": 1},
            )
            self.assertEqual(
                summary["by_expected_task_type"]["website_build"],
                {"case_count": 2, "passed_count": 1, "failed_count": 1},
            )
            self.assertEqual(summary["by_issue"], {"router-eval-scenario-mismatch": 1})

    def test_router_eval_reports_issue_classification_and_low_confidence_trend(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "router-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_count": 3,
                        "cases": [
                            {
                                "id": "scenario-false-positive",
                                "task": "build a product website and prepare launch checks",
                                "router": "scenario",
                                "expected_scenario": "",
                                "expected_task_type": "website_build",
                            },
                            {
                                "id": "scenario-false-negative",
                                "task": "帮我看一下这个事情是否合理",
                                "router": "scenario",
                                "expected_scenario": "website-build-launch",
                                "expected_task_type": "general",
                            },
                            {
                                "id": "low-confidence-general-ok",
                                "task": "帮我看一下这个事情是否合理",
                                "router": "scenario",
                                "expected_scenario": "",
                                "expected_task_type": "general",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            eval_out = io.StringIO()
            with contextlib.redirect_stdout(eval_out):
                eval_code = main(
                    [
                        "router-eval",
                        "--eval",
                        str(eval_path),
                        "--registry",
                        "catalog",
                        "--bundles",
                        "bundles/index.json",
                    ]
                )

            self.assertEqual(eval_code, 2)
            result = json.loads(eval_out.getvalue())
            summary = result["quality_summary"]
            self.assertEqual(summary["low_confidence_case_count"], 2)
            self.assertEqual(summary["low_confidence_passed_count"], 1)
            self.assertEqual(summary["low_confidence_failed_count"], 1)
            self.assertEqual(
                summary["by_confidence"]["low"],
                {"case_count": 2, "passed_count": 1, "failed_count": 1},
            )
            self.assertEqual(summary["by_issue_class"], {"false_negative": 1, "false_positive": 1})
            self.assertEqual(result["cases"][0]["issues"][0]["classification"], "false_positive")
            self.assertEqual(result["cases"][1]["issues"][0]["classification"], "false_negative")
            self.assertFalse(result["cases"][0]["actual_low_confidence"])
            self.assertTrue(result["cases"][2]["actual_low_confidence"])
            self.assertEqual(result["cases"][2]["actual_confidence"], "low")

    def test_router_eval_fails_forbidden_skills_prefixes_subcategories_and_skill_count_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "router-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_count": 1,
                        "cases": [
                            {
                                "id": "overloaded-website-pack",
                                "task": "build a product website and prepare launch checks",
                                "router": "scenario",
                                "expected_scenario": "website-build-launch",
                                "expected_task_type": "website_build",
                                "forbidden_skills": ["execution-publish-check"],
                                "forbidden_skill_prefixes": ["execution-browser"],
                                "forbidden_skill_subcategories": ["execution.browser"],
                                "max_skill_count": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            eval_out = io.StringIO()
            with contextlib.redirect_stdout(eval_out):
                eval_code = main(
                    [
                        "router-eval",
                        "--eval",
                        str(eval_path),
                        "--registry",
                        "catalog",
                        "--bundles",
                        "bundles/index.json",
                    ]
                )

            self.assertEqual(eval_code, 2)
            result = json.loads(eval_out.getvalue())
            issue_ids = {issue["id"] for issue in result["cases"][0]["issues"]}
            self.assertIn("router-eval-forbidden-skill", issue_ids)
            self.assertIn("router-eval-forbidden-skill-prefix", issue_ids)
            self.assertIn("router-eval-forbidden-skill-subcategory", issue_ids)
            self.assertIn("router-eval-max-skill-count-exceeded", issue_ids)

    def test_router_eval_can_assert_selection_trace_selected_pruned_required_and_reasons(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "router-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_count": 1,
                        "cases": [
                            {
                                "id": "skill-router-trace",
                                "task": "优化技能库的自动推荐和任务编排能力",
                                "router": "mesh",
                                "expected_scenario": "skill-router-quality-review",
                                "expected_task_type": "skill_router_review",
                                "expected_trace_selected": [
                                    "ai-opensquilla-metaskill-workflow",
                                    "ai-opensquilla-token-routing-pattern",
                                ],
                                "expected_trace_required": [
                                    "ai-opensquilla-token-routing-pattern",
                                    "code-test-regression",
                                ],
                                "expected_trace_pruned": [
                                    "execution-browser-check",
                                    "execution-browser-use-web-task",
                                ],
                                "expected_trace_reason_codes": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            eval_out = io.StringIO()
            with contextlib.redirect_stdout(eval_out):
                eval_code = main(
                    [
                        "router-eval",
                        "--eval",
                        str(eval_path),
                        "--registry",
                        "catalog",
                        "--bundles",
                        "bundles/index.json",
                    ]
                )

            self.assertEqual(eval_code, 0)
            result = json.loads(eval_out.getvalue())
            self.assertEqual(result["status"], "ok")
            self.assertIn("actual_selection_trace", result["cases"][0])
            self.assertEqual(result["cases"][0]["actual_selection_trace"]["selected_count"], 8)

    def test_router_eval_fails_selection_trace_mismatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "router-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_count": 1,
                        "cases": [
                            {
                                "id": "skill-router-bad-trace",
                                "task": "优化技能库的自动推荐和任务编排能力",
                                "router": "mesh",
                                "expected_scenario": "skill-router-quality-review",
                                "expected_task_type": "skill_router_review",
                                "expected_trace_selected": ["execution-browser-check"],
                                "expected_trace_required": ["execution-browser-check"],
                                "expected_trace_pruned": ["ai-opensquilla-token-routing-pattern"],
                                "expected_trace_reason_codes": ["no_trusted_scenario_match"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            eval_out = io.StringIO()
            with contextlib.redirect_stdout(eval_out):
                eval_code = main(
                    [
                        "router-eval",
                        "--eval",
                        str(eval_path),
                        "--registry",
                        "catalog",
                        "--bundles",
                        "bundles/index.json",
                    ]
                )

            self.assertEqual(eval_code, 2)
            result = json.loads(eval_out.getvalue())
            issue_ids = {issue["id"] for issue in result["cases"][0]["issues"]}
            self.assertIn("router-eval-trace-missing-selected", issue_ids)
            self.assertIn("router-eval-trace-missing-required", issue_ids)
            self.assertIn("router-eval-trace-missing-pruned", issue_ids)
            self.assertIn("router-eval-trace-missing-reason-code", issue_ids)

    def test_router_eval_rejects_invalid_constraint_field_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "router-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_count": 1,
                        "cases": [
                            {
                                "id": "invalid-constraints",
                                "task": "build a product website and prepare launch checks",
                                "router": "scenario",
                                "expected_scenario": "website-build-launch",
                                "expected_task_type": "website_build",
                                "forbidden_skills": "execution-publish-check",
                                "forbidden_skill_prefixes": [123],
                                "forbidden_skill_subcategories": {"name": "execution.browser"},
                                "expected_trace_selected": "design-ui-review",
                                "expected_trace_pruned": [123],
                                "expected_trace_required": {"name": "design-ui-review"},
                                "expected_trace_reason_codes": [False],
                                "max_skill_count": -1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            eval_out = io.StringIO()
            with contextlib.redirect_stdout(eval_out):
                eval_code = main(
                    [
                        "router-eval",
                        "--eval",
                        str(eval_path),
                        "--registry",
                        "catalog",
                        "--bundles",
                        "bundles/index.json",
                    ]
                )

            self.assertEqual(eval_code, 2)
            result = json.loads(eval_out.getvalue())
            field_issues = [
                issue for issue in result["cases"][0]["issues"] if issue["id"] == "router-eval-invalid-case-field"
            ]
            self.assertEqual(
                {issue["field"] for issue in field_issues},
                {
                    "forbidden_skills",
                    "forbidden_skill_prefixes",
                    "forbidden_skill_subcategories",
                    "expected_trace_selected",
                    "expected_trace_pruned",
                    "expected_trace_required",
                    "expected_trace_reason_codes",
                    "max_skill_count",
                },
            )

    def test_router_eval_rejects_invalid_expectation_field_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "router-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_count": 1,
                        "cases": [
                            {
                                "id": "invalid-expectations",
                                "task": "build a product website and prepare launch checks",
                                "router": "scenario",
                                "expected_scenario": ["website-build-launch"],
                                "expected_task_type": {"name": "website_build"},
                                "expected_skills": ["business-requirements-brief"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            eval_out = io.StringIO()
            with contextlib.redirect_stdout(eval_out):
                eval_code = main(
                    [
                        "router-eval",
                        "--eval",
                        str(eval_path),
                        "--registry",
                        "catalog",
                        "--bundles",
                        "bundles/index.json",
                    ]
                )

            self.assertEqual(eval_code, 2)
            result = json.loads(eval_out.getvalue())
            field_issues = [
                issue for issue in result["cases"][0]["issues"] if issue["id"] == "router-eval-invalid-case-field"
            ]
            self.assertEqual(
                {issue["field"] for issue in field_issues},
                {
                    "expected_scenario",
                    "expected_task_type",
                },
            )
            issue_ids = {issue["id"] for issue in result["cases"][0]["issues"]}
            self.assertNotIn("router-eval-scenario-mismatch", issue_ids)
            self.assertNotIn("router-eval-task-type-mismatch", issue_ids)

    def test_router_eval_rejects_invalid_control_field_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / "router-eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "case_count": 1,
                        "cases": [
                            {
                                "id": "invalid-controls",
                                "task": "build a product website and prepare launch checks",
                                "router": ["scenario"],
                                "strategy": "exhaustive",
                                "invariants": ["不能泄露密钥", 123],
                                "expected_scenario": "website-build-launch",
                                "expected_task_type": "website_build",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            eval_out = io.StringIO()
            with contextlib.redirect_stdout(eval_out):
                eval_code = main(
                    [
                        "router-eval",
                        "--eval",
                        str(eval_path),
                        "--registry",
                        "catalog",
                        "--bundles",
                        "bundles/index.json",
                    ]
                )

            self.assertEqual(eval_code, 2)
            result = json.loads(eval_out.getvalue())
            field_issues = [
                issue for issue in result["cases"][0]["issues"] if issue["id"] == "router-eval-invalid-case-field"
            ]
            self.assertEqual(
                {issue["field"] for issue in field_issues},
                {
                    "router",
                    "strategy",
                    "invariants",
                },
            )
            issue_ids = {issue["id"] for issue in result["cases"][0]["issues"]}
            self.assertNotIn("router-eval-invalid-router", issue_ids)

    def test_real_router_eval_file_covers_current_catalog_scenarios(self):
        eval_path = Path("evals/router-quality.json")
        payload = json.loads(eval_path.read_text(encoding="utf-8"))
        case_ids = {case["id"] for case in payload["cases"]}

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["case_count"], len(payload["cases"]))
        self.assertGreaterEqual(payload["case_count"], 24)
        self.assertIn("claude-skills-backlog-coverage", case_ids)
        self.assertIn("claude-skills-candidate-map-coverage", case_ids)
        self.assertIn("skill-router-traditional-orchestration", case_ids)
        self.assertIn("website-cn-launch", case_ids)
        self.assertIn("rag-cn-agent", case_ids)
        self.assertIn("commerce-cn-growth", case_ids)
        self.assertIn("industry-cn-solution-pack", case_ids)
        self.assertIn("industry-en-solution-pack", case_ids)

        eval_out = io.StringIO()
        with contextlib.redirect_stdout(eval_out):
            eval_code = main(
                [
                    "router-eval",
                    "--eval",
                    str(eval_path),
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--max-skills",
                    "10",
                ]
            )

        self.assertEqual(eval_code, 0)
        result = json.loads(eval_out.getvalue())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["failed_count"], 0)

    def test_router_eval_schema_v2_regression_envelope_runs_all_cases(self):
        eval_path = Path("evals/router-regression-v2.json")
        payload = load_router_eval(eval_path)

        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["dataset"], "router-quality-v2-baseline")
        self.assertEqual(payload["split"], "regression")
        self.assertEqual(payload["case_count"], 43)
        self.assertEqual(len(payload["cases"]), 43)

        eval_out = io.StringIO()
        with contextlib.redirect_stdout(eval_out):
            eval_code = main(
                [
                    "router-eval",
                    "--eval",
                    str(eval_path),
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--max-skills",
                    "10",
                ]
            )

        self.assertEqual(eval_code, 0)
        result = json.loads(eval_out.getvalue())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["case_count"], 43)
        self.assertEqual(result["passed_count"], 43)
        self.assertEqual(result["failed_count"], 0)

    def test_router_eval_v2_explains_legacy_router_eval_dataset_mismatch(self):
        eval_out = io.StringIO()
        with contextlib.redirect_stdout(eval_out):
            eval_code = main(
                [
                    "router-eval-v2",
                    "--eval",
                    "evals/router-regression-v2.json",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                ]
            )

        self.assertEqual(eval_code, 2)
        result = json.loads(eval_out.getvalue())
        self.assertEqual(result["status"], "error")
        self.assertIn("router-eval dataset", result["error"])
        self.assertIn("use router-eval", result["error"])
        self.assertIn("multi-intent gold/suite contract", result["error"])

    def test_load_router_eval_v2_requires_valid_regression_envelope(self):
        valid_case = {
            "id": "website-launch",
            "task": "build a product website and prepare launch checks",
            "router": "scenario",
        }
        valid_payload = {
            "schema_version": 2,
            "dataset": "router-quality-v2-baseline",
            "split": "regression",
            "case_count": 1,
            "cases": [valid_case],
        }
        invalid_payloads = {
            "dataset": ({key: value for key, value in valid_payload.items() if key != "dataset"}, "dataset"),
            "split": ({key: value for key, value in valid_payload.items() if key != "split"}, "split"),
            "non_regression_split": ({**valid_payload, "split": "training"}, "split"),
            "case_count": ({**valid_payload, "case_count": 2}, "case_count"),
            "unique_ids": ({**valid_payload, "case_count": 2, "cases": [valid_case, dict(valid_case)]}, "unique case id"),
        }

        with tempfile.TemporaryDirectory() as tmp:
            for name, (payload, expected_error) in invalid_payloads.items():
                with self.subTest(name=name):
                    eval_path = Path(tmp) / f"{name}.json"
                    eval_path.write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaisesRegex(SystemExit, expected_error):
                        load_router_eval(eval_path)


if __name__ == "__main__":
    unittest.main()
