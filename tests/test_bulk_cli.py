import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path


from onecode_skill_sanitizer.cli import claude_skills_candidate_sort_key
from onecode_skill_sanitizer.cli import main



class BulkCliTest(unittest.TestCase):
    def test_real_external_references_include_claude_skills_metadata_only(self):
        reference_out = io.StringIO()
        with contextlib.redirect_stdout(reference_out):
            reference_code = main(["reference-check", "--references", "external-references/index.json"])

        self.assertEqual(reference_code, 0)
        result = json.loads(reference_out.getvalue())
        self.assertEqual(result["status"], "ok")
        references = json.loads(Path("external-references/index.json").read_text(encoding="utf-8"))["references"]
        claude_skills = next((item for item in references if item["name"] == "claude-skills"), None)

        self.assertIsNotNone(claude_skills)
        self.assertEqual(claude_skills["adoption_status"], "reference_only")
        self.assertTrue(claude_skills["metadata_only"])
        self.assertIn("multi_agent_distribution", claude_skills["claimed_capabilities"])
        self.assertIn("Do not install", claude_skills["runtime_permission_notes"])

    def test_claude_skills_candidate_map_records_ranked_evaluation(self):
        candidate_map = json.loads(Path("docs/claude-skills-candidate-map.json").read_text(encoding="utf-8"))

        self.assertEqual(candidate_map["schema_version"], 1)
        self.assertEqual(candidate_map["source"], "https://github.com/alirezarezvani/claude-skills")
        self.assertGreaterEqual(candidate_map["candidate_count"], 300)
        self.assertEqual(candidate_map["candidate_count"], len(candidate_map["candidates"]))
        self.assertIn("sanitized_local_authoring_only", candidate_map["adoption_policy"])
        names = {candidate["name"]: candidate for candidate in candidate_map["candidates"]}
        for name in [
            "saas-metrics-coach",
            "rfp-responder",
            "procurement-optimizer",
            "clinical-research",
            "vendor-management",
            "commercial-forecaster",
            "revenue-operations",
            "deal-desk",
            "financial-analyst",
            "scrum-master",
            "knowledge-ops",
            "process-mapper",
            "commercial-policy",
            "partnerships-architect",
            "channel-economics",
            "senior-pm",
            "jira-expert",
            "confluence-expert",
            "internal-comms",
            "capacity-planner",
            "meeting-analyzer",
            "team-communications",
            "contract-and-proposal-writer",
            "sales-engineer",
            "market-research",
            "product-research",
            "research-finance",
            "business-investment-advisor",
            "atlassian-admin",
            "atlassian-templates",
            "pricing-strategy",
            "commercial-skills",
            "finance-skills",
            "business-growth-skills",
            "pm-skills",
            "research-ops-skills",
        ]:
            self.assertIn(name, names)
            self.assertIn(names[name]["priority"], {"P0", "P1"})
            self.assertIn(names[name]["adoption"], {"candidate", "converted"})

        converted = {candidate["name"] for candidate in candidate_map["candidates"] if candidate["adoption"] == "converted"}
        required_converted = {
                "saas-metrics-coach",
                "rfp-responder",
                "procurement-optimizer",
                "pricing-strategist",
                "customer-success-manager",
                "clinical-research",
                "vendor-management",
                "commercial-forecaster",
                "revenue-operations",
                "deal-desk",
                "financial-analyst",
                "scrum-master",
                "knowledge-ops",
                "process-mapper",
                "commercial-policy",
                "partnerships-architect",
                "channel-economics",
                "senior-pm",
                "jira-expert",
                "confluence-expert",
                "internal-comms",
                "capacity-planner",
                "meeting-analyzer",
                "team-communications",
                "contract-and-proposal-writer",
                "sales-engineer",
                "market-research",
                "product-research",
                "research-finance",
                "business-investment-advisor",
                "atlassian-admin",
                "atlassian-templates",
                "pricing-strategy",
                "commercial-skills",
                "finance-skills",
                "business-growth-skills",
                "pm-skills",
                "research-ops-skills",
                "business-operations-skills",
                "landing-page-generator",
                "marketing-strategy-pmm",
                "review",
                "ui-design-system",
                "content-strategy",
                "social-content",
                "eval",
                "report",
                "research",
                "browser-automation",
                "data-quality-auditor",
                "design-system",
                "landing",
                "brief",
        }
        self.assertTrue(required_converted.issubset(converted))
        self.assertEqual(candidate_map["candidate_count"], len(converted))

    def test_claude_skills_candidate_map_is_sorted_by_evaluation_priority(self):
        candidate_map = json.loads(Path("docs/claude-skills-candidate-map.json").read_text(encoding="utf-8"))
        candidates = candidate_map["candidates"]

        self.assertEqual(candidates, sorted(candidates, key=claude_skills_candidate_sort_key))
        self.assertEqual(
            {candidate["adoption"] for candidate in candidates},
            {"converted"},
        )

    def test_claude_skills_bulk_plan_batches_all_non_converted_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate_map = Path(tmp) / "candidate-map.json"
            candidate_map.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "https://github.com/alirezarezvani/claude-skills",
                        "candidate_count": 5,
                        "converted_skill_count": 1,
                        "candidates": [
                            {
                                "name": "alpha",
                                "adoption": "converted",
                                "priority": "P0",
                                "score": 90,
                                "mapped_category": "business",
                                "source_domain": "operations",
                                "source_path": "operations/skills/alpha",
                                "local_skill": "business-alpha-review",
                            },
                            {
                                "name": "beta",
                                "adoption": "reference_only",
                                "priority": "P1",
                                "score": 80,
                                "mapped_category": "code",
                                "source_domain": "engineering",
                                "source_path": "engineering/skills/beta",
                            },
                            {
                                "name": "gamma",
                                "adoption": "candidate",
                                "priority": "P0",
                                "score": 100,
                                "mapped_category": "security",
                                "source_domain": "security",
                                "source_path": "security/skills/gamma",
                            },
                            {
                                "name": "delta",
                                "adoption": "reference_only",
                                "priority": "P2",
                                "score": 70,
                                "mapped_category": "content",
                                "source_domain": "marketing",
                                "source_path": "marketing/skills/delta",
                            },
                            {
                                "name": "epsilon",
                                "adoption": "reference_only",
                                "priority": "P1",
                                "score": 60,
                                "mapped_category": "business",
                                "source_domain": "operations",
                                "source_path": "operations/skills/epsilon",
                            },
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                exit_code = main(
                    [
                        "claude-skills-bulk-plan",
                        "--candidate-map",
                        str(candidate_map),
                        "--batch-size",
                        "2",
                    ]
                )

            self.assertEqual(exit_code, 0)
            plan = json.loads(out.getvalue())
            self.assertEqual(plan["schema_version"], 1)
            self.assertEqual(plan["mode"], "metadata_only_bulk_review")
            self.assertEqual(plan["candidate_count"], 5)
            self.assertEqual(plan["converted_count"], 1)
            self.assertEqual(plan["actionable_count"], 4)
            self.assertEqual(plan["adoption_counts"], {"candidate": 1, "converted": 1, "reference_only": 3})
            self.assertEqual(plan["batch_size"], 2)
            self.assertEqual(plan["batch_count"], 2)
            self.assertIn("Do not copy, install, execute, or trust upstream skill bodies.", plan["safety_boundary"])
            self.assertEqual([item["name"] for item in plan["batches"][0]["items"]], ["gamma", "beta"])
            self.assertEqual([item["name"] for item in plan["batches"][1]["items"]], ["delta", "epsilon"])
            self.assertEqual(plan["recommended_next_action"], "Generate local sanitized batch drafts from the highest-priority batch, then import, approve serially, and verify.")

    def test_claude_skills_bulk_draft_generates_local_review_drafts_for_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate_map = root / "candidate-map.json"
            out_dir = root / "batch-999-claude-skills-bulk-draft"
            candidate_map.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "https://github.com/alirezarezvani/claude-skills",
                        "candidate_count": 3,
                        "converted_skill_count": 1,
                        "candidates": [
                            {
                                "name": "alpha",
                                "adoption": "converted",
                                "priority": "P0",
                                "score": 90,
                                "mapped_category": "business",
                                "source_domain": "operations",
                                "source_path": "operations/skills/alpha",
                                "local_skill": "business-alpha-review",
                            },
                            {
                                "name": "beta-toolkit",
                                "adoption": "reference_only",
                                "priority": "P1",
                                "score": 80,
                                "mapped_category": "code",
                                "source_domain": "engineering",
                                "source_path": "engineering/skills/beta-toolkit",
                            },
                            {
                                "name": "gamma-risk",
                                "adoption": "candidate",
                                "priority": "P0",
                                "score": 100,
                                "mapped_category": "security",
                                "source_domain": "security",
                                "source_path": "security/skills/gamma-risk",
                            },
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                exit_code = main(
                    [
                        "claude-skills-bulk-draft",
                        "--candidate-map",
                        str(candidate_map),
                        "--out",
                        str(out_dir),
                        "--batch-size",
                        "2",
                        "--batch-index",
                        "1",
                    ]
                )

            self.assertEqual(exit_code, 0)
            result = json.loads(out.getvalue())
            self.assertEqual(result["schema_version"], 1)
            self.assertEqual(result["mode"], "metadata_only_local_draft")
            self.assertEqual(result["draft_count"], 2)
            self.assertEqual(result["draft_names"], ["security-gamma-risk-review", "code-beta-toolkit-review"])
            self.assertIn("not trusted", result["next_steps"][0])

            for name in result["draft_names"]:
                skill_dir = out_dir / name
                skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                manifest = json.loads((skill_dir / "skill.json").read_text(encoding="utf-8"))
                self.assertIn("metadata-only", skill_text)
                self.assertIn("Do not execute upstream", skill_text)
                self.assertEqual(manifest["name"], name)
                self.assertEqual(manifest["status"], "draft")
                self.assertEqual(manifest["source"]["usage"], "local_authoring")
                self.assertEqual(manifest["source"]["type"], "local_folder")

    def test_claude_skills_bulk_assess_ranks_drafts_before_catalog_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate_map = root / "candidate-map.json"
            draft_root = root / "drafts"
            registry = root / "registry"
            existing = root / "existing"
            existing_skill = existing / "content-seo-audit-review"
            done_skill = existing / "business-done-skill-review"
            existing_skill.mkdir(parents=True)
            done_skill.mkdir(parents=True)
            (existing_skill / "SKILL.md").write_text(
                "Use when reviewing SEO audit quality, metadata, content structure, and search visibility.",
                encoding="utf-8",
            )
            (done_skill / "SKILL.md").write_text(
                "Use when reviewing completed business skill coverage.",
                encoding="utf-8",
            )
            main(["import", str(existing), "--registry", str(registry), "--collected-by", "onecode-test"])
            registry_index = json.loads((registry / "index.json").read_text(encoding="utf-8"))
            existing_path = next(entry["registry_path"] for entry in registry_index["skills"] if entry["name"] == "content-seo-audit-review")
            done_path = next(entry["registry_path"] for entry in registry_index["skills"] if entry["name"] == "business-done-skill-review")
            main(["approve", str(registry / existing_path)])
            main(["approve", str(registry / done_path)])

            candidate_map.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "https://github.com/alirezarezvani/claude-skills",
                        "candidate_count": 4,
                        "candidates": [
                            {
                                "name": "done-skill",
                                "adoption": "converted",
                                "priority": "P0",
                                "score": 100,
                                "mapped_category": "business",
                                "source_domain": "operations",
                                "source_path": "operations/skills/done-skill",
                                "local_skill": "business-done-skill-review",
                            },
                            {
                                "name": "growth-playbook",
                                "adoption": "reference_only",
                                "priority": "P1",
                                "score": 88,
                                "mapped_category": "business",
                                "source_domain": "product-team",
                                "source_path": "product-team/skills/growth-playbook",
                            },
                            {
                                "name": "seo-audit",
                                "adoption": "reference_only",
                                "priority": "P2",
                                "score": 70,
                                "mapped_category": "content",
                                "source_domain": "marketing-skill",
                                "source_path": "marketing-skill/skills/seo-audit",
                            },
                            {
                                "name": "low-noise",
                                "adoption": "reference_only",
                                "priority": "P3",
                                "score": 12,
                                "mapped_category": "business",
                                "source_domain": "c-level-advisor",
                                "source_path": "c-level-advisor/skills/low-noise",
                            },
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            for skill_name in [
                "business-growth-playbook-review",
                "content-seo-audit-review",
                "business-low-noise-review",
            ]:
                skill_dir = draft_root / skill_name
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(
                    f"Use when reviewing {skill_name} metadata-only candidates before catalog inclusion.",
                    encoding="utf-8",
                )
                (skill_dir / "skill.json").write_text(
                    json.dumps({"name": skill_name, "status": "draft"}, indent=2),
                    encoding="utf-8",
                )

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                exit_code = main(
                    [
                        "claude-skills-bulk-assess",
                        "--candidate-map",
                        str(candidate_map),
                        "--draft-root",
                        str(draft_root),
                        "--registry",
                        str(registry),
                    ]
                )

            self.assertEqual(exit_code, 0)
            result = json.loads(out.getvalue())
            self.assertEqual(result["schema_version"], 1)
            self.assertEqual(result["mode"], "metadata_only_bulk_assessment")
            self.assertEqual(result["candidate_count"], 4)
            self.assertEqual(result["draft_count"], 3)
            self.assertEqual(
                result["recommendation_counts"],
                {
                    "already_converted": 1,
                    "author_local_skill": 1,
                    "keep_reference_only": 1,
                    "merge_existing": 1,
                },
            )
            by_name = {item["candidate"]: item for item in result["items"]}
            self.assertEqual(by_name["growth-playbook"]["recommendation"], "author_local_skill")
            self.assertEqual(by_name["growth-playbook"]["next_gate"], "local-authoring-review")
            self.assertEqual(by_name["seo-audit"]["recommendation"], "merge_existing")
            self.assertEqual(by_name["seo-audit"]["overlap_skill"], "content-seo-audit-review")
            self.assertEqual(by_name["low-noise"]["recommendation"], "keep_reference_only")
            self.assertEqual(by_name["done-skill"]["recommendation"], "already_converted")
            self.assertIn("does not approve or trust drafts", result["safety_boundary"])

    def test_claude_skills_bulk_assess_flags_invalid_converted_mappings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate_map = root / "candidate-map.json"
            draft_root = root / "drafts"
            registry = root / "registry"
            incoming = root / "incoming"
            untrusted_skill = incoming / "business-untrusted-review"
            untrusted_skill.mkdir(parents=True)
            (untrusted_skill / "SKILL.md").write_text(
                "Use when reviewing untrusted business coverage.",
                encoding="utf-8",
            )
            (untrusted_skill / "skill.json").write_text(
                json.dumps(
                    {
                        "taxonomy": {
                            "category": "business",
                            "subcategory": "business.coverage",
                            "task_intent": "review business coverage",
                            "artifact_type": "review",
                            "collection_priority": "P1",
                        }
                    }
                ),
                encoding="utf-8",
            )
            main(["import", str(incoming), "--registry", str(registry), "--collected-by", "onecode-test"])
            candidate_map.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source": "https://github.com/alirezarezvani/claude-skills",
                        "candidate_count": 3,
                        "candidates": [
                            {
                                "name": "missing-local",
                                "adoption": "converted",
                                "priority": "P1",
                                "score": 90,
                                "mapped_category": "business",
                            },
                            {
                                "name": "missing-registry",
                                "adoption": "converted",
                                "priority": "P1",
                                "score": 88,
                                "mapped_category": "business",
                                "local_skill": "business-missing-review",
                            },
                            {
                                "name": "untrusted",
                                "adoption": "converted",
                                "priority": "P1",
                                "score": 86,
                                "mapped_category": "business",
                                "local_skill": "business-untrusted-review",
                            },
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                exit_code = main(
                    [
                        "claude-skills-bulk-assess",
                        "--candidate-map",
                        str(candidate_map),
                        "--draft-root",
                        str(draft_root),
                        "--registry",
                        str(registry),
                    ]
                )

            self.assertEqual(exit_code, 0)
            result = json.loads(out.getvalue())
            self.assertEqual(result["recommendation_counts"], {"invalid_converted_mapping": 3})
            by_name = {item["candidate"]: item for item in result["items"]}
            self.assertEqual(by_name["missing-local"]["mapping_status"], "missing_local_skill")
            self.assertEqual(by_name["missing-registry"]["mapping_status"], "missing_registry_skill")
            self.assertEqual(by_name["untrusted"]["mapping_status"], "non_trusted_local_skill")
            self.assertEqual(by_name["untrusted"]["local_skill_status"], "quarantined")
            self.assertEqual(by_name["untrusted"]["next_gate"], "candidate-map-fix")

    def test_real_claude_skills_bulk_assess_has_no_merge_backlog(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = main(
                [
                    "claude-skills-bulk-assess",
                    "--candidate-map",
                    "docs/claude-skills-candidate-map.json",
                    "--draft-root",
                    "batches",
                    "--registry",
                    "catalog",
                ]
            )

        self.assertEqual(exit_code, 0)
        result = json.loads(out.getvalue())
        self.assertEqual(result["recommendation_counts"], {"already_converted": 336})
        self.assertNotIn("author_local_skill", result["recommendation_counts"])
        self.assertNotIn("merge_existing", result["recommendation_counts"])
        self.assertNotIn("keep_reference_only", result["recommendation_counts"])

    def test_catalog_includes_claude_skills_backlog_cluster_skills(self):
        index = json.loads(Path("catalog/index.json").read_text(encoding="utf-8"))
        by_name = {entry["name"]: entry for entry in index["skills"]}

        expected = {
            "ai-claude-skills-meta-workflow-review": "ai",
            "business-claude-skills-backlog-orchestration": "business",
            "code-claude-skills-engineering-role-review": "code",
            "compliance-claude-skills-regulated-review": "compliance",
            "content-claude-skills-growth-review": "content",
            "engineering-claude-skills-operations-review": "engineering",
            "execution-claude-skills-productivity-review": "execution",
            "office-claude-skills-document-review": "office",
            "research-claude-skills-evidence-review": "research",
        }
        for name, category in expected.items():
            self.assertIn(name, by_name)
            self.assertEqual(by_name[name]["status"], "trusted")
            self.assertEqual(by_name[name]["taxonomy"]["category"], category)
            self.assertEqual(by_name[name]["source"]["usage"], "local_authoring")
            self.assertIn("claude-skills", by_name[name]["source"]["reference"])

    def test_catalog_includes_first_sanitized_claude_skills_expansion_batch(self):
        index = json.loads(Path("catalog/index.json").read_text(encoding="utf-8"))
        by_name = {entry["name"]: entry for entry in index["skills"]}

        expected = {
            "business-saas-metrics-review": "business",
            "commerce-rfp-response-review": "commerce",
            "business-procurement-optimization-review": "business",
            "commerce-pricing-strategy-review": "commerce",
            "business-customer-success-health-review": "business",
            "research-clinical-study-design-review": "research",
        }
        for name, category in expected.items():
            self.assertIn(name, by_name)
            self.assertEqual(by_name[name]["status"], "trusted")
            self.assertEqual(by_name[name]["risk_level"], "low")
            self.assertEqual(by_name[name]["taxonomy"]["category"], category)
            self.assertEqual(by_name[name]["source"]["usage"], "local_authoring")
            self.assertEqual(by_name[name]["source"]["collected_by"], "onecode-claude-skills-expansion")
            self.assertIn("claude-skills", by_name[name]["source"]["reference"])

    def test_catalog_includes_second_sanitized_claude_skills_depth_batch(self):
        index = json.loads(Path("catalog/index.json").read_text(encoding="utf-8"))
        by_name = {entry["name"]: entry for entry in index["skills"]}

        expected = {
            "business-vendor-management-review": "business",
            "commerce-commercial-forecast-review": "commerce",
            "business-revenue-operations-review": "business",
            "commerce-deal-desk-review": "commerce",
            "business-financial-analysis-review": "business",
            "business-scrum-project-review": "business",
            "business-knowledge-operations-review": "business",
            "business-process-mapping-review": "business",
        }
        for name, category in expected.items():
            self.assertIn(name, by_name)
            self.assertEqual(by_name[name]["status"], "trusted")
            self.assertEqual(by_name[name]["risk_level"], "low")
            self.assertEqual(by_name[name]["taxonomy"]["category"], category)
            self.assertEqual(by_name[name]["source"]["usage"], "local_authoring")
            self.assertEqual(by_name[name]["source"]["collected_by"], "onecode-claude-skills-depth")
            self.assertIn("claude-skills", by_name[name]["source"]["reference"])

    def test_catalog_includes_third_sanitized_claude_skills_ops_batch(self):
        index = json.loads(Path("catalog/index.json").read_text(encoding="utf-8"))
        by_name = {entry["name"]: entry for entry in index["skills"]}

        expected = {
            "commerce-commercial-policy-review": "commerce",
            "commerce-partnerships-strategy-review": "commerce",
            "commerce-channel-economics-review": "commerce",
            "business-product-management-review": "business",
            "business-jira-workflow-review": "business",
            "business-confluence-knowledge-review": "business",
            "business-internal-comms-review": "business",
            "business-capacity-planning-review": "business",
        }
        for name, category in expected.items():
            self.assertIn(name, by_name)
            self.assertEqual(by_name[name]["status"], "trusted")
            self.assertEqual(by_name[name]["risk_level"], "low")
            self.assertEqual(by_name[name]["taxonomy"]["category"], category)
            self.assertEqual(by_name[name]["source"]["usage"], "local_authoring")
            self.assertEqual(by_name[name]["source"]["collected_by"], "onecode-claude-skills-ops")
            self.assertIn("claude-skills", by_name[name]["source"]["reference"])

    def test_catalog_includes_fourth_sanitized_claude_skills_research_comms_batch(self):
        index = json.loads(Path("catalog/index.json").read_text(encoding="utf-8"))
        by_name = {entry["name"]: entry for entry in index["skills"]}

        expected = {
            "business-meeting-analysis-review": "business",
            "business-team-communications-review": "business",
            "business-contract-proposal-review": "business",
            "business-sales-engineering-review": "business",
            "research-market-analysis-review": "research",
            "research-product-analysis-review": "research",
            "research-finance-analysis-review": "research",
            "business-investment-memo-review": "business",
        }
        for name, category in expected.items():
            self.assertIn(name, by_name)
            self.assertEqual(by_name[name]["status"], "trusted")
            self.assertEqual(by_name[name]["risk_level"], "low")
            self.assertEqual(by_name[name]["taxonomy"]["category"], category)
            self.assertEqual(by_name[name]["source"]["usage"], "local_authoring")
            self.assertEqual(by_name[name]["source"]["collected_by"], "onecode-claude-skills-research-comms")
            self.assertIn("claude-skills", by_name[name]["source"]["reference"])

    def test_catalog_includes_fifth_sanitized_claude_skills_overlap_batch(self):
        index = json.loads(Path("catalog/index.json").read_text(encoding="utf-8"))
        by_name = {entry["name"]: entry for entry in index["skills"]}

        expected = {
            "business-atlassian-admin-governance-review": "business",
            "business-atlassian-template-governance-review": "business",
            "content-marketing-pricing-strategy-review": "content",
        }
        for name, category in expected.items():
            self.assertIn(name, by_name)
            self.assertEqual(by_name[name]["status"], "trusted")
            self.assertEqual(by_name[name]["risk_level"], "low")
            self.assertEqual(by_name[name]["taxonomy"]["category"], category)
            self.assertEqual(by_name[name]["source"]["usage"], "local_authoring")
            self.assertEqual(by_name[name]["source"]["collected_by"], "onecode-claude-skills-overlap-depth")
            self.assertIn("claude-skills", by_name[name]["source"]["reference"])

    def test_catalog_includes_claude_skills_authoring_wave(self):
        index = json.loads(Path("catalog/index.json").read_text(encoding="utf-8"))
        by_name = {entry["name"]: entry for entry in index["skills"]}

        expected = {
            "commerce-commercial-operations-review": "commerce",
            "business-finance-operations-review": "business",
            "business-growth-operations-review": "business",
            "business-project-management-operations-review": "business",
            "research-operations-governance-review": "research",
        }
        for name, category in expected.items():
            self.assertIn(name, by_name)
            self.assertEqual(by_name[name]["status"], "trusted")
            self.assertEqual(by_name[name]["risk_level"], "low")
            self.assertEqual(by_name[name]["taxonomy"]["category"], category)
            self.assertEqual(by_name[name]["source"]["usage"], "local_authoring")
            self.assertEqual(by_name[name]["source"]["collected_by"], "onecode-claude-skills-authoring-wave")
            self.assertIn("claude-skills", by_name[name]["source"]["reference"])

    def test_maintain_check_validates_claude_skills_coverage_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            registry = root / "registry"
            candidate_map = root / "claude-skills-candidate-map.json"
            skill = incoming / "business-covered-review"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "Use this workflow for business coverage review.",
                encoding="utf-8",
            )
            (skill / "skill.json").write_text(
                json.dumps(
                    {
                        "taxonomy": {
                            "category": "business",
                            "subcategory": "business.coverage",
                            "task_intent": "review business coverage",
                            "artifact_type": "review",
                            "collection_priority": "P1",
                        }
                    }
                ),
                encoding="utf-8",
            )

            main(["import", str(incoming), "--registry", str(registry), "--collected-by", "onecode-test"])
            main(["approve", str(registry / "business" / "business-covered-review")])
            candidate_map.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "candidate_count": 99,
                        "converted_skill_count": 1,
                        "candidates": [
                            {
                                "name": "covered",
                                "adoption": "converted",
                                "local_skill": "business-covered-review",
                            },
                            {
                                "name": "missing-local-skill",
                                "adoption": "converted",
                            },
                            {
                                "name": "missing-registry-skill",
                                "adoption": "converted",
                                "local_skill": "business-missing-review",
                            },
                        ],
                        "converted_skills": [
                            {
                                "source_candidate": "covered",
                                "local_skill": "business-covered-review",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            maintain_out = io.StringIO()
            with contextlib.redirect_stdout(maintain_out):
                maintain_code = main(
                    [
                        "maintain-check",
                        "--registry",
                        str(registry),
                        "--claude-skills-candidate-map",
                        str(candidate_map),
                    ]
                )

            self.assertEqual(maintain_code, 2)
            result = json.loads(maintain_out.getvalue())
            issue_ids = {issue["id"] for issue in result["issues"]}
            self.assertIn("claude-skills-candidate-count-mismatch", issue_ids)
            self.assertIn("claude-skills-converted-count-mismatch", issue_ids)
            self.assertIn("claude-skills-missing-local-skill", issue_ids)
            self.assertIn("claude-skills-missing-registry-skill", issue_ids)
            self.assertIn("claude-skills-converted-skills-mismatch", issue_ids)

    def test_real_maintain_check_includes_claude_skills_coverage_map(self):
        maintain_out = io.StringIO()
        with contextlib.redirect_stdout(maintain_out):
            maintain_code = main(
                [
                    "maintain-check",
                    "--registry",
                    "catalog",
                    "--bundles",
                    "bundles/index.json",
                    "--references",
                    "external-references/index.json",
                    "--claude-skills-candidate-map",
                    "docs/claude-skills-candidate-map.json",
                ]
            )

        self.assertEqual(maintain_code, 0)
        result = json.loads(maintain_out.getvalue())
        self.assertEqual(result["claude_skills_candidate_map_validation"]["status"], "ok")
        self.assertEqual(result["claude_skills_candidate_map_validation"]["converted_count"], 336)

    def test_real_catalog_scenario_router_selects_claude_skills_backlog_coverage_bundle(self):
        task_pack_out = io.StringIO()
        with contextlib.redirect_stdout(task_pack_out):
            task_pack_code = main(
                [
                    "task-pack",
                    "--schema-version",
                    "1",
                    "把剩余 claude-skills reference-only backlog 候选 skill 优化编排并纳入体系",
                    "--registry",
                    "catalog",
                    "--include-bundles",
                    "--bundles",
                    "bundles/index.json",
                    "--router",
                    "scenario",
                    "--max-skills",
                    "10",
                ]
            )

        self.assertEqual(task_pack_code, 0)
        task_pack = json.loads(task_pack_out.getvalue())
        names = [skill["name"] for skill in task_pack["skills"]]
        self.assertEqual(task_pack["selected_scenario"]["id"], "claude-skills-backlog-coverage")
        self.assertEqual(task_pack["pipeline_plan"]["id"], "claude-skills-backlog-coverage")
        self.assertIn("business-claude-skills-backlog-orchestration", names)
        self.assertIn("engineering-claude-skills-operations-review", names)
        self.assertIn("compliance-claude-skills-regulated-review", names)


if __name__ == "__main__":
    unittest.main()
