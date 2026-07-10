#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! python3 -c 'import jsonschema' >/dev/null 2>&1; then
  echo 'Install development checks with: python3 -m pip install -e ".[dev]"' >&2
  exit 2
fi

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
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 \
  --eval evals/multi-intent-gold.json >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer contract-check \
  --registry catalog \
  --bundles bundles/index.json \
  --scenario website-build-launch \
  --scenario code-review-hardening \
  --scenario codebase-change-lifecycle \
  --scenario skill-router-quality-review \
  --scenario open-source-release \
  --scenario rag-agent-knowledge-app \
  --scenario document-to-knowledge-base \
  --scenario security-agent-guardrails \
  --minimum-ratio 0.80 >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "build a landing page and prepare launch checks" \
  --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证" >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标" >/dev/null
python3 -m json.tool schemas/skill-manifest.schema.json >/dev/null
python3 -m json.tool schemas/sanitization-report.schema.json >/dev/null
python3 -m json.tool schemas/registry-index.schema.json >/dev/null
python3 -m json.tool schemas/verify-report.schema.json >/dev/null
python3 -m json.tool schemas/contract-v2.schema.json >/dev/null
PYTHONPATH=src python3 - <<'PY'
import json
from pathlib import Path

from jsonschema import Draft202012Validator, validators

contract_schema = json.loads(Path("schemas/contract-v2.schema.json").read_text(encoding="utf-8"))
manifest_schema = json.loads(Path("schemas/skill-manifest.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(contract_schema)
Draft202012Validator.check_schema(manifest_schema)
strict_type_checker = Draft202012Validator.TYPE_CHECKER.redefine(
    "integer", lambda checker, value: isinstance(value, int) and not isinstance(value, bool)
)
strict_validator = validators.extend(Draft202012Validator, type_checker=strict_type_checker)
contract_validator = strict_validator(contract_schema)
manifest_validator = strict_validator(manifest_schema)
validated = 0
for manifest_path in sorted(Path("catalog").glob("*/*/skill.json")):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contract = manifest.get("contract")
    if not isinstance(contract, dict) or contract.get("schema_version") != 2:
        continue
    contract_validator.validate(contract)
    manifest_validator.validate(manifest)
    validated += 1
if validated < 39:
    raise SystemExit(f"expected at least 39 Contract v2 manifests, validated {validated}")
PY
python3 -m json.tool examples/sanitization-report.example.json >/dev/null
python3 -m json.tool examples/registry-index.example.json >/dev/null
python3 -m json.tool examples/verify-report.example.json >/dev/null
if search_repo "TODO|FIXME|PLACEHOLDER|TBD|待定" "scripts/verify.sh"; then
  exit 1
fi
