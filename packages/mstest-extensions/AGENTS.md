# MSTest Extensions

Plugin sources: `skills/mstest/` and `skills/mstest-assertions/`; portable manifest:
`plugin.json`. Keep both independently usable, with each reference owned once.
`mstest` owns the API catalog, implementation/execution/review workflows and runner
probes. `mstest-assertions` owns precise built-in assertion semantics and examples.

`README.md` records verification commands and dated evidence. The solution includes
an intentionally failing probe executable; verify it with
`scripts/verify_mstest_probes.py`, not a whole-solution test run.
`scripts/package_plugin.py` builds the account-upload archive. No release.sh exists.

Regenerate `mstest/references/public-api.md` with `make update-mstest-api`; never
edit it by hand. Use `make check`, `make test`, `make check-mstest-api` and
`make verify-assertions`. The assertion probes pin their .NET 11 SDK in
`skills/mstest-assertions/examples/global.json`; runner probes retain the package's
.NET 10 SDK. Root `make check-skills` runs the unmodified upstream validator;
`make check-docs` also enforces local reference closure for both skills.
