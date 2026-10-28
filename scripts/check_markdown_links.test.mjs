import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { checkLinks } from "./check_markdown_links.mjs";

function fixture(t, markdown) {
  const root = mkdtempSync(join(tmpdir(), "ancplua-links-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const document = join(root, "source.md");
  writeFileSync(document, markdown);
  writeFileSync(join(root, "destination.md"), "# API `T`\n\n## Repeated\n\n## Repeated\n");
  return checkLinks(root, document);
}
test("local references and GitHub URLs resolve against the same checkout", t => {
  assert.deepEqual(fixture(t, "[local](destination.md#api-t)\n[remote](https://github.com/ANcpLua/ancplua-dotnet/blob/main/destination.md#repeated-1)"), []);
});
test("stale repository URLs fail even without HTTP access", t => {
  assert.match(fixture(t, "[old](https://github.com/ANcpLua/ancplua-dotnet/blob/main/old.md)")[0], /missing destination/);
});
test("reference-style links validate target anchors", t => {
  assert.match(fixture(t, "[section][api]\n\n[api]: destination.md#missing")[0], /missing heading anchor/);
});
test("links in code examples are not treated as navigation", t => {
  assert.deepEqual(fixture(t, "```md\n[example](not-a-file.md)\n```\n\n`[inline](missing.md)`"), []);
});
test("missing relative files fail", t => {
  assert.match(fixture(t, "[missing](old.md)")[0], /missing destination/);
});
