#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "missing required command: $command_name" >&2
    exit 1
  fi
}

require_command rg

PYTHONPATH=src python3 -m compileall src tests
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
  if rg -n "$private_path_pattern" . --glob '!.git/**'; then
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
if rg -n "TODO|FIXME|PLACEHOLDER|TBD|待定" . --glob '!scripts/verify.sh'; then
  exit 1
fi
