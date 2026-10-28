---
name: codex-native-messaging
description: Inspect existing native Codex threads, queue messages, resume conversations, or coordinate bounded fan-out while preserving verified identities and delivery semantics. Use for Codex thread messaging and handoffs, not general application development.
---

# Native Codex messaging

Use the host's native thread tools when available. They already know the running
server and expose bounded reads, thread creation and message delivery. Inspect
the installed CLI/protocol before using version-specific fallbacks.

## Identity and continuity

- Use verified thread UUIDs. Names, model labels, `/root`, and matching working
  directories are not unique identities.
- Keep thread ID, session ID, parent and fork source separate. A shared MCP
  process's environment may identify its launcher rather than its caller.
- `codex resume <uuid>` reconnects to an existing conversation. A disconnected
  terminal does not establish that its agent stopped.
- Read bounded metadata and the relevant recent turns. Do not copy whole chat
  histories into prompts or edit Codex's private SQLite/JSONL storage.

## Messages and fan-out

1. Resolve the explicit recipient UUID and the transport authorized by the user.
   For a configured server, use the documented `--remote` option consistently
   for discovery and sending.
2. Send through the native tool. If the installed CLI is needed, pass literal
   arguments rather than interpolating a message into a shell:

   ```sh
   codex queue --thread <verified-thread-uuid> --message <literal-message>
   ```

   Do not silently switch to `--last`, create a replacement thread or change its
   model to work around a delivery failure.
3. Record the native receipt when available and verify an actual response before
   claiming acknowledgement. Queue acceptance, arrival in a model turn and
   completion are separate facts. A timeout after submission is uncertain
   delivery, not proof that retrying is safe. Track an independent outcome per
   target for fan-out.

Host forwarding can provide native sender provenance. A textual source reference
or an ordinary CLI queue receipt does not manufacture that provenance.

## Starting or inspecting another agent

Create an agent when requested. Check the current model catalogue for the exact
model, reasoning effort and service tier; do not assume every model supports
every speed. Verify the effective start response. Explicit `default` speed is
different from inheriting an accelerated tier.

Keep delegated prompts focused on the user's objective. For an evaluation of
natural skill discovery, do not name the target skill or preload its answer.
Distinguish the available skill catalogue from evidence that a skill was read.

For protocol details and evidence boundaries, see
[protocol-notes.md](references/protocol-notes.md). The observations there are
version-specific, not promises about future client releases.
