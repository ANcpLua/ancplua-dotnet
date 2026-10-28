# Skill and documentation validation

## Repository checks

Run `npm ci --ignore-scripts` once, then `make check-docs`. The committed lockfile
pins markdownlint-cli2 0.24.0 and its parser dependencies. The same command runs
on pushes and pull requests; CI never applies automatic fixes.

- Markdownlint checks the maintained .NET skill/reference areas, package guidance
  and root documentation. Historical evaluation prompts, immutable union exports,
  the imported Submission Studio snapshot and the generated API table are outside
  this formatting pass. They retain their package-specific validation.
- The link checker parses Markdown rather than matching link-like code examples.
  It checks local files, reference-style links and GitHub heading anchors.
- URLs into `ANcpLua/ancplua-dotnet/blob/main` and `tree/main` resolve against this
  checkout, so stale cross-package links fail before a push. Other web URLs are
  not fetched by this offline check.
- `make check` validates the four package identities, skill counts, frontmatter
  names/descriptions, local references and portable resources. Archive verification
  includes the moved API generator template and the assertion examples.
- `make verify-nami` and `make verify-mstest` run the package's executable evidence.
  `make -C packages/mstest-extensions check-mstest-api` verifies generated API docs.

`mstest` owns API lookup, implementation, execution, extension and review workflows.
Each workflow remains a local reference loaded for its task. `mstest-assertions`
owns precise built-in assertion choices and corrections. Both are usable without
sibling skill files. The link checker enforces this boundary throughout their
Markdown references, including repository URLs that would otherwise hide a dependency.

## Upstream validator — 2026-10-28

The official [dotnet/skills validator](https://github.com/dotnet/skills/blob/main/eng/skill-validator/src/README.md)
provides a token-free static `check` and a separate model-based `evaluate` command.
The latter compares baseline, individual skill and whole-plugin behavior; it is
not implied by a passing linter or executable example suite.

The initial check of eleven MSTest and three Nami skills returned **37 errors**,
all from references that escaped their skill directories. Version 4.0.0 consolidates
the overlapping MSTest entrypoints into two self-contained skills. Shared resources
were moved to their single owner, and former entrypoints remain workflow references.
No reference trees were copied and no validator rules were disabled.

The same official macOS ARM64 binary published on 2026-10-27 now checks all **five
current MSTest/Nami skills with zero errors**. Its archive SHA-256 is
`c3deb61c0de0b98838cbf2c808a1f6cd683edd912fd1766d351226b6cd51674d`.
Five heuristic warnings remain: assertion-skill length and suggestions for numbered
steps or code blocks. These remain visible; short review guidance needs no filler.
No fresh model-selection or baseline-versus-skill quality evaluation was run.

Run `make check-skills` with Python 3.12+ and authenticated `gh`. The same command
runs in CI and fetches the current official `skill-validator-nightly` release,
selecting the platform asset by ID and verifying its published SHA-256. Archives
are cached by digest; updated nightlies get a new cache entry. The release identity
and full diagnostics are retained under `artifacts/skill-validator/` and uploaded
by CI. An upstream error, download failure, checksum mismatch or missing skill
fails the gate; there is no traversal exemption or ignored exit code.

To reuse an already verified binary locally:

```sh
python3 scripts/check_skills.py --validator /path/to/skill-validator
```

The gate retains its original MSTest/Nami scope; the other packages retain their
own validation. Consolidation changes the entrypoint count, not the covered
workflows. Local link closure and archive checks cover the moved references and
executable resources beyond the upstream entrypoint checks.

## Sources used for this setup

- [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices):
  coherent tasks, conditional references and improvement from actual execution.
- [dotnet/skills Markdown configuration](https://github.com/dotnet/skills/blob/main/.markdownlint-cli2.jsonc)
  and [workflow](https://github.com/dotnet/skills/blob/main/.github/workflows/markdownlint.yml):
  shared configuration and automated linting. This repository retains normal
  spacing, code-fence and table-validity checks rather than copying every exception.
- [dotnet/samples workflow](https://github.com/dotnet/samples/blob/main/.github/workflows/markdownlint.yml):
  run documentation checks on changes. Its older Node/tool versions were not copied.
- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2): pinned local
  dependency, configuration and the same CLI in developer and CI execution.
