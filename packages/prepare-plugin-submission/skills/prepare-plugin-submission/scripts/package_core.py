"""Pure package resolution and validation. Inputs are byte mappings, outputs are data.

No file reads, network calls, commands, or claim of directory approval occur here.
"""

from __future__ import annotations
import hashlib
import ipaddress
import json
import re
import shlex
import struct
import unicodedata
from pathlib import PurePosixPath
from urllib.parse import urlsplit

SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SOURCES = {
    "format": "https://developers.openai.com/plugins/build/plugins",
    "openai": "https://developers.openai.com/plugins/deploy/submission",
    "openai-errors": "https://developers.openai.com/plugins/deploy/submission-errors",
    "claude": "https://claude.com/docs/plugins/pre-submission-checklist",
    "claude-format": "https://code.claude.com/docs/en/plugins-reference",
    "api": "https://developers.openai.com/api/docs/guides/tools-connectors-mcp",
    "desktop": "https://developers.openai.com/plugins/deploy/desktop-only",
}
RETRIEVED = "2026-10-13"
CATEGORIES = {
    "Productivity",
    "Creativity",
    "Developer Tools",
    "Business & Operations",
    "Data & Analytics",
    "Communication",
    "Education & Research",
    "Security",
    "Finance",
    "Healthcare",
    "Travel",
    "Entertainment",
    "Other",
}
SEMVER = r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"


def safe_path(value):
    return (
        isinstance(value, str)
        and bool(value)
        and "\\" not in value
        and "\x00" not in value
        and not re.match(r"^[A-Za-z]:", value)
        and not PurePosixPath(value).is_absolute()
        and ".." not in PurePosixPath(value).parts
    )


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def digest_files(files):
    digest = hashlib.sha256()
    for name, blob in sorted(files.items()):
        digest.update(name.encode() + b"\0" + hashlib.sha256(blob).digest())
    return digest.hexdigest()


class Checker:
    def __init__(self, files, target, profile, repository=None, repository_prefix=None,
                 submission_route="remote", desktop_allowlist=None, synthetic=False, rule_context=None):
        self.files = files
        self.target = target
        self.profile = profile
        self.submission_route = submission_route
        self.desktop_allowlist = desktop_allowlist
        self.synthetic = synthetic
        self.rule_context = rule_context
        self.desktop_eligible = False
        self.repository = repository
        self.repository_prefix = repository_prefix
        self.public = profile == "submission"
        self.issues = []
        self.checked = []
        self.unresolved = False
        self.servers = {}
        self.server_sources = {}
        self.config_sources = []
        self.hooks = []
        self.source = "openai" if target == "openai" else "claude"

    def issue(self, code, path, fix, severity="error", source=None, scope=None):
        # The static CLI remains available with historical provenance. The guided
        # runtime supplies live constraints instead of enforcing remembered limits.
        policy_only = (code in {'category_missing','category_unknown','too_many_prompts','prompt_mention',
            'public_local_mcp','remote_required','public_server_headers','public_lifecycle_hooks',
            'public_app_binding','review_case_count','invalid_icon_size'} or
            (path.startswith('interface.') and code in {'text_too_long','text_required'}))
        if self.rule_context is not None and policy_only:
            severity = 'warning'
        self.issues.append(
            {
                "code": code,
                "path": path,
                "severity": severity,
                "fix": fix,
                "source": SOURCES[source or self.source],
                "retrieved": "2026-10-16" if source == "desktop" else RETRIEVED,
                "scope": scope or ("directory" if self.public else "package"),
                "classification": "historical_guidance" if policy_only else "structural_check",
                "current_policy_verified": False,
            }
        )

    @property
    def remote_review(self):
        return self.unresolved or any(isinstance(s, dict) and "url" in s for s in self.servers.values())

    def route_checks(self):
        if self.submission_route not in ("remote", "desktop-only"):
            self.issue("submission_route_invalid", "submission_route", "Select remote or desktop-only.")
            return
        if not (self.public and self.target == "openai" and self.submission_route == "desktop-only"):
            return
        if self.rule_context is not None and not any('allowlist' in d.get('text','').lower()
                for d in self.rule_context.get('documents',[]) if d.get('status')=='current' and d.get('id')=='publication.desktop'):
            return
        local = any(isinstance(s, dict) and "command" in s for s in self.servers.values())
        if not local:
            if not self.settings.get("requires_local_executor"):
                self.issue("desktop_execution_missing", "submission_route", "Desktop-only needs a local MCP server or requires_local_executor.", source="desktop")
            return
        record = self.desktop_allowlist
        required = ("organization_id", "confirmed_by", "confirmed_at", "evidence_reference")
        valid = (isinstance(record, dict) and record.get("status") == "allowlisted"
                 and all(isinstance(record.get(k), str) and record[k].strip() for k in required))
        if valid:
            from datetime import datetime
            try:
                valid = datetime.fromisoformat(record["confirmed_at"].replace("Z", "+00:00")).tzinfo is not None
            except ValueError:
                valid = False
        if not valid:
            self.issue("desktop_allowlist_required", "submission_route", "Supply organization allowlist confirmation with observer, date and evidence reference; obtain approval through your OpenAI representative.", source="desktop")
        elif record.get("synthetic") is True and not self.synthetic:
            self.issue("synthetic_allowlist_rejected", "submission_route", "Synthetic allowlist records are only valid for an explicitly synthetic fixture check.", source="desktop")
        else:
            self.desktop_eligible = True
            self.checked.append("Desktop-only route selected; allowlist confirmation record inspected, not independently verified with OpenAI")

    def obj(self, value, path):
        if not isinstance(value, dict):
            self.issue("object_required", path, "Use a JSON object.")
            return {}
        return value

    def read_json(self, name):
        if name not in self.files:
            self.issue("file_missing", name, "Include this declared file.")
            return {}
        try:
            return self.obj(
                json.loads(self.files[name], object_pairs_hook=no_duplicates), name
            )
        except (ValueError, UnicodeError, RecursionError):
            self.issue(
                "invalid_json", name, "Use valid UTF-8 JSON without duplicate keys."
            )
            return {}

    def text(self, value, path, required=True, maximum=None, single=False):
        if not isinstance(value, str) or not value.strip():
            if required or value is not None:
                self.issue("text_required", path, "Provide nonblank text.")
            return False
        if maximum and len(value) > maximum:
            self.issue("text_too_long", path, f"Use at most {maximum} characters.")
        if any(ord(c) < 32 and c not in "\n\t\r" for c in value) or (
            single and any(c in value for c in "\n\r\t\u2028\u2029")
        ):
            self.issue(
                "invalid_text",
                path,
                "Remove unsupported control characters and line breaks.",
            )
        return True

    def reference(self, value, path):
        if not safe_path(value):
            self.issue("unsafe_reference", path, "Use a contained relative path.")
            return None
        name = str(PurePosixPath(value))
        if name not in self.files:
            self.issue("reference_missing", path, "Include the referenced file.")
            return None
        return name

    def url(self, value, path, remote=False):
        if (
            self.target == "claude"
            and remote
            and isinstance(value, str)
            and (value == "" or re.search(r"\$\{user_config\.[A-Za-z0-9_]+\}", value))
        ):
            token = r"\$\{user_config\.[A-Za-z0-9_]+\}"
            if value and not re.fullmatch(token, value):
                expanded = re.sub(token, "configured.example", value)
                try:
                    parsed = urlsplit(expanded)
                except ValueError:
                    self.issue("claude_url", path, "Use a syntactically valid configured URL.")
                    return
                allowed = {"https", "wss"} if self.public else {"https", "wss", "http", "ws"}
                if parsed.scheme not in allowed or not parsed.hostname or parsed.username or parsed.password or any(c.isspace() for c in expanded):
                    self.issue("claude_url", path, "Use a supported URL scheme around runtime substitutions.")
                    return
            self.issue(
                "runtime_url_unverified",
                path,
                "Resolve and test the configured URL in each intended host.",
                "unverified",
            )
            return
        if not self.text(value, path, maximum=1024, single=True):
            return
        try:
            u = urlsplit(value)
            host = u.hostname or ""
            _ = u.port
            schemes = (
                {"https", "wss"} if self.target == "claude" and remote else {"https"}
            )
            if not self.public and remote:
                schemes |= {"http", "ws"} if self.target == "claude" else {"http"}
            bad = (
                u.scheme not in schemes
                or not host
                or u.username is not None
                or u.password is not None
                or any(c.isspace() for c in value)
            )
            if self.public and not self.synthetic:
                bad = (
                    bad
                    or host
                    in {"localhost", "example.com", "example.org", "example.net"}
                    or host.endswith(
                        (
                            ".localhost",
                            ".local",
                            ".test",
                            ".invalid",
                            ".example",
                            ".example.com",
                            ".example.org",
                            ".example.net",
                        )
                    )
                )
                try:
                    bad = bad or not ipaddress.ip_address(host).is_global
                except ValueError:
                    pass
            if bad:
                raise ValueError()
        except ValueError:
            self.issue(
                (
                    "claude_url"
                    if self.target == "claude" and remote
                    else "public_https_required"
                ),
                path,
                "Use a supported absolute URL without credentials; public endpoints must be public and non-placeholder.",
            )

    def resolve_servers(self, declaration, origin, default=False):
        if isinstance(declaration, list):
            for item in declaration:
                self.resolve_servers(item, origin)
            return
        if isinstance(declaration, str):
            if declaration.endswith((".mcpb", ".dxt")) and self.format in {
                "claude",
                "claude-import",
            }:
                remote = declaration.startswith(("https://", "http://"))
                self.issue(
                    "mcp_bundle_unverified",
                    origin,
                    "Inspect this MCP bundle with the native host; its server configuration remains unresolved.",
                    (
                        "error"
                        if self.public and remote
                        else "hold" if self.public else "unverified"
                    ),
                    "claude",
                )
                self.unresolved = True
                return
            if not safe_path(declaration):
                self.issue(
                    "mcp_reference_unsupported",
                    origin,
                    "Use a contained MCP configuration path.",
                )
                self.unresolved = True
                return
            path = str(PurePosixPath(declaration))
            if path not in self.files:
                self.issue(
                    "mcp_reference_missing",
                    path,
                    "Restore the declared MCP configuration.",
                )
                self.unresolved = True
                return
            if self.format == "codex" and path != ".mcp.json":
                self.issue(
                    "mcp_reference_unsupported",
                    origin,
                    (
                        "Public Codex compatibility configuration uses root .mcp.json."
                        if self.public
                        else "This Codex configuration path is not verified by the documented package format."
                    ),
                    "error" if self.public else "unverified",
                )
                self.unresolved = True
            count = len(self.issues)
            data = self.read_json(path)
            self.config_sources.append(path)
            if len(self.issues) > count:
                self.unresolved = True
            if "mcpServers" not in data:
                self.issue(
                    "mcp_servers_missing", path, "Include the mcpServers object."
                )
                self.unresolved = True
                return
            declaration = data["mcpServers"]
            origin = path
        if not isinstance(declaration, dict):
            self.issue(
                "mcp_reference_unsupported",
                origin,
                "Use a supported MCP object or configuration path.",
            )
            self.unresolved = True
            return
        for name, spec in declaration.items():
            if not name.strip():
                self.issue("server_name_empty", origin, "Name each server.")
                self.unresolved = True
            if name in self.servers:
                if self.format in {"claude", "claude-import"}:
                    self.issue(
                        "mcp_override",
                        origin + ":" + name,
                        "This later Claude declaration replaces the earlier server.",
                        "warning",
                        "claude-format",
                    )
                else:
                    self.issue(
                        "duplicate_server",
                        origin + ":" + name,
                        "Give declarations unambiguous unique aliases.",
                    )
                    self.unresolved = True
                    continue
            self.servers[name] = spec
            self.server_sources[name] = origin + ":mcpServers." + name

    def resolve(self):
        if self.target == "openai" and "plugin.json" in self.files:
            self.format = "portable"
            self.manifest_path = "plugin.json"
            self.manifest = self.read_json("plugin.json")
            ex = self.obj(self.manifest.get("extensions", {}), "plugin.json:extensions")
            if "com.openai" in ex:
                self.settings = self.obj(
                    ex["com.openai"], "plugin.json:extensions.com.openai"
                )
                self.settings_source = "plugin.json:extensions.com.openai"
            elif ".codex-plugin/plugin.json" in self.files:
                self.settings = self.read_json(".codex-plugin/plugin.json")
                self.settings_source = ".codex-plugin/plugin.json"
            else:
                self.settings = {}
                self.settings_source = "derived portable metadata"
            self.interface = self.obj(
                self.settings.get("interface", {}), self.settings_source + ":interface"
            )
            nested = self.obj(
                self.settings.get("extensions", {}),
                self.settings_source + ":extensions",
            )
            self.review_settings = (
                self.settings
                if "com.openai" in ex
                else self.obj(
                    nested.get("com.openai", {}),
                    self.settings_source + ":extensions.com.openai",
                )
            )
            self.skill_roots = ["skills"]
            if "mcp.json" in self.files:
                self.resolve_servers("mcp.json", "plugin.json", True)
            for origin, value in [
                ("plugin.json:extensions.com.openai", self.settings)
            ] + (
                [
                    (
                        ".codex-plugin/plugin.json",
                        self.read_json(".codex-plugin/plugin.json"),
                    )
                ]
                if ".codex-plugin/plugin.json" in self.files
                else []
            ):
                if "mcpServers" in value:
                    self.issue(
                        "inactive_mcp_declaration",
                        origin,
                        "Portable components come only from root mcp.json; this overlay declaration is ignored by the host.",
                        "warning",
                        "format",
                    )
        else:
            if self.target == "claude":
                path = ".claude-plugin/plugin.json"
                self.format = "claude"
            elif ".codex-plugin/plugin.json" in self.files:
                path = ".codex-plugin/plugin.json"
                self.format = "codex"
            elif ".claude-plugin/plugin.json" in self.files:
                path = ".claude-plugin/plugin.json"
                self.format = "claude-import"
            else:
                path = ".codex-plugin/plugin.json"
                self.format = "codex"
            self.manifest_path = path
            self.manifest = self.read_json(path)
            self.settings = self.manifest
            self.settings_source = path
            ex = self.obj(self.manifest.get("extensions", {}), path + ":extensions")
            self.review_settings = self.obj(
                ex.get("com.openai", {}), path + ":extensions.com.openai"
            )
            self.interface = self.obj(
                self.manifest.get("interface", {}), path + ":interface"
            )
            if self.format == "claude-import":
                self.issue(
                    "conversion_unverified",
                    path,
                    "Validate the portal-generated OpenAI listing after Claude import.",
                    "unverified",
                    "openai-errors",
                )
            roots = self.manifest.get("skills", ["skills"])
            if not isinstance(roots, (str, list)) or isinstance(roots, list) and any(not isinstance(x, str) for x in roots):
                self.issue("skills_declaration", path + ":skills", "Use a skill path or list of skill paths.")
            self.skill_roots = (
                [roots]
                if isinstance(roots, str)
                else roots if isinstance(roots, list) else []
            )
            if self.format in {"claude", "claude-import"}:
                self.skill_roots = list(
                    dict.fromkeys(
                        ["skills"] + [r for r in self.skill_roots if isinstance(r, str)]
                    )
                )
            for root in self.skill_roots:
                if not safe_path(root):
                    self.issue(
                        "unsafe_reference",
                        path + ":skills",
                        "Use contained skill directories.",
                    )
            if self.format in {"claude", "claude-import"} and ".mcp.json" in self.files:
                self.resolve_servers(".mcp.json", path, True)
            if "mcpServers" in self.manifest:
                self.resolve_servers(self.manifest["mcpServers"], path + ":mcpServers")
            if (
                self.format == "codex"
                and ".mcp.json" in self.files
                and "mcpServers" not in self.manifest
            ):
                self.issue(
                    "inactive_mcp_declaration",
                    ".mcp.json",
                    'Declare mcpServers: "./.mcp.json" to load this compatibility configuration.',
                    "warning",
                    "openai-errors",
                )
        if (
            self.format in {"claude", "claude-import"}
            and "hooks" in self.settings
            and "hooks/hooks.json" in self.files
        ):
            self.resolve_hooks("hooks/hooks.json", "hooks/hooks.json")
        self.resolve_hooks(
            self.settings.get(
                "hooks", "hooks/hooks.json" if "hooks/hooks.json" in self.files else []
            ),
            self.settings_source + ":hooks",
        )
        self.checked.append(
            "Effective manifest, settings precedence, skill paths, and MCP declarations"
        )

    def resolve_hooks(self, value, origin):
        if isinstance(value, list):
            for item in value:
                self.resolve_hooks(item, origin)
        elif isinstance(value, str):
            name = self.reference(value, origin)
            if name:
                self.resolve_hooks(self.read_json(name), name)
        elif isinstance(value, dict):
            events = value.get("hooks", value)
            if isinstance(events, dict) and any(events.values()):
                self.hooks.append(origin)
            elif not isinstance(events, dict):
                self.issue("object_required", origin, "Use a hooks object.")
        elif value is not None:
            self.issue(
                "hook_configuration", origin, "Use a hook file path, object, or list."
            )

    def identity(self):
        m = self.manifest
        path = self.manifest_path
        name = m.get("name")
        pattern = (
            r"[a-z0-9]+(?:-[a-z0-9]+)*"
            if self.public
            else r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?"
        )
        if (
            not isinstance(name, str)
            or not name
            or len(name) > 64
            or not re.fullmatch(pattern, name)
        ):
            severity = (
                "warning"
                if self.target == "claude"
                and isinstance(name, str)
                and name.isascii()
                and bool(name)
                else "error"
            )
            self.issue(
                "invalid_name",
                path,
                "Use an identifier accepted by the target package format.",
                severity,
            )
        version = m.get("version")
        if (
            version is not None
            or (self.public and self.target == "openai")
            or self.format == "codex"
        ):
            if not isinstance(version, str) or not re.fullmatch(SEMVER, version):
                self.issue(
                    "invalid_version",
                    path,
                    "Use a strict semantic version such as 1.1.0.",
                )
        self.text(
            m.get("description"),
            path + ":description",
            required=self.public and self.target == "openai",
        )
        if "author" in m or (self.public and self.target == "openai"):
            self.text(
                self.obj(m.get("author", {}), path + ":author").get("name"),
                path + ":author.name",
                required=self.public and self.target == "openai",
            )
        if self.public and self.target == "claude":
            for field in ["description", "author", "version"]:
                if not m.get(field):
                    self.issue(
                        "recommended_metadata",
                        path + ":" + field,
                        "Supply descriptive metadata before review.",
                        "warning",
                    )
        if self.format == "portable":
            if m.get("$schema") != SCHEMA:
                self.issue(
                    "schema_required",
                    path,
                    "Declare the Agent Plugins 1.0 schema.",
                    "error",
                    "format",
                )
            for key in m.keys() - {
                "$schema",
                "name",
                "version",
                "description",
                "author",
                "homepage",
                "repository",
                "license",
                "keywords",
                "extensions",
            }:
                self.issue(
                    "unknown_portable_field",
                    path + ":" + key,
                    "Use the appropriate extension or component file.",
                    "error",
                    "format",
                )
        self.checked.append("Manifest identity and version")

    def listing(self):
        if self.target != "openai":
            return
        i = self.interface
        required = self.public or self.format == "codex"
        for name, limit in [
            ("displayName", 30 if self.public else 80),
            ("shortDescription", 30 if self.public else 240),
            ("longDescription", 4000),
            ("developerName", 80 if self.public else 120),
        ]:
            self.text(
                i.get(name),
                "interface." + name,
                required=required,
                maximum=None if self.rule_context is not None else limit,
                single=name != "longDescription",
            )
        category = i.get("category")
        if self.public and category is None:
            self.issue(
                "category_missing",
                "interface.category",
                "Choose a directory category.",
                "error",
                "openai",
            )
        elif category is not None and (
            not isinstance(category, str) or category not in CATEGORIES
        ):
            self.issue(
                "category_unknown",
                "interface.category",
                "Use a documented category title.",
                "error",
                "openai-errors",
            )
        caps = i.get("capabilities")
        if caps is None and self.format == "codex":
            self.issue(
                "capabilities_missing",
                "interface.capabilities",
                "Use a capability list, which may be empty.",
                "error",
                "openai",
            )
        elif caps is not None:
            if not isinstance(caps, list):
                self.issue(
                    "invalid_capabilities",
                    "interface.capabilities",
                    "Use a list of at most 20 text labels.",
                )
            else:
                if len(caps) > 20:
                    self.issue(
                        "invalid_capabilities",
                        "interface.capabilities",
                        "Use at most 20 labels.",
                    )
                for n, label in enumerate(caps):
                    self.text(
                        label, f"interface.capabilities[{n}]", maximum=120, single=True
                    )
        for field in ["logo", "composerIcon", "logoDark", "composerIconDark"]:
            if field not in i and not (required and field in ["logo", "composerIcon"]):
                continue
            asset = self.reference(i.get(field), "interface." + field)
            if asset and asset.lower().endswith(".png"):
                blob = self.files[asset]
                if len(blob) < 24 or blob[:8] != b"\x89PNG\r\n\x1a\n":
                    self.issue("invalid_png_header", asset, "Use a valid icon.")
                else:
                    w, h = struct.unpack(">II", blob[16:24])
                    if w != h or w < 48 or w > 4096:
                        self.issue(
                            "invalid_icon_size",
                            asset,
                            "Use a square raster icon from 48 to 4096 pixels.",
                        )
        prompts = i.get("defaultPrompt", [])
        prompts = [prompts] if isinstance(prompts, str) else prompts
        if not isinstance(prompts, list):
            self.issue(
                "invalid_prompts",
                "interface.defaultPrompt",
                "Use a string or list of up to three strings.",
            )
        else:
            normalized = set()
            if len(prompts) > 3:
                self.issue(
                    "too_many_prompts",
                    "interface.defaultPrompt",
                    "Use at most three prompts.",
                )
            for n, p in enumerate(prompts):
                if self.text(
                    p, f"interface.defaultPrompt[{n}]", maximum=128, single=True
                ):
                    norm = " ".join(unicodedata.normalize("NFKC", p).split())
                    if norm in normalized:
                        self.issue(
                            "duplicate_prompt",
                            "interface.defaultPrompt",
                            "Use distinct prompts.",
                        )
                    normalized.add(norm)
                    if re.search(r"(?<![\w.])@[\w-]+", p):
                        self.issue(
                            "prompt_mention",
                            "interface.defaultPrompt",
                            "Omit app mentions.",
                        )
        for field in [
            "websiteURL",
            "supportURL",
            "privacyPolicyURL",
            "termsOfServiceURL",
        ]:
            if field in i or (self.public and self.remote_review):
                self.url(i.get(field), "interface." + field)
        self.checked.append(
            "Applicable listing fields, limits, prompts, and asset references"
        )

    def skills(self):
        found = []
        for root in self.skill_roots:
            if not safe_path(root):
                continue
            normalized = str(PurePosixPath(root))
            if normalized + "/SKILL.md" in self.files:
                found.append(normalized + "/SKILL.md")
            prefix = normalized.rstrip("/") + "/" if normalized != "." else ""
            found += [
                name
                for name in self.files
                if name.startswith(prefix)
                and len(name[len(prefix) :].split("/")) == 2
                and name.endswith("/SKILL.md")
            ]
        for name in found:
            try:
                contents = self.files[name].decode("utf-8")
            except UnicodeError:
                self.issue("invalid_skill_encoding", name, "Use UTF-8.")
                continue
            fm = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", contents, re.S)
            if not fm:
                self.issue(
                    "skill_frontmatter",
                    name,
                    "Include name and description in YAML frontmatter.",
                )
                continue
            fields = dict(re.findall(r"^([\w-]+):[ \t]*(.+)$", fm.group(1), re.M))
            if fields.get("name", "").strip("\"'") != PurePosixPath(name).parent.name:
                self.issue(
                    "skill_name_mismatch", name, "Match the skill directory name."
                )
            if not fields.get("description", "").strip() or fields.get(
                "description", ""
            ).startswith(("[", "{")):
                self.issue(
                    "skill_description", name, "Use a nonblank text description."
                )
        # All Markdown resources, not just SKILL.md, are checked for local references.
        for name, blob in self.files.items():
            if not name.endswith(".md"):
                continue
            try:
                contents = blob.decode("utf-8")
            except UnicodeError:
                continue
            for link in re.findall(r"\]\(([^)\s]+)\)", contents):
                target = link.split("#", 1)[0]
                if not target or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                    continue
                resolved = PurePosixPath(name).parent / target
                parts = []
                for part in resolved.parts:
                    if part == "..":
                        if not parts:
                            break
                        parts.pop()
                    else:
                        parts.append(part)
                else:
                    if "/".join(parts) in self.files:
                        continue
                self.issue(
                    "skill_link_missing",
                    name,
                    "Include the linked resource inside the package.",
                )
        self.checked.append("Skill entrypoints and local Markdown references")
        return found

    def servers_check(self):
        for name, value in self.servers.items():
            path = self.server_sources[name]
            spec = self.obj(value, path)
            if not isinstance(value, dict):
                self.unresolved = True
            if "connector_id" in spec:
                self.issue(
                    "legacy_connector_id",
                    path,
                    "Use the server endpoint; connector_id is an API built-in connector selector.",
                    "error",
                    "api",
                )
            if self.public and self.target == "openai" and spec.get("headers"):
                self.issue(
                    "public_server_headers",
                    path,
                    "Use the supported anonymous/OAuth configuration.",
                )
            if "url" in spec:
                typ = spec.get("type")
                if self.target == "claude" and (
                    not isinstance(typ, str) or typ not in {"http", "sse", "ws"}
                ):
                    self.issue(
                        "claude_transport",
                        path,
                        "Declare http, sse, or ws for a Claude remote server.",
                    )
                elif self.format == "portable" and typ != "streamable-http":
                    self.issue(
                        "remote_transport",
                        path,
                        "Use portable streamable-http for this remote server.",
                    )
                elif self.format in {"codex", "claude-import"} and (
                    not isinstance(typ, (str, type(None)))
                    or typ not in {None, "http", "sse", "streamable-http"}
                ):
                    self.issue(
                        "transport_unverified",
                        path,
                        "Verify this compatibility transport with the host.",
                        "unverified",
                    )
                self.url(spec.get("url"), path + ":url", remote=True)
            elif "command" in spec:
                self.text(spec["command"], path + ":command")
                if not isinstance(spec.get("args", []), list) or any(
                    not isinstance(a, str) for a in spec.get("args", [])
                ):
                    self.issue("invalid_args", path, "Use a list of string arguments.")
                if self.format == "portable" and spec.get("type") != "stdio":
                    self.issue("local_transport", path, "Portable local MCP entries require type: stdio.")
                if self.public and self.target == "openai" and not self.desktop_eligible:
                    self.issue(
                        "remote_required", path,
                        "Use a hosted HTTPS endpoint for the remote route, or select desktop-only with allowlist confirmation.",
                    )
                if self.public and self.target == "claude":
                    self.launcher(spec, path)
            else:
                self.issue(
                    "server_configuration", path, "Provide a URL or local command."
                )
                self.unresolved = True
        if self.target == "openai" and len(self.servers) > 1:
            self.issue(
                "one_connection_limit",
                "mcpServers",
                "The current portal connects one server per plugin.",
                "warning",
            )
        if self.servers:
            self.checked.append(
                "Resolved MCP declarations; no endpoint or tool was executed"
            )

    def launcher(self, spec, path):
        command = spec.get("command")
        args = spec.get("args", [])
        if (
            not isinstance(command, str)
            or not isinstance(args, list)
            or any(not isinstance(a, str) for a in args)
        ):
            return
        try:
            tokens = shlex.split(command) + args
        except ValueError:
            self.issue(
                "launcher_unverified",
                path,
                "Inspect this shell command manually.",
                "unverified",
            )
            return
        if not tokens:
            return
        exe = PurePosixPath(tokens[0]).name
        tokens = tokens[1:]
        kind = None
        if exe in {"npx", "bunx", "uvx"}:
            kind = "python" if exe == "uvx" else "npm"
        elif exe in {"pnpm", "yarn"} and tokens[:1] == ["dlx"]:
            kind = "npm"
            tokens = tokens[1:]
        elif exe == "pipx" and tokens[:1] == ["run"]:
            kind = "python"
            tokens = tokens[1:]
        elif exe == "uv" and "run" in tokens:
            kind = "uv"
            pinned = "--locked" in tokens or "--frozen" in tokens
        if kind:
            unknown_option = False
            if kind != "uv":
                packages = []
                positionals = []
                i = 0
                unknown_option = False
                value_flags = {"--package", "-p", "--from", "--spec", "--with"}
                safe_flags = {
                    "-y",
                    "--yes",
                    "--no-install",
                    "--quiet",
                    "--verbose",
                    "--no-cache",
                    "--ignore-existing",
                }
                while i < len(tokens):
                    token = tokens[i]
                    if token in value_flags:
                        i += 1
                        if i < len(tokens):
                            packages.append(tokens[i])
                        else:
                            packages.append("")
                    elif any(token.startswith(flag + "=") for flag in value_flags):
                        packages.append(token.split("=", 1)[1])
                    elif token.startswith("-"):
                        if token not in safe_flags:
                            unknown_option = True
                    else:
                        positionals.append(token)
                    i += 1
                if not packages:
                    packages = positionals[:1]

                def exact(package):
                    version = (
                        package.rsplit("==", 1)[-1]
                        if kind == "python" and "==" in package
                        else (
                            package.rsplit("@", 1)[-1]
                            if kind == "npm" and "@" in package[1:]
                            else ""
                        )
                    )
                    # Python distribution releases need not use three SemVer components.
                    return bool(
                        re.fullmatch(
                            r"(?:[0-9]+!)?[0-9]+(?:\.[0-9]+)*(?:(?:[._-]?(?:a|b|rc|post|dev))[0-9]+)*(?:\+[A-Za-z0-9._-]+)?",
                            version,
                        )
                        if kind == "python"
                        else re.fullmatch(SEMVER, version)
                    )

                pinned = bool(packages) and all(exact(package) for package in packages)
                if unknown_option:
                    self.issue(
                        "launcher_options_unverified",
                        path,
                        "Verify launcher flags and every downloaded dependency with the native validator.",
                        "unverified",
                    )
            self.issue(
                "launcher_review" if pinned else "launcher_options_unverified" if unknown_option else "unpinned_launcher",
                path,
                (
                    "Review registry-resolved dependencies."
                    if pinned
                    else "Pin the launcher package to an exact version; uv run requires --locked or --frozen."
                ),
                "hold" if pinned else "unverified" if unknown_option else "error",
            )
            for name in self.files:
                if PurePosixPath(name).name in {
                    ".npmrc",
                    "bunfig.toml",
                    "uv.toml",
                    "pip.conf",
                } and re.search(
                    rb"(?im)^\s*(?:registry|index|index-url|extra-index-url|proxy|url)\s*[=:]",
                    self.files[name],
                ):
                    self.issue(
                        "package_source_override",
                        name,
                        "Remove package source overrides from a launcher-based submission.",
                    )
        elif (
            exe in {"sh", "bash", "zsh", "cmd", "powershell", "pwsh"}
            or "-c" in tokens
            or (exe == "npm" and "run" in tokens)
        ):
            self.issue(
                "command_review",
                path,
                "A reviewer must inspect this indirect command.",
                "hold",
            )

    def review(self):
        if not (self.public and self.target == "openai"):
            return
        if self.rule_context is not None:
            return  # Current review requirements are resolved from the selected primary pages.
        if self.hooks:
            self.issue(
                "public_lifecycle_hooks",
                ",".join(self.hooks),
                "Remove executable lifecycle hooks from the public upload; retain them only in manual/local distributions.",
                "error",
                "openai",
            )
        for file in [
            "plugin.json",
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
        ]:
            if file not in self.files:
                continue
            m = self.read_json(file)
            ex = self.obj(m.get("extensions", {}), file + ":extensions")
            o = self.obj(ex.get("com.openai", {}), file + ":extensions.com.openai")
            if m.get("apps") is not None or o.get("apps") is not None:
                self.issue(
                    "public_app_binding",
                    file,
                    "Remove app bindings from the public upload copy.",
                )
        if ".app.json" in self.files:
            self.issue(
                "public_app_binding",
                ".app.json",
                "Remove private bindings from the public upload copy.",
            )
        if not self.remote_review:
            return
        review = self.obj(self.review_settings.get("review", {}), "review")
        publication = self.obj(
            self.review_settings.get("publication", {}), "publication"
        )
        self.url(review.get("demo_recording_url"), "review.demo_recording_url")
        self.text(publication.get("release_notes"), "publication.release_notes")
        if len(self.servers) == 1:
            spec = next(iter(self.servers.values()))
            ex = spec.get("extensions", {}) if isinstance(spec, dict) else {}
            if (
                isinstance(ex, dict)
                and isinstance(ex.get("com.openai"), dict)
                and "review" in ex["com.openai"]
                and "test_cases" in review
            ):
                self.issue(
                    "mixed_case_location", "review", "Use one supported case location."
                )
            cases = self.obj(review.get("test_cases", {}), "review.test_cases")
            self.cases(cases, "positive", 5, False, "review")
            self.cases(cases, "negative", 3, False, "review")
        elif len(self.servers) > 1:
            if review.get("test_cases") is not None:
                self.issue(
                    "mixed_case_location",
                    "review.test_cases",
                    "Put multi-server cases on the exact server.",
                )
            for name, spec in self.servers.items():
                if not isinstance(spec, dict):
                    continue
                ex = self.obj(spec.get("extensions", {}), name + ":extensions")
                o = self.obj(ex.get("com.openai", {}), name + ":com.openai")
                r = self.obj(o.get("review", {}), name + ":review")
                self.cases(r, "testCases", 5, True, name + ":review")
                self.cases(r, "negativeTestCases", 3, True, name + ":review")
        self.checked.append(
            "Static review material fields; submitted-case/supported-surface outcomes remain unverified"
        )

    def cases(self, values, key, count, camel, prefix):
        cases = values.get(key)
        path = prefix + "." + key
        if not isinstance(cases, list) or len(cases) != count:
            self.issue(
                "review_case_count",
                path,
                f"Provide exactly {count} initial-review cases.",
            )
            return
        for n, case in enumerate(cases):
            case = self.obj(case, f"{path}[{n}]")
            fields = ["description", "userPrompt" if camel else "prompt"]
            if count == 5:
                fields += (
                    ["toolsTriggered", "expectedOutput"]
                    if camel
                    else ["tools_triggered", "expected_behavior"]
                )
            for field in fields:
                self.text(case.get(field), f"{path}[{n}].{field}")

    def repository_checks(self):
        if not (self.public and self.target == "claude"):
            return
        readme = self.files.get("README.md", b"").decode("utf-8", errors="replace")
        if len(re.sub(r"```.*?```", "", readme, flags=re.S).split()) < 40:
            self.issue(
                "readme_too_short", "README.md", "Include at least 40 prose words."
            )
        if not self.manifest.get("license") and not any(
            n in self.files for n in ["LICENSE", "LICENSE.md", "LICENSE.txt"]
        ):
            self.issue(
                "license_missing",
                self.manifest_path,
                "Provide a creator-approved license.",
            )
        if len(self.files) > 512:
            self.issue(
                "claude_file_count_review",
                "package",
                "More than 512 plugin files requires reviewer inspection.",
                "hold",
            )
        for name, blob in self.files.items():
            if len(blob) >= 5 * 1024 * 1024:
                self.issue(
                    "claude_file_limit", name, "Keep each plugin file under 5 MiB."
                )
            suffix = PurePosixPath(name).suffix.lower()
            media = suffix in {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp",
                ".svg",
                ".ttf",
                ".otf",
                ".woff",
                ".woff2",
            }
            if not media and len(blob) >= 256 * 1024:
                self.issue(
                    "claude_text_review",
                    name,
                    "Non-image/font files at this size require reviewer inspection.",
                    "hold",
                )
            if not media:
                try:
                    blob.decode("utf-8")
                    binary = b"\0" in blob
                except UnicodeError:
                    binary = True
                if binary:
                    self.issue(
                        "claude_binary_review",
                        name,
                        "This binary format requires reviewer inspection.",
                        "hold",
                    )
            if blob.startswith(b"version https://git-lfs.github.com/spec/v1"):
                active = (
                    name.endswith("SKILL.md")
                    or name in self.config_sources
                    or name == self.manifest_path
                )
                self.issue(
                    "git_lfs_pointer",
                    name,
                    "Commit the actual content instead of an LFS pointer.",
                    "error" if active else "warning",
                )
        repo = self.repository
        if repo is None:
            repo = self.files
            self.issue(
                "repository_scope_unverified",
                "repository",
                "Supply --repository-root to check files outside the plugin folder.",
                "unverified",
                scope="repository",
            )
        metadata = getattr(repo, "inventory", None) or {
            "files": len(repo),
            "entries": len(repo)
            + len(
                {
                    str(PurePosixPath(n).parent)
                    for n in repo
                    if str(PurePosixPath(n).parent) != "."
                }
            ),
            "unpacked_bytes": sum(map(len, repo.values())),
            "archive_bytes": None,
        }
        if metadata["entries"] >= 10000:
            self.issue(
                "repository_file_limit",
                "repository",
                "Keep repository files and folders below 10,000.",
                scope="repository",
            )
        if metadata["unpacked_bytes"] >= 256 * 1024 * 1024:
            self.issue(
                "repository_size_limit",
                "repository",
                "Keep the unpacked repository under 256 MiB.",
                scope="repository",
            )
        if (
            metadata.get("archive_bytes") is not None
            and metadata["archive_bytes"] >= 50 * 1024 * 1024
        ):
            self.issue(
                "repository_archive_limit",
                "repository",
                "Keep the repository archive under 50 MiB.",
                scope="repository",
            )
        elif metadata.get("archive_bytes") is None:
            self.issue(
                "archive_size_unverified",
                "repository",
                "Verify the size of GitHub's repository archive separately.",
                "unverified",
                scope="repository",
            )
        for name, blob in repo.items():
            if PurePosixPath(name).name == ".gitattributes":
                lines = "\n".join(
                    line
                    for line in blob.decode("utf-8", errors="replace").splitlines()
                    if not line.lstrip().startswith("#")
                )
                archive_rule = bool(
                    re.search(r"\b(?:export-ignore|export-subst)\b", lines)
                )
                filter_rule = bool(re.search(r"\bfilter(?:\b|=)", lines))
                parent = str(PurePosixPath(name).parent)
                prefix = self.repository_prefix
                relevant = (
                    repo is self.files
                    or prefix == "."
                    or parent == "."
                    or prefix is not None
                    and (
                        parent == prefix
                        or parent.startswith(prefix.rstrip("/") + "/")
                        or prefix.startswith(parent.rstrip("/") + "/")
                    )
                )
                if archive_rule or (filter_rule and relevant):
                    self.issue(
                        "gitattributes_rewrite",
                        name,
                        "Remove archive/content-rewriting Git attributes in the documented scope.",
                        scope="repository",
                    )
                elif filter_rule and prefix is None:
                    self.issue(
                        "gitattributes_scope_unverified",
                        name,
                        "Supply the plugin path within this repository to resolve filter-attribute scope.",
                        "unverified",
                        scope="repository",
                    )
            if PurePosixPath(name).name == ".gitmodules":
                self.issue(
                    "git_submodule",
                    name,
                    "Verify runtime content is committed rather than provided by a submodule.",
                    "unverified",
                    scope="repository",
                )
        self.checked.append(
            "Claude plugin limits/holds and available repository-scope evidence"
        )

    def hygiene(self):
        for name, blob in self.files.items():
            parts = PurePosixPath(name).parts
            if self.public:
                if any(
                    p in {".DS_Store", "Thumbs.db", "desktop.ini", "__MACOSX"}
                    for p in parts
                ):
                    self.issue("system_file", name, "Remove operating-system metadata.")
                if self.target == "claude" and any(
                    re.search(r'[<>:"|?*]', p)
                    or p.rstrip(" .") != p
                    or re.fullmatch(
                        r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p
                    )
                    for p in parts
                ):
                    self.issue("nonportable_filename", name, "Use portable filenames.")
            if name.endswith((".pem", ".key")) or any(
                p.startswith(".env") for p in parts
            ):
                self.issue(
                    "sensitive_file",
                    name,
                    "Inspect this possible credential file; filename detection is not a secret scan.",
                    "warning",
                )
            if name.endswith(".json") and self.public and self.target == "openai":
                try:
                    self.private_fields(json.loads(blob), name)
                except (ValueError, UnicodeError, RecursionError):
                    pass

    def private_fields(self, obj, path):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in {"test_credentials", "reviewer_instructions"}:
                    self.issue(
                        "private_review_field",
                        path + ":" + key,
                        "Keep reviewer access in secure portal fields.",
                    )
                self.private_fields(value, path + ":" + key)
        elif isinstance(obj, list):
            for value in obj:
                self.private_fields(value, path)

    def run(self):
        self.resolve()
        self.route_checks()
        self.identity()
        self.listing()
        skills = self.skills()
        self.servers_check()
        self.review()
        self.repository_checks()
        self.hygiene()
        if self.rule_context is not None and self.public and self.target=='openai':
            import openai_core
            self.issues.extend(openai_core.policy_findings(self.rule_context, self.settings.get('interface',{}),self.review_settings.get('review',{}),self.remote_review,self.servers))
        if not skills and not self.servers and not self.unresolved:
            self.issue(
                "no_capabilities",
                self.manifest_path,
                "Include a skill or a supported MCP declaration.",
            )
        kind = (
            "unresolved"
            if self.unresolved
            else "mcp" if self.servers else "skills-only"
        )
        unverified = [
            "Official schema/policy coverage and current portal checks",
            "Complete dependency/command analysis, userConfig references, and secret-content scanning",
            "Real host behavior, source revision, and package-hash evidence",
            "Publisher identity, legal declarations, and review/publication state",
        ]
        if self.servers or self.unresolved:
            unverified += [
                "Live MCP schemas/annotations/permissions, authentication, and reviewer access",
                "Submitted review cases on every supported surface; recording playback and URL contents",
            ]
        return {
            "target": self.target,
            "profile": self.profile,
            "submission_route": self.submission_route,
            "synthetic": self.synthetic,
            "desktop_allowlist": {
                "record_accepted": self.desktop_eligible,
                "verification": "Synthetic fixture" if self.synthetic else "Creator-supplied confirmation; OpenAI membership not queried",
            } if self.submission_route == "desktop-only" else None,
            "human_handoffs": ["Portal upload", "Allowlist/identity confirmation", "Review submission", "Publication"],
            "status": (
                "local_checks_failed"
                if any(i["severity"] == "error" for i in self.issues)
                else "local_checks_passed"
            ),
            "ready_to_submit": False,
            "format": self.format,
            "classification": {
                "kind": kind,
                "server_count": len(self.servers),
                "settings_source": self.settings_source,
                "mcp_sources": self.config_sources,
            },
            "content_sha256": digest_files(self.files),
            "file_count": len(self.files),
            "checked": self.checked,
            "issues": self.issues,
            "issue_counts": {
                level: sum(i["severity"] == level for i in self.issues)
                for level in ["error", "hold", "warning", "unverified"]
            },
            "unverified": unverified,
            "not_applicable": (
                []
                if kind != "skills-only"
                else ["MCP review cases, server OAuth, and MCP demo recording"]
            ),
        }

