#!/usr/bin/env bash
# Exercises skills/release/scripts/candidate-wave.sh offline: a fake feed, a stub restore, no dotnet.
#   scripts/test-candidate-wave.sh   (exit 1 on the first failed expectation)
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
wave_script="$root/skills/release/scripts/candidate-wave.sh"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
expect_code() { [[ $1 -eq $2 ]] || fail "$3: exit $1, expected $2"; }

repo="$work/consumer"
mkdir -p "$repo" "$work/nuspec"
git -C "$repo" init -q
git -C "$repo" -c user.name=test -c user.email=test@example.invalid commit -q --allow-empty -m init
cat >"$work/nuspec/Acme.Widgets.nuspec" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd">
  <metadata>
    <id>Acme.Widgets</id>
    <version>2.1.0</version>
    <dependencies><dependency id="Other.Lib" version="1.0.0" /></dependencies>
  </metadata>
</package>
EOF
mkdir -p "$work/feed"
(cd "$work/nuspec" && zip -q "$work/feed/Acme.Widgets.2.1.0.nupkg" Acme.Widgets.nuspec)
cache="$repo/artifacts/candidate/packages"
mkdir -p "$cache/acme.widgets/2.0.0" "$cache/other.lib/1.0.0"

# The stub plays restore: it extracts the candidate the way NuGet does and writes build output.
cat >"$work/restore-stub.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
grep -q '<package pattern="Acme.\*" />' "$RestoreConfigFile"
grep -q "<add key=\"candidate\" value=\"$CANDIDATE_WAVE_DIR/feed\" />" "$RestoreConfigFile"
target="$NUGET_PACKAGES/acme.widgets/2.1.0"
mkdir -p "$target" "$CANDIDATE_ARTIFACTS/bin" "$CANDIDATE_WAVE_DIR/results"
if [[ ${STUB_TAMPER:-0} == 1 ]]; then hash=AAAA; else
  hash=$(openssl dgst -sha512 -binary "$CANDIDATE_WAVE_DIR/feed/Acme.Widgets.2.1.0.nupkg" | openssl base64 -A)
fi
printf '%s' "$hash" >"$target/acme.widgets.2.1.0.nupkg.sha512"
echo binary >"$CANDIDATE_ARTIFACTS/bin/App.dll"
echo '<TestRun />' >"$CANDIDATE_WAVE_DIR/results/run.trx"
echo "stub restored in $PWD"
exit "${STUB_EXIT:-0}"
EOF
chmod +x "$work/restore-stub.sh"
run() { set +e; "$wave_script" "$repo" "$@" >"$work/out.log" 2>&1; local code=$?; set -e; echo "$code"; }

echo "== verified wave"
code=$(run first --feed "$work/feed" --ids 'Acme.*' -- "$work/restore-stub.sh")
expect_code "$code" 0 "verified wave"
wave="$repo/artifacts/candidate/first"
[[ ! -e $cache/acme.widgets/2.0.0 ]] || fail "older candidate version was not evicted"
[[ -d $cache/other.lib/1.0.0 ]] || fail "third-party package was evicted"
[[ -f $wave/NuGet.Config && -f $wave/results/run.trx ]] || fail "evidence missing"
[[ ! -e $wave/feed && ! -e $wave/build ]] || fail "feed or build output survived"
[[ ! -e $repo/artifacts/candidate/.lock ]] || fail "lock survived"
grep -q "stub restored in $repo" "$wave/run.log" || fail "run.log lacks the command output or the command ran elsewhere"
grep -q '"restoredMatches":true' "$wave/identity.json" || fail "identity.json does not prove the restored bytes"
grep -q '"exitCode": 0' "$wave/identity.json" || fail "identity.json lacks the exit code"
python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$wave/identity.json" || fail "identity.json is not JSON"

echo "== other bytes restored"
code=$(STUB_TAMPER=1 run tampered --feed "$work/feed" --ids 'Acme.*' -- "$work/restore-stub.sh")
expect_code "$code" 3 "tampered restore"
grep -q '"restoredMatches":false' "$repo/artifacts/candidate/tampered/identity.json" || fail "mismatch not recorded"

echo "== failing command"
code=$(STUB_EXIT=7 run failing --feed "$work/feed" --ids 'Acme.*' -- "$work/restore-stub.sh")
expect_code "$code" 7 "failing command"
[[ ! -e $repo/artifacts/candidate/failing/build ]] || fail "build output survived a failing command"

echo "== preconditions"
code=$(run first --feed "$work/feed" --ids 'Acme.*' -- true)
expect_code "$code" 2 "reused wave name"
code=$(run unmapped --feed "$work/feed" --ids 'Other.*' -- true)
expect_code "$code" 2 "candidate outside --ids"
grep -q 'would take it from nuget.org' "$work/out.log" || fail "unmapped candidate not explained"
code=$(run everything --feed "$work/feed" --ids '*' -- true)
expect_code "$code" 2 "bare '*' pattern"

echo "test-candidate-wave: all checks passed"
