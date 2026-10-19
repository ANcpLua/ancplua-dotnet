---
type: llm
---
PASS if the answer says the AL0xxx IDs were renumbered in 2.0 (look them up in the migration catalog, AL0017->AL1600 and AL0018->AL1601) so the NoWarn entries are dead, and that AL1600 reports on Directory.Packages.props so a [*.cs] section never reaches it (needs a global config or NoWarn). FAIL if it says both suppressions work.
