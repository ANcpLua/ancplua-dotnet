import { McpServer, createMcpHandler } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import { toNodeHandler } from '@modelcontextprotocol/node';
import { createMcpExpressApp } from '@modelcontextprotocol/express';
import { z } from 'zod';
import { appendFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

// An opt-in sample-data receipt, separate from the MCP stdout protocol stream.
function receipt(tool: string, args: unknown) {
  const file = process.env.SUBMISSION_RECEIPTS_FILE;
  if (file) appendFileSync(file, JSON.stringify({
    timestamp: new Date().toISOString(), tool, arguments: args,
    arguments_sha256: createHash('sha256').update(JSON.stringify(args)).digest('hex'),
  }) + '\n', { mode: 0o600 });
}

export function createServer() {
  const server = new McpServer({ name: 'submission-starter', version: '1.0.0' });
  server.registerTool('add_numbers', {
    title: 'Add two numbers', description: 'Return the sum of two finite numbers.',
    inputSchema: z.object({ a: z.number().finite(), b: z.number().finite() }),
    outputSchema: z.object({ sum: z.number() }),
    annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
  }, async args => {
    receipt('add_numbers', args);
    const sum = args.a + args.b;
    if (!Number.isFinite(sum)) return { isError: true, content: [{ type: 'text', text: 'Sum exceeds the finite numeric range.' }] };
    return { content: [{ type: 'text', text: JSON.stringify({ sum }) }], structuredContent: { sum } };
  });
  return server;
}

if (process.argv.includes('--http')) {
  // Local development only. Add the deployment's identity provider before exposure.
  const app = createMcpExpressApp({ host: '127.0.0.1' });
  const handler = createMcpHandler(createServer);
  const nodeHandler = toNodeHandler(handler);
  app.all('/mcp', (req, res) => { void nodeHandler(req, res, req.body); });
  const listener = app.listen(Number(process.env.PORT ?? 3000), '127.0.0.1', () => {
    console.error(JSON.stringify({ listening: listener.address() }));
  });
  process.on('SIGTERM', () => { listener.close(); void handler.close(); });
} else {
  serveStdio(createServer, { onerror: error => console.error(error) });
}

