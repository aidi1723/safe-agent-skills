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


if __name__ == "__main__":
    unittest.main()
