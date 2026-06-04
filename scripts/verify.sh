#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHONPATH=src python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check --registry catalog --bundles bundles/index.json >/dev/null
python3 -m json.tool schemas/skill-manifest.schema.json >/dev/null
python3 -m json.tool schemas/registry-index.schema.json >/dev/null
python3 -m json.tool schemas/verify-report.schema.json >/dev/null
python3 -m json.tool examples/sanitization-report.example.json >/dev/null
python3 -m json.tool examples/registry-index.example.json >/dev/null
python3 -m json.tool examples/verify-report.example.json >/dev/null
if command -v rg >/dev/null 2>&1; then
  ! rg -n "TODO|FIXME|PLACEHOLDER|TBD|待定" . --glob '!scripts/verify.sh'
fi
