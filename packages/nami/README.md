# nami

One portable plugin with five skills:

| Skill | Purpose |
| --- | --- |
| [C# unions](plugins/nami/skills/csharp-union-types/SKILL.md) | C# 15 unions, closed hierarchies, matching and serialization |
| [MSTest](plugins/nami/skills/mstest/SKILL.md) | Version-checked MSTest APIs, assertions, configuration and review |
| [MSTest assertions](plugins/nami/skills/mstest-assertions/SKILL.md) | The most precise MSTest 4.5.1 assertion for each contract, with executable examples and AOT analysis |
| [Fixture scope](plugins/nami/skills/fixture-scope/SKILL.md) | Explicit ownership, shared inputs and cleanup |
| [Native Codex messaging](plugins/nami/skills/codex-native-messaging/SKILL.md) | Verified thread identity, queue/resume semantics and bounded fan-out |

The package is listed in the central `ancplua-dotnet` marketplace. This repository
has no standalone marketplace. Install it with `codex plugin add nami@ancplua-dotnet`
after registering the central catalog. The package uses portable `plugin.json` and
`skills/`. The [format decision](plugin-design.md) records the checked layout.
The checks below do not install or register plugins.

```sh
make check
make test
make verify-assertions
make verify-fixtures
make verify-union
```

`make check` validates package structure, local links and exported union hashes.
`make verify-assertions` runs the standalone MSTest 4.5.1 examples and positive/negative
AOT-analysis probes in temporary projects. The assertion skill contains its own
examples, verifier and references; it needs no application or sibling skill.
`make verify-fixtures` builds and runs the fixture example in a temporary directory.
`make verify-union` runs the pinned compiler and runtime probes, including replacing
only the library underneath an unchanged consumer. Its temporary reports are deleted
when the command returns.

The union source remains the canonical Nami `.agents/skills/csharp-union-types` directory selected through `UNION_SOURCE`. Use
`make check-union-sync` to compare it and `make sync-union` to explicitly export it
into this plugin package. It does not create another standalone checkout.
Override `UNION_SOURCE` if the canonical source is elsewhere. Only when deliberately
maintaining another distribution, pass `UNION_CHECKOUT=/absolute/path` to include
that additional export. Plugin use does not need either external checkout.

MSTest's generated API reference is maintained separately from its lifecycle
guidance. `make update-mstest-api` regenerates it from the configured release tags;
`make check-mstest-api` compares without writing. Python dependencies are locked
with uv. Supporting files belong to their individual skill.
