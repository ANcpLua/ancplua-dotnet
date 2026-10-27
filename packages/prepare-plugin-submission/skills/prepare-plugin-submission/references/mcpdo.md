# Connector testing with mcpdo

Use experimental `mcpdo` for authorized live connector tests, regardless of the
server's implementation language. Choose the client by the lifetime the test needs:

| Test | Client |
| --- | --- |
| One request or an independent CI assertion | `mcp-inspector --cli`: connect, request, disconnect. |
| Several calls sharing a connection, elicitation, or supported task/subscription flows | `mcpdo`: a named connection held by the automatically started `mcpdod` daemon. |

Both commands ship in `@modelcontextprotocol/inspector`. A persistent connection
does not imply persistent application state or support for every protocol feature.

## Read the installed guide first

Verify the current package release and record the version used for evidence.
Version 2.10.1 was checked on 2026-10-13. For a temporary, reproducible invocation:

```sh
npm exec --yes --package=@modelcontextprotocol/inspector@2.10.1 -- mcpdo --help
npm exec --yes --package=@modelcontextprotocol/inspector@2.10.1 -- mcpdo agent-help
```

If `mcpdo` is installed, use it directly. Recheck the version instead of treating
this snapshot as permanently current. `agent-help --skill-path` locates the
package's installable skill; `agent-help --instructions` emits project guidance.
Read that guidance before driving unfamiliar commands. Installing another skill
or changing project-wide instructions is a separate requested change.

## Work through one named connection

Inspect the relevant catalog/config entry, then connect as its own command:

```sh
mcpdo connect my-server --era modern --format json
```

Inspect the returned state before proceeding. `pendingAuth: true` may accompany
exit zero: relay the sign-in URL promptly and resume after sign-in. Do not chain
`connect` with `&&` and a tool call, or reconnect to repair a pending sign-in.
Use `--stored-auth-only` when the test requires existing noninteractive access.

Once connected, run separate commands against the explicit name. These examples
assume an actual configured `my-server` whose inventory contains `echo`:

```sh
mcpdo @my-server tools/list --format json
mcpdo @my-server tools/call echo message:=hi --format json
mcpdo connections/show my-server --format json
mcpdo disconnect my-server --format json
```

Use the real tool and argument schema, and inspect each result before the next
step. `@name` or `--connection name` prevents accidental use of a different
connection; non-TTY calls normally reject an omitted name. Keep that default.
JSON output is the payload itself, without the one-shot CLI's `result` wrapper.
Record selected/negotiated era; mcpdo selects it with `connect --era`, while the
Inspector CLI uses `--protocol-era`. Use modern by default; legacy/auto are explicitly selected compatibility tests.

## Handle pending work as pending

In a noninteractive call, `elicitationPending` plus `elicitationId` means the
command returned but the tool call is parked on the daemon. Read the question
and schema. Answer from known facts and existing authorization; obtain a missing
user decision instead of automatically approving it.

Use `mcpdo elicitation/respond "$elicitation_id" field:=value --format json` for form answers.
For example, `approved:=true` is appropriate only if that is the requested field
and approval is already authorized. `--decline` handles form refusal; `--cancel`
ends either mode. URL mode uses `--done` only after the interaction is completed.
Inspect the response: it can be the final result or another question.

Each connection allows one parked elicitation; other calls on it are refused
until resolved, and the parked call expires after ten minutes. Continue unrelated
work through other connections as appropriate. Do not wait on an already-exited
CLI process or mark a pending result successful.

For a tool that advertises task support, `tools/call --task` waits for the final
result; it is not a fire-and-forget job launcher. Check the selected era and
actual server capabilities before using task or subscription commands.

## Recovery and cleanup

Allow mcpdo to re-dial a dropped transport on the next command. Reconnect for
`auth_required`; do not add a parallel reconnect loop. A daemon crash loses its
connections and requires establishing them again. Recovery does not prove an
interrupted write failed: check its outcome before repeating a mutation.

Use connection/daemon commands to inspect state rather than reading secret-store
files. Disconnect only the test connections you opened. A shared `daemon stop`
closes other connections too; the daemon normally exits after its last connection
has been closed for about a minute. Private daemon mode separates test state but
does not sandbox a stdio server or isolate it from processes with the same user.

Capture relevant results, failures, version, era, source revision, and cleanup.
Keep auth URLs, credentials, and daemon tokens out of committed evidence. mcpdo
testing and real-Claude host testing remain distinct evidence.

## Primary references

- [mcpdo connection client](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/mcpdo)
- [Inspector CLI](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/cli)
- [Inspector security and daemon behavior](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/security)
- [Protocol eras](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/protocol-eras)


## Agent command contract

Always pass `--format json` to operational commands, including `connect`, auth,
elicitation and cleanup. Help and `agent-help` are documentation commands.
Use `mcpdo help` and `mcpdo <command> --help` as the installed command authority.
Install with `npm install -g @modelcontextprotocol/inspector`, or use
`npx -p @modelcontextprotocol/inspector mcpdo ...`; record the actual version.

Name ad-hoc connections explicitly, for example
`mcpdo connect @api https://your-verified-endpoint/mcp --era modern --format json`.
Later commands require `@api` or `--conn api`. Do not set
`MCP_ALLOW_DEFAULT_CONNECTION=1` to bypass agent targeting. Use the real endpoint,
not this illustrative URL. `connections/list` and `servers/list` inspect state;
`disconnect api` closes your connection. Each accepts `--format json`.

`tools/call` uses positional `key:=value` arguments; check help for JSON values.
Do not assume the one-shot CLI's `--tool-name`, `--tool-arg`, `--strict`,
`--app-info`, or `--verify` flags exist in mcpdo. The stateless `--cli` makes one
`--method` call per process and handles mid-session auth step-up; use it for
that flow instead of inventing an mcpdo command.

`auth/list`, `auth/clear`, `connect --relogin`, and `disconnect --clear-auth`
inspect or refresh authorization. Clearing stored authorization is a separate
intentional action; routine recovery must not clear the user's tokens.
Edit the real catalog file `~/.mcp-inspector/mcp.json` only within the requested
scope, or use `--catalog` / `MCP_CATALOG_PATH`; mcpdo has no catalog editor.

Run `mcpdo daemon stop --format json` after an Inspector package upgrade when
stopping those connections is authorized. `eval "$(mcpdo private)"` is the
package's documented way to isolate a shell's daemon; inspect its output before
using it. The test runner uses a private temporary daemon directory instead.
A stdio process has the user's privileges. For an untrusted server, use a
reviewed container command such as
`mcpdo connect @x --format json --era modern -- docker run -i --rm --network none IMAGE`.
Replace IMAGE with the intended image and select mounts/network deliberately.
Daemon isolation alone does not sandbox that process.

If non-TTY `connect` returns `pendingAuth` and `authUrl` with exit zero, relay
the URL privately and wait for the user; do not reconnect. The next named
operation finishes the connection. If a form/URL elicitation is parked, respond
only from fixture facts or actual user input; `--done` confirms a completed URL
interaction, `--decline` refuses a form, and `--cancel` ends either mode. Never
accept a question because a process exited zero. Preserve ten-minute expiry,
one call per connection, and transparent transport recovery in test results.
