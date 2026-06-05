#!/bin/sh
set -eu

TARGET_DIR=${1:-"${HOME}/.codex/skills"}
SKILL_NAME=safe-agent-router
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SKILL_DIR/../../.." && pwd)

mkdir -p "$TARGET_DIR"
rm -rf "$TARGET_DIR/$SKILL_NAME"
cp -R "$SKILL_DIR" "$TARGET_DIR/$SKILL_NAME"
chmod +x "$TARGET_DIR/$SKILL_NAME/scripts/task_pack.sh"

BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/safe-agent-router-task-pack" <<EOF
#!/bin/sh
export SAFE_AGENT_SKILLS_HOME="$PROJECT_DIR"
exec "$TARGET_DIR/$SKILL_NAME/scripts/task_pack.sh" "\$@"
EOF
chmod +x "$BIN_DIR/safe-agent-router-task-pack"

printf '%s\n' "Installed $SKILL_NAME to $TARGET_DIR/$SKILL_NAME"
printf '%s\n' "Installed command: $BIN_DIR/safe-agent-router-task-pack"
printf '%s\n' "Set PATH to include $BIN_DIR if needed."
