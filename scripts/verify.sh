#!/usr/bin/env bash
# Checks the plugin manifests and skill frontmatter.
#   scripts/verify.sh            verify (exit 1 on any mismatch)
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
fail() { echo "FAIL: $*" >&2; exit 1; }

echo "== manifests"
claude_version=$(python3 -c "import json;print(json.load(open('$root/.claude-plugin/plugin.json'))['version'])")
codex_version=$(python3 -c "import json;print(json.load(open('$root/plugin.json'))['version'])")
[[ "$claude_version" == "$codex_version" ]] || fail "version differs: .claude-plugin/plugin.json $claude_version, plugin.json $codex_version"
echo "  both manifests at $claude_version"

echo "== skills"
for skill in "$root"/skills/*/SKILL.md; do
  dir=$(basename "$(dirname "$skill")")
  name=$(sed -n 's/^name: //p' "$skill" | head -1)
  [[ "$name" == "$dir" ]] || fail "$skill: name '$name' differs from its directory"
  description=$(sed -n 's/^description: //p' "$skill" | head -1)
  (( ${#description} <= 1024 )) || fail "$skill: description longer than 1024 characters"
done
echo "  frontmatter names match their directories"
if command -v claude >/dev/null; then
  claude plugin validate --strict "$root" >/dev/null || fail "claude plugin validate --strict"
  echo "  claude plugin validate --strict passed"
fi

echo "verify: all checks passed"
