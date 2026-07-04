#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

search_repo() {
  local pattern="$1"
  local exclude_path="${2:-}"
  if command -v rg >/dev/null 2>&1; then
    if [[ -n "$exclude_path" ]]; then
      rg -n "$pattern" . --glob '!.git/**' --glob "!$exclude_path"
    else
      rg -n "$pattern" . --glob '!.git/**'
    fi
    return
  fi
  if [[ -n "$exclude_path" ]]; then
    grep -RInE --exclude-dir=.git --exclude="$(basename "$exclude_path")" -- "$pattern" .
  else
    grep -RInE --exclude-dir=.git -- "$pattern" .
  fi
}

PYTHONPATH=src python3 -m compileall src tests
if python3 -m ruff --version >/dev/null 2>&1; then
  python3 -m ruff check .
fi
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m onecode_skill_sanitizer maintain-check \
  --registry catalog \
  --bundles bundles/index.json \
  --references external-references/index.json \
  --claude-skills-candidate-map docs/claude-skills-candidate-map.json >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer reference-check --references external-references/index.json >/dev/null
private_path_patterns=(
  '/[U]sers/'
  '大[字]典'
  '/one[ ]code/'
)
for private_path_pattern in "${private_path_patterns[@]}"; do
  if search_repo "$private_path_pattern"; then
    exit 1
  fi
done
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval \
  --eval evals/router-quality.json \
  --registry catalog \
  --bundles bundles/index.json >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "build a landing page and prepare launch checks" \
  --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证" >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标" >/dev/null
python3 -m json.tool schemas/skill-manifest.schema.json >/dev/null
python3 -m json.tool schemas/sanitization-report.schema.json >/dev/null
python3 -m json.tool schemas/registry-index.schema.json >/dev/null
python3 -m json.tool schemas/verify-report.schema.json >/dev/null
python3 -m json.tool examples/sanitization-report.example.json >/dev/null
python3 -m json.tool examples/registry-index.example.json >/dev/null
python3 -m json.tool examples/verify-report.example.json >/dev/null
if search_repo "TODO|FIXME|PLACEHOLDER|TBD|待定" "scripts/verify.sh"; then
  exit 1
fi
