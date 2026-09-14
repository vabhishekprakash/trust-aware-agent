#!/bin/sh
# Copies the project hooks into .git/hooks so git runs them.
# Run once after cloning:  sh scripts/hooks/install-hooks.sh

set -e
root=$(git rev-parse --show-toplevel)
hooks_dir=$(git rev-parse --git-path hooks)
case "$hooks_dir" in
  /*|?:*) ;;
  *) hooks_dir="$root/$hooks_dir" ;;
esac
mkdir -p "$hooks_dir"
for h in commit-msg pre-push; do
  cp "$root/scripts/hooks/$h" "$hooks_dir/$h"
  chmod +x "$hooks_dir/$h"
done
echo "installed commit-msg and pre-push into $hooks_dir"
