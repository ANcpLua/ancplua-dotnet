import { Client, StreamableHTTPClientTransport, SSEClientTransport, SdkErrorCode } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { spawn } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync, mkdtempSync, rmSync, existsSync } from 'node:fs';
import { resolve, dirname, basename, join } from 'node:path';
import { tmpdir } from 'node:os';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { z } from 'zod';

const { values } = parseArgs({ options: {
  plan: { type: 'string', default: 'plan.json' }, engine: { type: 'string', default: 'sdk' },
  era: { type: 'string', default: 'modern' }, report: { type: 'string', default: 'results/report.json' },
  timeout: { type: 'string', default: '15000' }, receipts: { type: 'string' }, mcpdo: { type: 'string' },
  'allow-writes': { type: 'boolean' }, 'allow-destructive': { type: 'boolean' },
  'allow-model-calls': { type: 'boolean' }, 'model-budget': { type: 'string', default: '2' },
} });
const engine = values.engine! as 'sdk' | 'mcpdo' | 'inspector' | 'claude-code';
if (!['sdk', 'mcpdo', 'inspector', 'claude-code'].includes(engine) || !['modern', 'legacy', 'auto'].includes(values.era!)) throw new Error('Unsupported engine or era');
const timeout = Number(values.timeout);
if (!Number.isFinite(timeout) || timeout < 1 || timeout > 600000) throw new Error('timeout must be 1..600000 ms');
const planPath = resolve(values.plan!);
const planSchema = z.object({
  schema_version: z.literal(1),
  binding: z.object({ integration_id: z.string(), source_revision: z.string(), input_sha256: z.string(), inventory_sha256: z.string() }),
  connection: z.record(z.string(), z.any()), hosts: z.array(z.string()),
  tools: z.array(z.object({ name: z.string().regex(/^[A-Za-z0-9_.-]{1,128}$/) }).passthrough()),
  cases: z.array(z.object({ id: z.string(), tool: z.string(), kind: z.enum(['valid', 'invalid', 'boundary', 'workflow']), effect: z.enum(['read', 'write', 'destructive', 'unknown']), arguments: z.any(),
    expected: z.object({ kind: z.enum(['success', 'tool_error', 'protocol_error', 'timeout']), structured: z.unknown().optional(), text_contains: z.string().optional(),
      max_text_chars: z.number().nonnegative().optional(), text_length: z.number().nonnegative().optional(), max_duration_ms: z.number().positive().optional(), code: z.union([z.string(), z.number()]).optional() }).nullable(),
    timeout_ms: z.number().int().min(1).max(600000).optional(),
    engines: z.array(z.enum(['sdk', 'mcpdo', 'inspector', 'claude-code'])).optional(),
  }).passthrough()),
  receipt_file: z.string().nullable().optional(),
  source_files: z.array(z.object({ path: z.string(), sha256: z.string() })).optional(),
});
const plan = planSchema.parse(JSON.parse(readFileSync(planPath, 'utf8')));
const reportPath = resolve(values.report!);
if (reportPath === planPath || existsSync(reportPath)) throw new Error('Choose a new report path; never overwrite plans or prior evidence');
const evidenceDir = reportPath + '.evidence';
mkdirSync(dirname(reportPath), { recursive: true });
mkdirSync(evidenceDir, { recursive: false, mode: 0o700 });
const scratch = mkdtempSync(join(tmpdir(), 'ss-'));
const stable = (x: any): any => Array.isArray(x) ? x.map(stable) : x !== null && typeof x === 'object' ? Object.fromEntries(Object.keys(x).sort().map(k => [k, stable(x[k])])) : x;
const equal = (a: any, b: any) => JSON.stringify(stable(a)) === JSON.stringify(stable(b));
const hash = (x: any) => createHash('sha256').update(JSON.stringify(stable(x))).digest('hex');
const report: any = { schema_version: 1, binding: plan.binding, engine, requested_era: values.era,
  surface: engine === 'claude-code' ? 'claude-code' : 'direct-protocol', started_at: new Date().toISOString(),
  cases: [], inventory: { status: 'Not run' }, negotiated_era: null, continuous_monitoring: false };
const receipts = values.receipts ?? plan.receipt_file;
const receiptPath = receipts ? resolve(dirname(planPath), receipts) : undefined;
const readReceipts = () => receiptPath && existsSync(receiptPath) ? readFileSync(receiptPath, 'utf8').split('\n').filter(Boolean) : [];
let receiptCursor = readReceipts().length;
const childEnv: Record<string, string> = {};
const headers: Record<string, string> = {};
let blocked: string | undefined;
for (const file of plan.source_files ?? []) {
  const path = resolve(dirname(planPath), file.path);
  if (!existsSync(path) || createHash('sha256').update(readFileSync(path)).digest('hex') !== file.sha256)
    blocked = 'Source changed; regenerate the plan and relevant evidence';
}
for (const [target, source] of Object.entries(plan.connection.env_from ?? {})) {
  if (!process.env[String(source)]) blocked = `Missing environment variable ${source}`;
  else childEnv[target] = process.env[String(source)]!;
}
for (const [target, source] of Object.entries(plan.connection.headers_from_env ?? {})) {
  if (!process.env[String(source)]) blocked = `Missing environment variable ${source}`;
  else headers[target] = process.env[String(source)]!;
}
const connection = plan.connection;
const serverCwd = resolve(dirname(planPath), connection.cwd ?? '.');
const config = { mcpServers: { submission_test: connection.transport === 'stdio'
  ? { command: connection.command, args: connection.args ?? [], cwd: serverCwd, env: childEnv }
  : { type: connection.transport === 'sse' ? 'sse' : 'http', url: connection.url, headers } } };
const configPath = join(scratch, 'connection.json');
writeFileSync(configPath, JSON.stringify(config), { mode: 0o600 });
const daemonEnv = { ...process.env, MCP_STORAGE_DIR: scratch, MCP_INSPECTOR_DAEMON_DIR: scratch,
  MCP_INSPECTOR_SECRET_STORE: 'file', MCP_INSPECTOR_SECRET_FILE: join(scratch, 'secrets.json'),
  MCP_INSPECTOR_SECRET_KEY: randomUUID(), MCP_AUTO_OPEN_ENABLED: '0' };
delete (daemonEnv as Record<string, string | undefined>).MCP_INSPECTOR_SECRET_KEY_FILE;
// These subprocesses use argument arrays, never a shell or an interpolated command.
async function command(argv: string[], maxMs = timeout + 15000, env = process.env) {
  return await new Promise<{ code: number; stdout: string; stderr: string; timedOut: boolean }>((done) => {
    const child = spawn(argv[0], argv.slice(1), { cwd: serverCwd, env, stdio: ['ignore', 'pipe', 'pipe'], detached: process.platform !== 'win32' });
    let stdout = '', stderr = '', timedOut = false;
    const stop = () => { try { process.platform === 'win32' ? child.kill('SIGTERM') : process.kill(-child.pid!, 'SIGTERM'); } catch {} };
    const timer = setTimeout(() => { timedOut = true; stop(); }, maxMs);
    child.stdout.on('data', d => { stdout += d; if (stdout.length > 8 * 1024 * 1024) stop(); });
    child.stderr.on('data', d => { stderr += d; if (stderr.length > 8 * 1024 * 1024) stop(); });
    child.on('error', error => { clearTimeout(timer); done({ code: 127, stdout, stderr: error.message, timedOut }); });
    child.on('close', code => { clearTimeout(timer); done({ code: code ?? 1, stdout, stderr, timedOut }); });
  });
}
const npmPrefix = ['npm', 'exec', '--yes', '--package=@modelcontextprotocol/inspector@2.10.1', '--'];
const mcpdoPrefix = values.mcpdo ? [resolve(values.mcpdo)] : [...npmPrefix, 'mcpdo'];
const mcpdo = (args: string[]) => command([...mcpdoPrefix, '--format', 'json', '--stored-auth-only', ...args], timeout + 20000, daemonEnv);
const inspector = (args: string[]) => command([...npmPrefix, 'mcp-inspector', '--cli', '--config', configPath, '--server', 'submission_test', '--protocol-era', values.era!, '--format', 'json', '--stored-auth-only', ...args], timeout + 20000, daemonEnv);
function parse(text: string) { try { return JSON.parse(text.trim()); } catch { return undefined; } }
function outcome(result: any, error?: any): any {
  if (error) return { kind: error.code === SdkErrorCode.RequestTimeout ? 'timeout' : 'protocol_error', code: error.code ?? null };
  if (result?.elicitationPending || result?.pendingAuth) return { kind: 'pending', result };
  return { kind: result?.isError ? 'tool_error' : 'success', result };
}
function processOutcome(p: {code: number; stdout: string; stderr: string; timedOut: boolean}, unwrap = false) {
  const raw = parse(p.stdout);
  const result = unwrap ? raw?.result ?? raw : raw;
  if (p.timedOut) return { kind: 'timeout' };
  if (p.code === 5) return { kind: 'tool_error', result };
  if (p.code !== 0 || result === undefined) return { kind: [3, 4, 127].includes(p.code) ? 'blocked' : 'protocol_error', code: p.code };
  return outcome(result);
}
function assertions(actual: any, expected: any, elapsed: number) {
  const checks: any[] = [{ check: 'kind', expected: expected.kind, observed: actual.kind, passed: expected.kind === actual.kind }];
  const result = actual.result;
  const text = (result?.content ?? []).filter((c: any) => c.type === 'text').map((c: any) => c.text).join('\n');
  if ('structured' in expected) checks.push({ check: 'structured', passed: equal(expected.structured, result?.structuredContent) });
  if ('text_contains' in expected) checks.push({ check: 'text_contains', passed: text.includes(expected.text_contains) });
  if ('code' in expected) checks.push({ check: 'error_code', passed: expected.code === actual.code });
  if ('max_text_chars' in expected) checks.push({ check: 'max_text_chars', observed: [...text].length, passed: [...text].length <= expected.max_text_chars });
  if ('text_length' in expected) checks.push({ check: 'text_length', observed: [...text].length, passed: [...text].length === expected.text_length });
  if ('max_duration_ms' in expected) checks.push({ check: 'max_duration_ms', observed: elapsed, passed: elapsed <= expected.max_duration_ms });
  return checks;
}
let client: Client | undefined;
let currentTest: any;
let unansweredElicitation = false;
let connected = false;
let advertised: any[] = [];
function artifact(index: number, data: any) {
  const file = join(evidenceDir, String(index).padStart(4, '0') + '.json');
  const bytes = JSON.stringify(data, null, 2) + '\n';
  writeFileSync(file, bytes, { mode: 0o600 });
  return { file: basename(evidenceDir) + '/' + basename(file), sha256: createHash('sha256').update(bytes).digest('hex') };
}
async function claudeCall(test: any): Promise<any> {
  if (!values['allow-model-calls']) return { kind: 'blocked', reason: 'Pass --allow-model-calls for real Claude Code verification' };
  const tool = 'mcp__submission_test__' + test.tool;
  const prompt = `Call ${tool} exactly once with these JSON arguments: ${JSON.stringify(test.arguments)}. Do not substitute a calculation or a prose answer for the tool call. Report the tool result briefly.`;
  const p = await command(['claude', '-p', prompt, '--strict-mcp-config', '--mcp-config', configPath,
    '--tools', '', '--allowedTools', tool, '--permission-mode', 'dontAsk', '--no-session-persistence',
    '--output-format', 'stream-json', '--verbose', '--max-budget-usd', values['model-budget']!], Math.max(timeout, 120000));
  const events = p.stdout.split('\n').map(parse).filter(Boolean);
  const uses = events.flatMap(e => e.message?.content ?? []).filter(c => c.type === 'tool_use' && c.name === tool && equal(c.input, test.arguments));
  const results = events.flatMap(e => e.message?.content ?? []).filter(c => c.type === 'tool_result' && uses.some(u => u.id === c.tool_use_id));
  if (p.code !== 0 || uses.length !== 1 || results.length !== 1) return { kind: 'blocked', reason: 'No unique matching real tool-use/result pair', trace: events };
  const r = results[0];
  const text = typeof r.content === 'string' ? r.content : (r.content ?? []).map((c: any) => c.text ?? '').join('\n');
  const decoded = parse(text);
  const normalized = decoded?.content ? decoded : { content: [{ type: 'text', text }], structuredContent: decoded, isError: !!r.is_error };
  return { ...outcome(normalized), trace: events, tool_use_id: uses[0].id };
}
try {
  if (!connection.transport || !(connection.command || connection.url)) blocked = 'Missing connection';
  if (!blocked && engine === 'sdk') {
    const mode = values.era === 'modern' ? { pin: '2026-07-28' } : values.era === 'auto' ? 'auto' : 'legacy';
    client = new Client({ name: 'submission-studio', version: '2.0.0' }, { versionNegotiation: { mode }, capabilities: { elicitation: { form: {} } } });
    client.setRequestHandler('elicitation/create', async () => {
      if (currentTest?.elicitation_response) return { action: 'accept' as const, content: currentTest.elicitation_response };
      unansweredElicitation = true;
      return { action: 'cancel' as const };
    });
    const transport = connection.transport === 'stdio'
      ? new StdioClientTransport({ command: connection.command, args: connection.args ?? [], cwd: serverCwd, env: childEnv, stderr: 'pipe' })
      : connection.transport === 'sse' ? new SSEClientTransport(new URL(connection.url), { requestInit: { headers } })
      : new StreamableHTTPClientTransport(new URL(connection.url), { requestInit: { headers } });
    await client.connect(transport);
    connected = true; report.negotiated_era = client.getProtocolEra();
    advertised = (await client.listTools()).tools;
  } else if (!blocked && engine === 'mcpdo') {
    // Connect is always a separate operation: exit zero can mean pending auth.
    const p = await mcpdo(['--config', configPath, 'connect', 'submission_test', '--era', values.era!]);
    const c = processOutcome(p);
    const errorCode = parse(p.stderr)?.error?.code;
    const safeCode = typeof errorCode === 'string' && /^[A-Za-z0-9_.-]{1,100}$/.test(errorCode) ? errorCode : null;
    report.connection_attempt = { exit_code: p.code, timed_out: p.timedOut, outcome: c.kind, error_code: safeCode };
    if (c.kind !== 'success') blocked = safeCode ? `mcpdo connection unavailable: ${safeCode}` : 'mcpdo connection unavailable or pending authentication';
    else {
      connected = true;
      const list = processOutcome(await mcpdo(['@submission_test', 'tools/list']));
      if (list.kind !== 'success' || !Array.isArray(list.result?.tools)) blocked = 'mcpdo inventory unavailable';
      else advertised = list.result.tools;
      const info = parse((await mcpdo(['connections/show', 'submission_test'])).stdout);
      report.connection_info = info;
      report.negotiated_era = info?.protocolEra ?? info?.connection?.protocolEra ?? null;
    }
  } else if (!blocked && engine === 'inspector') {
    const list = processOutcome(await inspector(['--method', 'tools/list']), true);
    if (list.kind !== 'success' || !Array.isArray(list.result?.tools)) blocked = 'Inspector inventory unavailable';
    else { advertised = list.result.tools; connected = true; report.negotiated_era = null; report.negotiation_note = 'One-shot output did not establish negotiated era'; }
  }
  const wanted = plan.tools.map(t => t.name).sort();
  const found = advertised.map(t => t.name).sort();
  if (engine !== 'claude-code') {
    report.negotiation_status = report.negotiated_era ? 'Observed' : 'Not run';
    if (values.era === 'modern' && report.negotiated_era && report.negotiated_era !== 'modern') blocked = 'Observed era does not match the required modern era';
  }
  report.inventory = { status: engine === 'claude-code' ? 'Not run' : blocked ? 'Blocked' : equal(wanted, found) ? 'Passed' : 'Failed', expected: wanted, observed: engine === 'claude-code' || !connected ? null : found, source: engine === 'claude-code' || !connected ? 'unobserved' : 'live' };
  if (!blocked && engine !== 'claude-code' && !equal(wanted, found)) blocked = 'Live inventory differs from the plan; regenerate cases';
} catch (error: any) { blocked = `Connection unavailable (${error.code ?? error.name})`; report.inventory = { status: 'Blocked', reason: blocked }; }

try {
  for (const [index, test] of plan.cases.entries()) {
    if (Array.isArray(test.engines) && !test.engines.includes(engine)) continue;
    if (engine === 'claude-code' && !['valid', 'workflow'].includes(test.kind)) continue;
    const row: any = { id: test.id, tool: test.tool, kind: test.kind, status: 'Not run', server_confirmation: 'Not run' };
    let reason = blocked;
    if (!test.arguments || !test.expected) reason = 'Missing input fixture or expected outcome';
    if (!['read', 'write', 'destructive'].includes(test.effect)) reason = 'Unknown side effects';
    if (test.effect === 'write' && !values['allow-writes']) reason = 'Write execution not enabled';
    if (test.effect === 'destructive' && !values['allow-destructive']) reason = 'Destructive execution not enabled';
    if (!plan.tools.some(t => t.name === test.tool)) reason = 'Unknown tool';
    if (test.task && engine === 'sdk') reason = 'Use mcpdo for this task-augmented fixture';
    if (test.expected?.kind === 'success' && !['structured', 'text_contains', 'max_text_chars', 'text_length'].some(k => k in test.expected!)) reason = 'Success needs a result assertion';
    if (reason) { row.status = 'Blocked'; row.reason = reason; report.cases.push(row); continue; }
    const start = Date.now();
    currentTest = test; unansweredElicitation = false;
    let actual: any;
    try {
      if (engine === 'sdk') actual = outcome(await client!.callTool({ name: test.tool, arguments: test.arguments }, { timeout: Number(test.timeout_ms ?? timeout) }));
      else if (engine === 'mcpdo') {
        actual = processOutcome(await mcpdo(['@submission_test', 'tools/call', ...(test.task ? ['--task'] : []), test.tool, ...Object.entries(test.arguments).map(([key, value]) => `${key}:=${JSON.stringify(value)}`)]));
        const pending = actual.result?.elicitationPending;
        const elicitationId = pending?.elicitationId ?? actual.result?.elicitationId;
        if (actual.kind === 'pending' && elicitationId) {
          const id = elicitationId;
          if (test.elicitation_response) actual = processOutcome(await mcpdo(['elicitation/respond', id, JSON.stringify(test.elicitation_response)]));
          else await mcpdo(['elicitation/respond', id, '--cancel']);
        }
      } else if (engine === 'inspector') actual = processOutcome(await inspector(['--method', 'tools/call', '--tool-name', test.tool, '--tool-args-json', JSON.stringify(test.arguments)]), true);
      else actual = await claudeCall(test);
    } catch (error) { actual = outcome(undefined, error); }
    if (unansweredElicitation) actual = { ...actual, kind: 'pending', reason: 'No fixture-authorized elicitation response' };
    row.elapsed_ms = Date.now() - start;
    row.assertions = assertions(actual, test.expected, row.elapsed_ms);
    row.text_characters = [...(actual.result?.content ?? []).filter((c: any) => c.type === 'text').map((c: any) => c.text).join('\n')].length;
    row.status = ['blocked', 'pending'].includes(actual.kind) ? 'Blocked' : row.assertions.every((a: any) => a.passed) ? 'Passed' : 'Failed';
    if (actual.reason) row.reason = actual.reason;
    const fresh = readReceipts();
    if (receiptPath) {
      row.server_confirmation = fresh.slice(receiptCursor).map(parse).some(r => r?.tool === test.tool && equal(r.arguments, test.arguments)) ? 'Passed' : test.kind === 'invalid' ? 'Not applicable' : 'Not observed';
      receiptCursor = fresh.length;
    }
    row.evidence = artifact(index, { binding: plan.binding, engine, case_id: test.id, tool: test.tool, arguments: test.arguments, actual, assertions: row.assertions });
    report.cases.push(row);
  }
} catch (error: any) {
  report.fatal = { name: error.name, code: error.code ?? null };
} finally {
  await client?.close().catch(() => undefined);
  if (engine === 'mcpdo') {
    if (connected) await mcpdo(['disconnect', 'submission_test']);
    // This daemon belongs to this run's private directory, never the user's shared daemon.
    await mcpdo(['daemon', 'stop']);
  }
  rmSync(scratch, { recursive: true, force: true });
  report.finished_at = new Date().toISOString();
  report.status = report.fatal || report.cases.some((r: any) => r.status === 'Failed') || report.inventory.status === 'Failed' ? 'Failed'
    : !report.cases.length || report.cases.some((r: any) => r.status !== 'Passed') || blocked || (engine !== 'claude-code' && values.era === 'modern' && report.negotiated_era !== 'modern') ? 'Incomplete' : 'Passed';
  report.summary = Object.fromEntries(['Passed', 'Failed', 'Blocked', 'Not run'].map(s => [s, report.cases.filter((r: any) => r.status === s).length]));
  report.dependencies = {};
  for (const pkg of ['client', 'server']) {
    const path = resolve(dirname(fileURLToPath(import.meta.url)), '../node_modules/@modelcontextprotocol', pkg, 'package.json');
    if (existsSync(path)) report.dependencies[pkg] = JSON.parse(readFileSync(path, 'utf8')).version;
  }
  writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n', { mode: 0o600 });
  console.log(JSON.stringify({ report: reportPath, status: report.status, summary: report.summary }));
  process.exitCode = report.status === 'Passed' ? 0 : report.status === 'Failed' ? 1 : 2;
}

