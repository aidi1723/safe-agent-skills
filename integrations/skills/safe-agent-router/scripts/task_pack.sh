#!/bin/sh
set -eu

if [ $# -lt 1 ]; then
  printf '%s\n' "usage: task_pack.sh <task> [--format markdown|json] [--max-skills N] [--schema-version 2|3] [--routing-examples PATH]" >&2
  exit 2
fi

TASK=$1
shift

FORMAT=markdown
MAX_SKILLS=8
SCHEMA_VERSION=2
ROUTING_EXAMPLES=catalog/routing-examples.json

while [ $# -gt 0 ]; do
  case "$1" in
    --format)
      if [ $# -lt 2 ]; then
        printf '%s\n' "missing value for --format" >&2
        exit 2
      fi
      FORMAT=$2
      shift 2
      ;;
    --max-skills)
      if [ $# -lt 2 ]; then
        printf '%s\n' "missing value for --max-skills" >&2
        exit 2
      fi
      MAX_SKILLS=$2
      shift 2
      ;;
    --schema-version)
      if [ $# -lt 2 ]; then
        printf '%s\n' "missing value for --schema-version" >&2
        exit 2
      fi
      case "$2" in
        2|3)
          SCHEMA_VERSION=$2
          ;;
        *)
          printf '%s\n' "unsupported schema version: $2" >&2
          exit 2
          ;;
      esac
      shift 2
      ;;
    --routing-examples)
      if [ $# -lt 2 ]; then
        printf '%s\n' "missing value for --routing-examples" >&2
        exit 2
      fi
      ROUTING_EXAMPLES=$2
      shift 2
      ;;
    *)
      printf '%s\n' "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SCRIPT_PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../../../.." && pwd)

if [ -d "$SCRIPT_PROJECT_DIR/catalog" ] && [ -d "$SCRIPT_PROJECT_DIR/src" ]; then
  PROJECT_DIR=$SCRIPT_PROJECT_DIR
elif [ -n "${SAFE_AGENT_SKILLS_HOME:-}" ]; then
  PROJECT_DIR=$SAFE_AGENT_SKILLS_HOME
else
  PROJECT_DIR=$SCRIPT_PROJECT_DIR
fi

if [ ! -d "$PROJECT_DIR/catalog" ] || [ ! -d "$PROJECT_DIR/src" ]; then
  printf '%s\n' "Safe-Agent-Skills repository not found. Set SAFE_AGENT_SKILLS_HOME=/path/to/safe-agent-skills." >&2
  exit 2
fi

cd "$PROJECT_DIR"

PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m onecode_skill_sanitizer smart "$TASK" \
  --registry catalog \
  --bundles bundles/index.json \
  --max-skills "$MAX_SKILLS" \
  --schema-version "$SCHEMA_VERSION" \
  --routing-examples "$ROUTING_EXAMPLES" \
  --format "$FORMAT"
