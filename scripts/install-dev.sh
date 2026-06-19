#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(dirname "$SCRIPT_DIR")
SKILLS_DIR="$REPO_ROOT/skills"

FORCE=false
if [ "${1:-}" = "--force" ]; then
  FORCE=true
fi

TARGETS=(
  "$HOME/.agents/skills"
  "$HOME/.claude/skills"
)

for target_dir in "${TARGETS[@]}"; do
  mkdir -p "$target_dir"
done

for skill_path in "$SKILLS_DIR"/*/; do
  [ -d "$skill_path" ] || continue
  name=$(basename "$skill_path")
  src=$(cd "$skill_path" && pwd)

  for target_dir in "${TARGETS[@]}"; do
    target="$target_dir/$name"

    if [ -e "$target" ] || [ -L "$target" ]; then
      if $FORCE; then
        rm -rf "$target"
        ln -s "$src" "$target"
        echo "Forced:  $target_dir/$name"
      else
        echo "Skip:    $target_dir/$name (already exists)"
      fi
    else
      ln -s "$src" "$target"
      echo "Linked:  $target_dir/$name"
    fi
  done
done
