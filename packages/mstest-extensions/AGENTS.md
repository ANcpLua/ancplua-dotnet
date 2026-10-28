# MSTest Extensions

Plugin source: `skills/mstest-extensions/`; portable manifest: `plugin.json`.
`README.md` records verification commands and dated evidence. The solution includes
an intentionally failing probe executable; verify it with
`scripts/verify_mstest_probes.py`, not a whole-solution test run.
`scripts/package_plugin.py` builds the account-upload archive. No release.sh exists.

All eleven skill directories belong to this package. `mstest` owns version-checked
API lookup and its generated `references/public-api.md`; regenerate it with
`make update-mstest-api`. `mstest-assertions` owns precise built-in assertion semantics
and its executable examples. Use `make check`, `make test`, `make check-mstest-api`
and `make verify-assertions` for these resources. The assertion probes pin their
.NET 11 SDK in `skills/mstest-assertions/examples/global.json`; runner probes retain
the package's .NET 10 SDK. Never edit the generated API table by hand.
