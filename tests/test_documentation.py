import re
import unittest
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def markdown_local_links(path: Path) -> list[Path]:
    links = []
    for raw_target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
        target = unquote(raw_target.split("#", 1)[0])
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        links.append(Path(target))
    return links


class DocumentationTest(unittest.TestCase):
    def test_readme_points_to_documentation_index(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("[Documentation Index](docs/index.md)", readme)

    def test_primary_document_links_resolve(self):
        paths = [ROOT / "README.md", ROOT / "docs/index.md", ROOT / "docs/history.md"]
        for path in paths:
            self.assertTrue(path.is_file(), f"missing primary document: {path}")
            for target in markdown_local_links(path):
                resolved = (path.parent / target).resolve()
                self.assertTrue(resolved.exists(), f"broken link: {path} -> {target}")

    def test_v3_design_and_plan_are_linked_from_documentation_index(self):
        index_path = ROOT / "docs/index.md"
        index = index_path.read_text(encoding="utf-8")
        targets = [
            "superpowers/specs/2026-07-15-high-frequency-intelligent-skill-selection-design.md",
            "superpowers/plans/2026-07-15-high-frequency-intelligent-skill-selection.md",
        ]

        for target in targets:
            self.assertIn(f"]({target})", index)
            self.assertTrue((index_path.parent / target).is_file(), f"missing document: {target}")

    def test_v3_rollout_status_and_boundaries_are_documented(self):
        readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
        router_guide = " ".join(
            (ROOT / "docs/router-development.md").read_text(encoding="utf-8").split()
        )
        task_pack = " ".join(
            (ROOT / "docs/agent-task-pack.md").read_text(encoding="utf-8").split()
        )
        index = " ".join((ROOT / "docs/index.md").read_text(encoding="utf-8").split())

        for document in (readme, router_guide, task_pack, index):
            self.assertIn("Router v3 remains opt-in; Router v2 remains the default.", document)

        for document in (readme, router_guide, task_pack):
            self.assertIn("final_acceptance_failed", document)
            self.assertIn("task_evaluation_missing", document)
            self.assertIn("Skills are method guidance, not permission grants.", document)

        required_router_truth = [
            "router entry plus exactly seven high-frequency candidates",
            "Deterministic selection is active.",
            "Semantic providers are candidate-bounded and run in shadow only.",
            "Semantic influence is disabled through the public CLI.",
            "The validation split passes",
            "the one permitted `final_test` run failed release acceptance",
            "no real three-arm task evidence was generated",
            "Runtime examples are reviewed routing data",
            "The isolated 120 held-out cases are evaluator-only and must not be runtime inputs.",
            "Adding an eighth candidate requires a separate frequency, trust, examples, evaluation, and operator-review decision.",
        ]
        for statement in required_router_truth:
            self.assertIn(statement, router_guide)

        for document in (router_guide, task_pack):
            self.assertIn("Semantic providers are candidate-bounded and run in shadow only.", document)
            self.assertIn("Semantic influence is disabled through the public CLI.", document)
            self.assertIn("The isolated 120 held-out cases are evaluator-only and must not be runtime inputs.", document)

    def test_v3_cli_opt_in_and_one_shot_release_boundary_are_documented(self):
        paths = [
            ROOT / "README.md",
            ROOT / "docs/router-development.md",
            ROOT / "docs/agent-task-pack.md",
            ROOT / "docs/index.md",
        ]
        documents = [" ".join(path.read_text(encoding="utf-8").split()) for path in paths]

        for document in documents:
            self.assertIn("--schema-version 3", document)
            self.assertIn("bash scripts/verify.sh", document)
            self.assertIn("skips `final_test` by default", document)
            self.assertIn("ONECODE_RUN_ROUTER_V3_FINAL_TEST=1", document)
            self.assertIn("future fresh, explicitly authorized one-shot release evaluation", document)
            self.assertIn("Do not set it for the current rollout", document)


if __name__ == "__main__":
    unittest.main()
