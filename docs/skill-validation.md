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

`mstest` owns API/version questions; `mstest-writing-tests` owns implementing tests;
`mstest-assertions` owns precise assertion choices and corrections. Report-only
assertion assessment stays in `mstest-assertion-review`. Read supporting references
only for the current task; don't preload every sibling skill.

## Upstream validator experiment — 2026-10-28

The official [dotnet/skills validator](https://github.com/dotnet/skills/blob/main/eng/skill-validator/src/README.md)
provides a token-free static `check` and a separate model-based `evaluate` command.
The latter compares baseline, individual skill and whole-plugin behavior; it is
not implied by a passing linter or executable example suite.

The official `skill-validator-nightly` macOS ARM64 archive published on 2026-10-27
was checked against its published SHA-256:
`c3deb61c0de0b98838cbf2c808a1f6cd683edd912fd1766d351226b6cd51674d`.

Its static check of the eleven MSTest and three Nami skills returned **exit 1**:
37 errors, all rejecting parent-directory links to sibling skills. The shared
MSTest references deliberately ship together in one plugin. This validator's
single-skill portability rule therefore does not accept the package's layout.
The full local output is retained in `artifacts/skill-validator/upstream-check.json`.
It is not reported as a passing check or installed as a silently weakened CI gate.
The repository instead verifies those targets and package contents directly.

The check also returned heuristic suggestions such as adding numbered steps or
code blocks. Those are not evidence that a short review skill needs extra prose.
No fresh model-selection or baseline-versus-skill quality evaluation was run.

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
