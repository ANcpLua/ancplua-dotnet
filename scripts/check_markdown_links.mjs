import { existsSync, readFileSync, statSync } from "node:fs";
import { resolve, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import MarkdownIt from "markdown-it";
import GithubSlugger from "github-slugger";

const parser = new MarkdownIt({ html: true });
function tokens(file) {
  const content = readFileSync(file, "utf8").replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, "");
  return parser.parse(content, {});
}
function anchors(file) {
  const result = new Set();
  const slugger = new GithubSlugger();
  const parsed = tokens(file);
  for (let i = 0; i < parsed.length; i++) {
    if (parsed[i].type === "heading_open") {
      const text = (parsed[i + 1].children ?? []).filter(t => ["text", "code_inline"].includes(t.type)).map(t => t.content).join("");
      result.add(slugger.slug(text));
    }
    for (const token of [parsed[i], ...(parsed[i].children ?? [])]) {
      if (token.type.startsWith("html_")) {
        for (const match of token.content.matchAll(/\b(?:id|name)=["']([^"']+)["']/g)) result.add(match[1]);
      }
    }
  }
  return result;
}
export function checkLinks(root, document) {
  const failures = [];
  const skill = /^(packages\/(?:ancplua-dotnet|mstest-extensions|prepare-plugin-submission)\/skills\/[^/]+)\//.exec(relative(root, document));
  const skillRoot = skill ? resolve(root, skill[1]) : undefined;
  const catalogFile = resolve(root, ".agents/plugins/marketplace.json");
  const packages = new Map(existsSync(catalogFile)
    ? JSON.parse(readFileSync(catalogFile, "utf8")).plugins.map(p => [p.name, p.source.path]) : []);
  for (const block of tokens(document)) {
    for (const token of block.children ?? []) {
      if (token.type === "code_inline") {
        const route = /^([a-z0-9-]+):([a-z0-9-]+)$/.exec(token.content);
        if (route && packages.has(route[1]) && !existsSync(resolve(root, packages.get(route[1]), "skills", route[2], "SKILL.md"))) {
          failures.push(`${token.content}: missing marketplace skill handoff`);
        }
      }
      if (!["link_open", "image"].includes(token.type)) continue;
      const link = token.attrGet(token.type === "image" ? "src" : "href");
      let target = link;
      const owned = /^https:\/\/github\.com\/ANcpLua\/ancplua-dotnet\/(?:blob|tree)\/main\/(.*)$/i.exec(link);
      if (owned) target = "/" + owned[1];
      else if (/^(?:[a-z][a-z\d+.-]*:|\/\/)/i.test(link)) continue;
      const [pathAndQuery, fragment] = target.split("#", 2);
      const path = decodeURIComponent(pathAndQuery.split("?", 1)[0]);
      const destination = path ? resolve(path.startsWith("/") ? root : dirname(document), path.replace(/^\//, "")) : document;
      if (skillRoot && (relative(skillRoot, destination) === ".." || relative(skillRoot, destination).startsWith("../"))) {
        failures.push(`${link}: leaves self-contained skill ${relative(root, skillRoot)}`);
      }
      if (!existsSync(destination)) failures.push(`${link}: missing destination ${relative(root, destination)}`);
      else if (fragment && destination.endsWith(".md") && statSync(destination).isFile()
               && !anchors(destination).has(decodeURIComponent(fragment))) failures.push(`${link}: missing heading anchor`);
    }
  }
  return failures;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  const files = execFileSync("git", ["ls-files", "--cached", "--others", "--exclude-standard", "-z"], { cwd: root, encoding: "utf8" }).split("\0");
  const selected = [...new Set(files)].filter(f => f.endsWith(".md") && existsSync(resolve(root, f)) && (
    !f.includes("/") || f.startsWith("docs/") ||
    f.startsWith("packages/ancplua-dotnet/") ||
    /^packages\/mstest-extensions\/(?:README.md|AGENTS.md|skills\/)/.test(f) ||
    /^packages\/nami\/[^/]+\.md$/.test(f) ||
    f.startsWith("packages/nami/plugins/nami/skills/fixture-scope/") ||
    f.startsWith("packages/nami/plugins/nami/skills/codex-native-messaging/") ||
    f.startsWith("packages/prepare-plugin-submission/skills/") ||
    f === "packages/prepare-plugin-submission/README.md"
  ));
  let count = 0;
  for (const file of selected) {
    for (const error of checkLinks(root, resolve(root, file))) {
      console.error(`${file}: ${error}`); count++;
    }
  }
  console.log(`Checked links and Markdown anchors in ${selected.length} files: ${count} failures.`);
  process.exitCode = count ? 1 : 0;
}
