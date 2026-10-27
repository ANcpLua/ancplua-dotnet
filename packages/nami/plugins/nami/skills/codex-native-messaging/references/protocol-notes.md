# Protocol observations

Verified locally with Codex CLI 0.164.0 on 2026-10-27.

- `codex app-server generate-json-schema --out <scratch-directory>` exposes the
  installed public protocol. Inspect its request/response definitions instead
  of guessing undocumented flags or editing application-private state.
- Bounded `thread/list` supports a cursor and `useStateDbOnly: true`. For recent
  activity, `thread/turns/list` supports a bounded limit and a summary view.
  A thread's preview is not necessarily its latest reply.
- Model discovery distinguishes supported reasoning efforts from service tiers.
  In the observed catalogue, GPT-6.1 Terra had `priority` but no `ultrafast` tier;
  GPT-6 Astra supported both. Recheck rather than copying these observations as
  permanent configuration.
- The public turn-start schema allows `effort`, `serviceTier` and
  `serviceTierForTurn`. The documented `default` tier selects standard speed;
  omitted values can inherit a previous choice. Confirm the returned metadata.
- The native host's forwarding path supplied `codexDelegation.sourceThreadId`.
  Ordinary third-party MCP calls must not be assumed to carry the same field.
- Native fan-out to two existing idle threads retained their IDs and history.
  This was not a test of every active/waiting state.
- The local `app-server proxy` path did not answer initialization in that run;
  public WebSocket requests over the advertised control socket worked. This is
  a client-version observation, not justification to patch or restart the user's
  daemon. Prefer the working host tools over adding a custom transport.

When durable questions are managed by a separate app, saving an answer, queueing
it to a thread and the agent continuing remain distinct operations. Persist small
explicit records and correlation IDs; do not keep an agent turn alive by polling
or sleeping just to preserve a UI question. Pending or missing answers are not
authorization.

Useful handoff content is the objective, current state, actual file paths and
verification evidence. A transcript link is a navigation reference, not automatic
context transfer. Never claim the same model identity across independent threads.
