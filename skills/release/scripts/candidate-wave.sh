#!/usr/bin/env bash
# Runs one candidate verification wave in a consumer repository against locally packed packages.
# Usage: candidate-wave.sh <consumer-repo> <wave-name> --feed <dir with .nupkg> --ids <glob>[,<glob>] -- <command...>
#   <glob> uses NuGet packageSourceMapping syntax: an exact id or a prefix ending in '*'.
# Layout under <consumer-repo>/artifacts/candidate/:
#   packages/  the repository's candidate package cache, reused across waves; each wave first evicts
#              every version of the --ids packages, so restore can only take them from this wave's feed
#   <wave>/    NuGet.Config, run.log and identity.json survive; feed/ and build/ are removed at the end
# The command runs in <consumer-repo> with NUGET_PACKAGES and RestoreConfigFile exported, plus
# CANDIDATE_WAVE_DIR (keep results there) and CANDIDATE_ARTIFACTS (pass it to --artifacts-path).
# Exit: the command's code; 2 usage or precondition error; 3 a candidate restored with other bytes.
set -euo pipefail
shopt -s nullglob

usage() { echo "usage: $0 <consumer-repo> <wave-name> --feed <dir> --ids <glob>[,<glob>] -- <command...>" >&2; exit 2; }
die() { echo "candidate-wave: $*" >&2; exit 2; }
lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }
json() { local s=$1; s=${s//\\/\\\\}; s=${s//\"/\\\"}; s=${s//$'\n'/\\n}; s=${s//$'\r'/\\r}; s=${s//$'\t'/\\t}; printf '"%s"' "$s"; }
xml() { local s=$1; s=${s//&/&amp;}; s=${s//</&lt;}; s=${s//>/&gt;}; s=${s//\"/&quot;}; printf '%s' "$s"; }
sha512() { openssl dgst -sha512 -binary "$1" | openssl base64 -A; }
utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }

[[ $# -ge 2 ]] || usage
repo=$1 wave_name=$2
shift 2
feed_source='' ids=''
while [[ $# -gt 0 ]]; do
  case $1 in
    --feed) [[ $# -ge 2 ]] || usage; feed_source=$2; shift 2 ;;
    --ids) [[ $# -ge 2 ]] || usage; ids=$2; shift 2 ;;
    --) shift; break ;;
    *) usage ;;
  esac
done
[[ $# -gt 0 && -n $feed_source && -n $ids ]] || usage
[[ -d $repo ]] || die "consumer repository not found: $repo"
[[ -d $feed_source ]] || die "feed directory not found: $feed_source"
[[ $wave_name =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && $wave_name != packages ]] || die "invalid wave name: $wave_name"
command -v openssl >/dev/null || die "openssl is required"
command -v unzip >/dev/null || die "unzip is required"

repo=$(cd "$repo" && pwd)
root="$repo/artifacts/candidate"
cache="$root/packages"
wave="$root/$wave_name"
[[ ! -e $wave ]] || die "wave already exists, choose a new name: $wave"
IFS=',' read -r -a globs <<<"$ids"
for glob in "${globs[@]}"; do
  [[ $glob =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]*\*?$ ]] || die "invalid --ids pattern '$glob': use an id or an id prefix ending in '*'"
done

# Read each candidate's identity from its nuspec and require that the source mapping routes it to this feed.
nupkgs=("$feed_source"/*.nupkg)
[[ ${#nupkgs[@]} -gt 0 ]] || die "no .nupkg in $feed_source"
pkg_ids=() pkg_versions=() pkg_files=()
for nupkg in "${nupkgs[@]}"; do
  [[ $nupkg == *.symbols.nupkg ]] && continue
  nuspec=$(unzip -p "$nupkg" '*.nuspec' 2>/dev/null) || die "no nuspec in $nupkg"
  id=$(printf '%s' "$nuspec" | sed -n 's:.*<id>\([^<]*\)</id>.*:\1:p' | head -1)
  version=$(printf '%s' "$nuspec" | sed -n 's:.*<version>\([^<]*\)</version>.*:\1:p' | head -1)
  [[ -n $id && -n $version ]] || die "cannot read id and version from $nupkg"
  routed=0
  for glob in "${globs[@]}"; do
    # shellcheck disable=SC2053 # the glob is a pattern on purpose
    [[ $(lower "$id") == $(lower "$glob") ]] && routed=1
  done
  [[ $routed -eq 1 ]] || die "$id is not covered by --ids '$ids', so restore would take it from nuget.org"
  pkg_ids+=("$id") pkg_versions+=("$version") pkg_files+=("$(basename "$nupkg")")
done

# One wave at a time per repository: eviction must not race another wave's restore.
mkdir -p "$root"
mkdir "$root/.lock" 2>/dev/null || die "another wave holds $root/.lock (remove it if no wave is running)"
trap 'rm -rf "$wave/feed" "$wave/build"; rmdir "$root/.lock" 2>/dev/null || true' EXIT

mkdir -p "$wave/feed" "$wave/build" "$cache"
cp "${nupkgs[@]}" "$wave/feed/"
for glob in "${globs[@]}"; do
  for dir in "$cache"/$(lower "$glob"); do
    echo "evict $dir"
    rm -rf "$dir"
  done
done

{
  printf '<?xml version="1.0" encoding="utf-8"?>\n<configuration>\n'
  printf '  <config><add key="globalPackagesFolder" value="%s" /></config>\n' "$(xml "$cache")"
  printf '  <packageSources>\n    <clear />\n'
  printf '    <add key="candidate" value="%s" />\n' "$(xml "$wave/feed")"
  printf '    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" />\n  </packageSources>\n'
  printf '  <packageSourceMapping>\n    <packageSource key="candidate">\n'
  for glob in "${globs[@]}"; do printf '      <package pattern="%s" />\n' "$(xml "$glob")"; done
  printf '    </packageSource>\n    <packageSource key="nuget.org">\n      <package pattern="*" />\n'
  printf '    </packageSource>\n  </packageSourceMapping>\n</configuration>\n'
} >"$wave/NuGet.Config"

head=$(git -C "$repo" rev-parse HEAD 2>/dev/null || echo unknown)
dirty=false
[[ -n $(git -C "$repo" status --porcelain 2>/dev/null) ]] && dirty=true
started=$(utc)
command_text=$(printf '%q ' "$@")

set +e
(
  cd "$repo" &&
    NUGET_PACKAGES="$cache" RestoreConfigFile="$wave/NuGet.Config" \
      CANDIDATE_WAVE_DIR="$wave" CANDIDATE_ARTIFACTS="$wave/build/" "$@"
) 2>&1 | tee "$wave/run.log"
code=${PIPESTATUS[0]}
set -e

# Prove which bytes restore used: NuGet records each extracted package's SHA-512 beside it.
packages_json='' mismatch=0
for i in "${!pkg_ids[@]}"; do
  id=$(lower "${pkg_ids[$i]}") version=$(lower "${pkg_versions[$i]}")
  expected=$(sha512 "$wave/feed/${pkg_files[$i]}")
  record="$cache/$id/$version/$id.$version.nupkg.sha512"
  restored=null
  if [[ -f $record ]]; then
    if [[ $(tr -d '[:space:]' <"$record") == "$expected" ]]; then restored=true; else restored=false mismatch=1; fi
  fi
  [[ -z $packages_json ]] || packages_json+=','
  packages_json+="{\"id\":$(json "${pkg_ids[$i]}"),\"version\":$(json "${pkg_versions[$i]}"),\"sha512\":$(json "$expected"),\"restoredMatches\":$restored}"
done

cat >"$wave/identity.json" <<EOF
{
  "wave": $(json "$wave_name"),
  "repository": $(json "$repo"),
  "head": $(json "$head"),
  "dirty": $dirty,
  "command": $(json "${command_text% }"),
  "started": $(json "$started"),
  "finished": $(json "$(utc)"),
  "exitCode": $code,
  "packages": [$packages_json]
}
EOF

if [[ $mismatch -eq 1 ]]; then
  echo "candidate-wave: a candidate was restored with bytes other than the feed's; see $wave/identity.json" >&2
  [[ $code -ne 0 ]] || code=3
fi
echo "candidate-wave: exit $code; evidence in $wave"
exit "$code"
