#!/bin/sh
set -eu

if [ $# -lt 1 ]; then
  printf '%s\n' "usage: task_pack.sh <task> [--format markdown|json] [--max-skills N]" >&2
  exit 2
fi

TASK=$1
shift

FORMAT=markdown
MAX_SKILLS=8

while [ $# -gt 0 ]; do
  case "$1" in
    --format)
      FORMAT=${2:-}
      shift 2
      ;;
    --max-skills)
      MAX_SKILLS=${2:-}
      shift 2
      ;;
    *)
      printf '%s\n' "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ -n "${SAFE_AGENT_SKILLS_HOME:-}" ]; then
  PROJECT_DIR=$SAFE_AGENT_SKILLS_HOME
else
  PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../../../.." && pwd)
fi

if [ ! -d "$PROJECT_DIR/catalog" ] || [ ! -d "$PROJECT_DIR/src" ]; then
  printf '%s\n' "Safe-Agent-Skills repository not found. Set SAFE_AGENT_SKILLS_HOME=/path/to/safe-agent-skills." >&2
  exit 2
fi

cd "$PROJECT_DIR"

PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m onecode_skill_sanitizer task-pack "$TASK" \
  --registry catalog \
  --include-bundles \
  --bundles bundles/index.json \
  --router scenario \
  --max-skills "$MAX_SKILLS" \
  --format "$FORMAT"
