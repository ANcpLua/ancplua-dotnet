#!/usr/bin/env bash
# Checks the facts this plugin states against the real toolchain.
#   scripts/verify.sh            verify (exit 1 on any mismatch)
#   scripts/verify.sh --update   rewrite fixtures/mstest-probe/help/*.txt from the current packages
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
probe="$root/fixtures/mstest-probe"
update=false
[[ "${1:-}" == "--update" ]] && update=true
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

echo "== MSTest.Sdk probe ($probe)"
cd "$probe"
props=$(dotnet msbuild MSTestProbe.csproj -getProperty:IsTestProject -getProperty:IsTestingPlatformApplication \
  -getProperty:OutputType -getProperty:IsPackable -getProperty:EnableMSTestRunner)
expect() { python3 -c "import json,sys;v=json.loads(sys.argv[1])['Properties'][sys.argv[2]];sys.exit(0 if v==sys.argv[3] else 1)" "$props" "$1" "$2" \
  || fail "MSTest.Sdk property $1 is not '$2' (skills/mstest section 1 relies on it)"; }
expect IsTestProject ""
expect IsTestingPlatformApplication true
expect OutputType Exe
expect IsPackable false
expect EnableMSTestRunner true
echo "  SDK defaults as documented"

for profile in Default AllMicrosoft; do
  dotnet build MSTestProbe.csproj -c Release -p:TestingExtensionsProfile=$profile -v q -nologo >/tmp/ancplua-dotnet-probe-build.txt 2>&1 \
    || { cat /tmp/ancplua-dotnet-probe-build.txt; fail "probe build ($profile): an API named in skills/mstest no longer compiles"; }
  options=$(./bin/Release/net10.0/MSTestProbe --help | grep -E '^\s+--' | awk '{print $1}' | sort -u)
  snapshot="help/$profile.txt"
  if $update; then
    printf '%s\n' "$options" > "$snapshot"
    echo "  $profile: wrote $snapshot ($(wc -l < "$snapshot" | tr -d ' ') options)"
  else
    diff <(printf '%s\n' "$options") "$snapshot" || fail "--help options for $profile differ from $snapshot (run with --update after checking the skill)"
    echo "  $profile: $(printf '%s\n' "$options" | wc -l | tr -d ' ') options match $snapshot"
  fi
done

dotnet test --project MSTestProbe.csproj -c Release --no-build >/tmp/ancplua-dotnet-probe-test.txt 2>&1 \
  || { cat /tmp/ancplua-dotnet-probe-test.txt; fail "probe tests"; }
echo "  probe tests: $(grep -E 'succeeded:' /tmp/ancplua-dotnet-probe-test.txt | tr -s ' ')"
echo "verify: all checks passed"
