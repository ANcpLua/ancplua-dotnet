# Candidate waves

A candidate wave restores a consumer repository against packages you packed but haven't
published, then runs that consumer's gate. It proves the exact `.nupkg` bytes before nuget.org
makes the version immutable.

## Rules

- **Exact bytes.** The consumer restores each candidate from the wave's feed and nowhere else:
  no project reference, no cached public release, no earlier candidate of the same version.
  Package source mapping routes the candidate ids to the feed; eviction removes every cached
  version of those ids before the wave starts. Every wave of one release can carry the same
  version with different contents, and NuGet never re-extracts a version it already has.
- **One cache per consumer.** `artifacts/candidate/packages` is reused across waves. Third-party
  packages stay in it, so a wave downloads only what changed. A fresh cache per wave costs
  gigabytes (every runtime pack and native dependency again) and proves nothing extra.
- **Evidence, not outputs.** A wave keeps `NuGet.Config`, `run.log`, results you write to
  `$CANDIDATE_WAVE_DIR` and `identity.json`: repository HEAD, dirty flag, command, exit code,
  each candidate's id, version and SHA-512, and whether the restored bytes match. The copied feed
  and the build output under `$CANDIDATE_ARTIFACTS` are removed when the wave ends, pass or fail.
- **Shared caches stay.** `~/.nuget/packages` and the HTTP cache belong to the user; the wave
  never reads candidates from them and never clears them.

## Running one

```bash
skills/release/scripts/candidate-wave.sh ~/src/consumer namespace-fix \
  --feed ~/src/library/artifacts/package/release \
  --ids 'Acme.Telemetry.*' -- \
  bash -c 'dotnet test --artifacts-path "$CANDIDATE_ARTIFACTS" --results-directory "$CANDIDATE_WAVE_DIR/results"'
```

The command runs without a shell, so wrap it in `bash -c '...'` with single quotes whenever it
names `$CANDIDATE_ARTIFACTS` or `$CANDIDATE_WAVE_DIR`; a build entrypoint (Fallout, `make`) can
read them from the environment instead. Restore picks up the wave's `NuGet.Config` through the
exported `RestoreConfigFile` and `NUGET_PACKAGES`; a repository that sets `RestoreConfigFile`
itself needs `-p:RestoreConfigFile="$CANDIDATE_WAVE_DIR/NuGet.Config"` inside that `bash -c`.

Give each wave a new name; the script refuses an existing one so earlier evidence survives.
One wave runs at a time per consumer (`artifacts/candidate/.lock`), because eviction would race
another wave's restore.

Exit codes: the command's own code, `2` for a usage or precondition error (wave exists, lock
held, a candidate id outside `--ids`), `3` when the command passed but a candidate was restored
with bytes other than the feed's.

## Afterwards

Report each wave by its `identity.json`. A wave whose `restoredMatches` is `null` never restored
that candidate, so it proves nothing about it. Old wave directories hold only evidence; delete
them when the release they verified is published and reported.
