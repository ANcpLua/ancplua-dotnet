---
name: csharp-refactoring
description: Refactor C# and reconcile stale constants, dead checks and abandoned code, including indirect production uses. Use for renames, moves, deduplication, exhaustive cleanup, generated declarations and runtime/API contracts. MSTest test design and review belong to mstest-extensions.
license: Apache-2.0
---

# C# refactoring

## Process

1. **Map the change.** Find the declaration, binding references, generator inputs
   and affected TFMs or `#if` branches. Identify which contracts must stay stable
   and which changes the user authorized. A compile-clean rename alone does not
   establish compatibility with runtime consumers.
2. **Edit the owner.** Prefer IDE/Roslyn rename or compiler-checked binding edits.
   Include partial declarations; change generator inputs rather than generated
   output. Extract shared behavior toward its existing owner, preserving each
   caller's inputs, evaluation order and side effects.
3. **Verify the boundary.** Use the repository's affected build/test entrypoint
   for each changed target. Reuse its compilation evidence instead of building
   twice. Check the runtime contracts below when touched; report unverified
   branches explicitly. Keep authorized behavior changes distinct from the
   mechanical refactor without refusing the rest of the task.

## Contracts the compiler cannot settle

| Boundary | Check |
| --- | --- |
| Serialization, configuration, reflection, DI or `dynamic` | Names may be data. Preserve external names through existing metadata, or migrate their consumers when that change is authorized. |
| Public API, nullable annotations, parameter names | Include source/binary compatibility and named arguments; check the repository's API record when present. |
| Type moved between assemblies | A same-name move may need `TypeForwardedTo` in the original assembly; a rename needs a different compatibility decision. |
| Generated/partial code, friends, conditional builds | Follow generator ownership, `InternalsVisibleTo`, all declarations and each affected compilation. |
| Wrapper removal or type merge | Retain compatibility adapters only for a real consumer boundary. Remove internal dead indirection once its callers are migrated. |

## Constants and abandoned code

For exhaustive cleanup, use [constant reconciliation](references/constant-reconciliation.md).
Account for every declaration in scope, including retained and unresolved items;
do not stop at an easy deletion shortlist. Use [performance](../performance/SKILL.md)
for production telemetry and profiles when deciding which checks are expensive.

For MSTest validation or changes to test code, select the focused skill through
[companion routing](../audit/references/mstest-routing.md). Package/framework
upgrades use [nuget-versions](../nuget-versions/SKILL.md).
