# Constants, dead checks and abandoned code

## Complete the inventory

For an exhaustive request, enumerate constants, constant-like static fields,
feature switches, guard predicates and abandoned implementations in the agreed
repositories and configurations. Record the revision, exclusions and scanned
projects/TFMs. Reconcile every production-referenced constant, even when retained.
A small set of obvious unused symbols is not a completed audit.

Trace binding references and transitive callers from production entrypoints.
Include aliases, wrappers, linked files, generated source and generator inputs,
conditional compilation, MSBuild/configuration substitution, DI, reflection,
serialization, native interop and external package consumers. Search values as
well as names when constants become protocol/configuration keys. Inlined public
constants may survive in already-built consumers. A text-search miss or one
successful build does not prove absence of use.

## Reconcile meaning and cost

For each entry, connect declaration -> direct/indirect uses -> reachable behavior.
Establish the actual value and predicate outcomes per supported configuration;
distinguish a permanently fixed branch from a rare fallback, safety invariant
or feature used only in another deployment. Follow abandoned paths far enough
to decide whether their owners, registrations and artifacts remain necessary.

When available, correlate production logs, metrics, trace/span paths and profiles
with the deployed revision, configuration and observation window. Profiles can
identify costly redundant checks, including repeated parsing, allocations,
locking and I/O. Missing or sampled telemetry cannot establish deadness; an
observed branch proves reachability, not necessity. Label source-only cost
estimates and missing coverage instead of presenting them as measurements.

## Finish with a reconciled ledger

Give each entry a disposition: retain (live contract), simplify (fixed/redundant),
remove (unreachable/abandoned), or unresolved (name the missing evidence).
Include declaration and caller locations, configuration, evidence, action and
measured cost where available. Totals must cover the inventory; unresolved items
remain visible rather than disappearing from the report. Continue through the
whole scope, stating concrete access blockers without claiming complete proof.

An audit produces this ledger. When edits are requested, remove or simplify the
owner and reconcile its transitive references, registrations and documentation.
Preserve expression side effects and evaluation order unless changing them is
authorized. Verify the affected production boundaries with the repository's
existing checks; use the MSTest companion for test design or execution.
