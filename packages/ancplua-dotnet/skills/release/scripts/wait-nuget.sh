#!/bin/sh
# Waits until nuget.org serves a package version through both the flat container (used by
# restore) and the registration leaf (used by PackageMetadataResource and most tools).
# Usage: wait-nuget.sh <PackageId> <version> [timeout-seconds, default 1200]
# Exit: 0 indexed, 1 timeout, 2 usage error.
set -u
[ $# -ge 2 ] || { echo "usage: $0 <PackageId> <version> [timeout-seconds]" >&2; exit 2; }
id=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
version=$(printf '%s' "$2" | tr '[:upper:]' '[:lower:]')
timeout=${3:-1200}
flat="https://api.nuget.org/v3-flatcontainer/$id/index.json"
leaf="https://api.nuget.org/v3/registration5-gz-semver2/$id/$version.json"
start=$(date +%s)
flat_ok=0
while :; do
  now=$(date +%s)
  elapsed=$((now - start))
  if [ "$flat_ok" -eq 0 ] && curl -fsS "$flat" 2>/dev/null | grep -q "\"$version\""; then
    flat_ok=1
    echo "flat container: $id $version after ${elapsed}s"
  fi
  if [ "$flat_ok" -eq 1 ]; then
    code=$(curl -s -o /dev/null -w '%{http_code}' --compressed "$leaf")
    if [ "$code" = 200 ]; then
      echo "registration: $id $version after ${elapsed}s"
      exit 0
    fi
  fi
  if [ "$elapsed" -ge "$timeout" ]; then
    echo "timeout after ${elapsed}s: flat=$flat_ok registration=not yet" >&2
    exit 1
  fi
  sleep 15
done
