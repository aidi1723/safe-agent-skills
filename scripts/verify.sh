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
  if [[ -n "$exclude_path" ]]; then
    git grep -n -E -- "$pattern" -- . ":(exclude,literal)$exclude_path"
  else
    git grep -n -E -- "$pattern" -- .
  fi
}

assert_repo_has_no_matches() {
  local status
  if search_repo "$@"; then
    return 1
  else
    status=$?
  fi
  if [[ "$status" -eq 1 ]]; then
    return 0
  fi
  return "$status"
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
  assert_repo_has_no_matches "$private_path_pattern"
done
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval \
  --eval evals/router-quality.json \
  --registry catalog \
  --bundles bundles/index.json >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer router-eval-v2 \
  --eval evals/multi-intent-gold.json >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer schema-check --registry catalog >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer batch-check \
  --batches batches \
  --catalog catalog \
  --index batches/index.json >/dev/null
PYTHONPATH=src python3 -m onecode_skill_sanitizer depth-check \
  --catalog catalog \
  --policy catalog/depth-policy.json >/dev/null
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
  --invariants "不能泄露密钥；公开文案必须合规；必须响应式验证；必须核查来源证据；必须使用浏览器截图验证" \
  --format json | PYTHONPATH=src python3 -c '
import json
import sys

payload = json.load(sys.stdin)
expected = {
    "secret_redaction": "security-secret-context-redaction",
    "claims_compliance": "content-claims-compliance-filter",
    "responsive_check": "design-responsive-viewport-check",
    "source_check": "research-source-check",
    "browser_verification": "execution-playwright-browser-automation",
}
stages = ["preflight", "source", "planning", "production", "review", "verification", "handoff"]
stage_rank = {stage: rank for rank, stage in enumerate(stages)}
skills = {item["name"]: item for item in payload["selected_skills"]}
nodes = {node["id"]: node for node in payload["execution_graph"]["nodes"]}
graph_skills = {node["skill"] for node in nodes.values()}
records = {
    item["capability"]: item
    for item in payload["capability_resolution"]["capabilities"]
    if item.get("source") == "invariant"
}
if payload["routing_status"] != "complete":
    raise SystemExit("v2 invariant acceptance route is not complete")
if payload["routing_metrics"].get("overlap_policy") != "validated_not_applied":
    raise SystemExit("v2 overlap policy must be validated_not_applied")
for capability, skill in expected.items():
    if skill not in skills or skill not in graph_skills:
        raise SystemExit(f"missing invariant safeguard skill: {skill}")
    if records.get(capability, {}).get("status") != "covered":
        raise SystemExit(f"invariant capability is not covered: {capability}")
    node = next(node for node in nodes.values() if node.get("invariant_capability") == capability)
    contract = skills[skill].get("contract")
    if isinstance(contract, dict) and node["stage"] != contract["stage_hint"]:
        raise SystemExit(f"invariant contract stage mismatch: {capability}")
    if records[capability].get("stage") != node["stage"]:
        raise SystemExit(f"invariant stage mismatch: {capability}")
for edge in payload["execution_graph"]["edges"]:
    if stage_rank[nodes[edge["from"]]["stage"]] > stage_rank[nodes[edge["to"]]["stage"]]:
        raise SystemExit(f"backward stage edge: {edge}")
'
PYTHONPATH=src python3 -m onecode_skill_sanitizer smart \
  "复查 safe-agent-skills 项目是否达到智能选择和自动搭配 skill 的目标" >/dev/null
python3 -m json.tool schemas/skill-manifest.schema.json >/dev/null
python3 -m json.tool schemas/sanitization-report.schema.json >/dev/null
python3 -m json.tool schemas/registry-index.schema.json >/dev/null
python3 -m json.tool schemas/verify-report.schema.json >/dev/null
python3 -m json.tool schemas/contract-v2.schema.json >/dev/null
python3 -m json.tool schemas/intent-graph.schema.json >/dev/null
python3 -m json.tool schemas/task-pack-v2-selected-skill.schema.json >/dev/null
python3 -m json.tool schemas/task-pack-v2.schema.json >/dev/null
python3 -m json.tool schemas/batch-index.schema.json >/dev/null
python3 -m json.tool schemas/router-eval-suite.schema.json >/dev/null
python3 -m json.tool schemas/router-eval-review.schema.json >/dev/null
python3 -m json.tool catalog/depth-policy.json >/dev/null
PYTHONPATH=src python3 - <<'PY'
import json
from pathlib import Path

from jsonschema import Draft202012Validator, validators
from referencing import Registry, Resource

from onecode_skill_sanitizer.cli import build_task_pack_v2

contract_schema = json.loads(Path("schemas/contract-v2.schema.json").read_text(encoding="utf-8"))
intent_graph_schema = json.loads(Path("schemas/intent-graph.schema.json").read_text(encoding="utf-8"))
manifest_schema = json.loads(Path("schemas/skill-manifest.schema.json").read_text(encoding="utf-8"))
task_pack_schema = json.loads(Path("schemas/task-pack-v2.schema.json").read_text(encoding="utf-8"))
selected_skill_schema = json.loads(Path("schemas/task-pack-v2-selected-skill.schema.json").read_text(encoding="utf-8"))
router_eval_suite_schema = json.loads(Path("schemas/router-eval-suite.schema.json").read_text(encoding="utf-8"))
router_eval_review_schema = json.loads(Path("schemas/router-eval-review.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(contract_schema)
Draft202012Validator.check_schema(intent_graph_schema)
Draft202012Validator.check_schema(manifest_schema)
Draft202012Validator.check_schema(task_pack_schema)
Draft202012Validator.check_schema(selected_skill_schema)
Draft202012Validator.check_schema(router_eval_suite_schema)
Draft202012Validator.check_schema(router_eval_review_schema)
strict_type_checker = Draft202012Validator.TYPE_CHECKER.redefine(
    "integer", lambda checker, value: isinstance(value, int) and not isinstance(value, bool)
)
strict_validator = validators.extend(Draft202012Validator, type_checker=strict_type_checker)
contract_validator = strict_validator(contract_schema)
manifest_validator = strict_validator(manifest_schema)
schema_registry = Registry().with_resources(
    [
        (intent_graph_schema["$id"], Resource.from_contents(intent_graph_schema)),
        (selected_skill_schema["$id"], Resource.from_contents(selected_skill_schema)),
        (contract_schema["$id"], Resource.from_contents(contract_schema)),
        (manifest_schema["$id"], Resource.from_contents(manifest_schema)),
    ]
)
task_pack_validator = strict_validator(task_pack_schema, registry=schema_registry)
intent_graph_validator = strict_validator(intent_graph_schema)
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

task_pack = build_task_pack_v2(
    Path("catalog"),
    "构建官网，同时审计 skill 路由器，验证通过后发布更新",
    Path("bundles/index.json"),
)
task_pack_validator.validate(task_pack)
intent_graph_validator.validate(task_pack["intent_graph"])
for skill in task_pack["selected_skills"]:
    contract = skill.get("contract")
    if isinstance(contract, dict):
        contract_validator.validate(contract)
try:
    build_task_pack_v2(Path("catalog"), "", Path("bundles/index.json"))
except ValueError:
    pass
else:
    raise SystemExit("empty v2 task must fail before task-pack serialization")
PY
python3 -m json.tool examples/sanitization-report.example.json >/dev/null
python3 -m json.tool examples/registry-index.example.json >/dev/null
python3 -m json.tool examples/verify-report.example.json >/dev/null
assert_repo_has_no_matches "TODO|FIXME|PLACEHOLDER|TBD|待定" "scripts/verify.sh"
