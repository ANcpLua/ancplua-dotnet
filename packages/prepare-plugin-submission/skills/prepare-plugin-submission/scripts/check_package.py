#!/usr/bin/env python3
"""Offline preflight. Reads files only; never executes a plugin or contacts a service."""
from __future__ import annotations
import argparse
import html
import json
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath
from importlib.util import spec_from_file_location, module_from_spec

_core_spec = spec_from_file_location(
    "submission_studio_core", Path(__file__).with_name("package_core.py")
)
_core = module_from_spec(_core_spec)
_core_spec.loader.exec_module(_core)
Checker = _core.Checker

LIMIT = 16 * 1024 * 1024
TOTAL_LIMIT = 320 * 1024 * 1024


class InputError(ValueError):
    pass


class PackageFiles(dict):
    """Bytes plus observed input metadata; the validator never opens files."""

    inventory = None
    modes = None


def safe_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    p = PurePosixPath(value)
    return not (
        p.is_absolute()
        or ".." in p.parts
        or re.match(r"^[A-Za-z]:", value)
        or "\x00" in value
    )


def load_files(path):
    """Bounded reads with no ZIP extraction; reject ambiguity and special files."""
    data = PackageFiles()
    total = 0
    directories = set()
    seen_paths = set()
    modes = {}

    def add(name, size, reader, mode):
        nonlocal total
        if not safe_path(name):
            raise InputError(
                "Unsafe package path; archive paths must be contained and relative."
            )
        name = str(PurePosixPath(name))
        if name.casefold() in seen_paths:
            raise InputError("Duplicate or case-colliding package path.")
        if size > LIMIT:
            raise InputError("A package file exceeds the 16 MiB checker safety limit.")
        total += size
        if total > TOTAL_LIMIT or len(data) >= 20000:
            raise InputError("Package exceeds the bounded preflight inventory limit.")
        seen_paths.add(name.casefold())
        data[name] = reader()
        modes[name] = mode

    if path.is_dir():
        for p in sorted(path.rglob("*")):
            rel = p.relative_to(path)
            if any(x in {".git", "__pycache__", ".pytest_cache"} for x in rel.parts):
                continue
            if p.is_symlink():
                raise InputError(
                    "Symbolic links are not supported in a plugin package."
                )
            if p.is_dir():
                directories.add(rel.as_posix())
            if len(data) + len(directories) > 20000:
                raise InputError("Package exceeds the 20,000-entry safety limit.")
            if p.is_file():
                add(rel.as_posix(), p.stat().st_size, p.read_bytes, p.stat().st_mode)
            elif not p.is_dir():
                raise InputError("Special files are not supported.")
    elif path.is_file() and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            if len(z.infolist()) > 20000:
                raise InputError("Package exceeds the 20,000-entry safety limit.")
            for item in z.infolist():
                if not safe_path(item.filename):
                    raise InputError("Unsafe ZIP entry; path traversal is not allowed.")
                mode = item.external_attr >> 16
                if stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in (
                    0,
                    stat.S_IFREG,
                    stat.S_IFDIR,
                ):
                    raise InputError("ZIP contains a symbolic link or special file.")
                if item.is_dir():
                    directories.add(item.filename.rstrip("/"))
                    continue
                if item.flag_bits & 1:
                    raise InputError("Encrypted ZIP entries cannot be inspected.")
                add(item.filename, item.file_size, lambda i=item: z.read(i), mode)
        root_markers = (
            "plugin.json",
            ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json",
        )
        if not any(m in data for m in root_markers):
            roots = {n.split("/")[0] for n in data}
            if len(roots) == 1:
                prefix = next(iter(roots)) + "/"
                data = PackageFiles({n[len(prefix) :]: v for n, v in data.items()})
                modes = {n[len(prefix):]: v for n, v in modes.items()}
                directories = {
                    n[len(prefix) :] for n in directories if n.startswith(prefix)
                }
    else:
        raise InputError("Input must be a readable plugin directory or ZIP archive.")
    data.modes = modes
    data.inventory = {
        "files": len(data),
        "entries": len(data) + len(directories),
        "unpacked_bytes": total,
        "archive_bytes": path.stat().st_size if path.is_file() else None,
    }
    return data


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def render_html(result):
    e = lambda value: html.escape(str(value))
    rows = "".join(
        "<tr><td>"
        + e(i["severity"])
        + "</td><td><code>"
        + e(i["code"])
        + "</code><br>"
        + e(i["path"])
        + "</td><td>"
        + e(i["fix"])
        + "<br><small>"
        + e(i.get("scope", ""))
        + " · "
        + e(i.get("source", ""))
        + " · retrieved "
        + e(i.get("retrieved", ""))
        + "</small></td></tr>"
        for i in result["issues"]
    )
    if not rows:
        rows = '<tr><td colspan="3">No findings from the implemented local checks.</td></tr>'
    checks = "".join("<li>" + e(x) + "</li>" for x in result["checked"])
    gaps = "".join("<li>" + e(x) + "</li>" for x in result["unverified"])
    return (
        """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Submission Studio — package report</title>
<style>body{margin:0;background:#f4f6f8;color:#172536;font:16px/1.6 system-ui,sans-serif}main{max-width:1000px;margin:48px auto;padding:0 24px}.brand{color:#216d7a;font-weight:700;letter-spacing:.12em;font-size:13px}h1{font-size:40px;line-height:1.15;margin:12px 0}h2{font-size:21px}.status{background:#13384a;color:white;padding:24px 30px;border-radius:14px;margin:28px 0}.status strong{font-size:22px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}section{background:white;border:1px solid #dde4eb;border-radius:14px;padding:24px;margin-bottom:24px}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:14px;border-bottom:1px solid #e4e8ee;vertical-align:top}code{font-size:13px;overflow-wrap:anywhere}small{color:#536474}li{margin:8px 0}footer{font-size:13px;color:#536474;overflow-wrap:anywhere}@media(max-width:700px){.grid{display:block}h1{font-size:30px}main{margin-top:24px}}</style><main><div class="brand">SUBMISSION STUDIO / OFFLINE PREFLIGHT</div><h1>Your package, checked.</h1><p>Concrete findings for the exact inspected files. Host behavior and review remain separate.</p>"""
        + f'<div class="status"><strong>{e(result["status"].replace("_"," ").capitalize())}</strong><br>{e(result["target"])} · {e(result["profile"])} · {result["file_count"]} files<br>Directory submission readiness: not established by this check.</div><section><h2>Findings</h2><table><thead><tr><th>Level</th><th>Location</th><th>Next action</th></tr></thead><tbody>{rows}</tbody></table></section><div class="grid"><section><h2>What was checked</h2><ul>{checks}</ul></section><section><h2>What still needs evidence</h2><ul>{gaps}</ul></section></div><footer>Content SHA-256: {e(result["content_sha256"])}<br>Read-only report. No plugin code was executed and no service was contacted.</footer></main></html>'
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--target", choices=["openai", "claude"], required=True)
    parser.add_argument(
        "--profile", choices=["package", "submission"], default="package"
    )
    parser.add_argument("--submission-route", choices=["remote", "desktop-only"], default="remote")
    parser.add_argument("--desktop-allowlist", type=Path, help="JSON confirmation record; never include credentials")
    parser.add_argument("--synthetic", action="store_true", help="Validate fixture data; never proves partner eligibility")
    parser.add_argument("--json", type=Path, dest="json_path")
    parser.add_argument("--html", type=Path, dest="html_path")
    parser.add_argument(
        "--repository-root",
        type=Path,
        help="Optional complete repository directory or archive for Claude repository-scope checks.",
    )
    args = parser.parse_args(argv)
    try:
        files = load_files(args.package)
        repository = load_files(args.repository_root) if args.repository_root else None
        prefix = None
        if (
            args.repository_root
            and args.repository_root.is_dir()
            and args.package.is_dir()
        ):
            try:
                prefix = (
                    args.package.resolve()
                    .relative_to(args.repository_root.resolve())
                    .as_posix()
                )
            except ValueError:
                pass
        allowlist = None
        if args.desktop_allowlist:
            if args.desktop_allowlist.is_symlink() or args.desktop_allowlist.stat().st_size > 65536:
                raise InputError("Allowlist record must be a regular JSON file below 64 KiB")
            try:
                allowlist = json.loads(args.desktop_allowlist.read_text(), object_pairs_hook=no_duplicates)
            except (ValueError, UnicodeError) as exc:
                raise InputError("Invalid allowlist record JSON") from exc
        result = Checker(
            files,
            args.target,
            args.profile,
            repository=repository,
            repository_prefix=prefix,
            submission_route=args.submission_route,
            desktop_allowlist=allowlist,
            synthetic=args.synthetic,
        ).run()
        # Preflight every destination before writing either report.
        destinations = [p.resolve() for p in [args.json_path, args.html_path] if p]
        if len(destinations) != len(set(destinations)):
            raise InputError("JSON and HTML reports must use different destinations.")
        for resolved in destinations:
            for source_path in [args.package, args.repository_root]:
                if source_path is None:
                    continue
                source = source_path.resolve()
                if resolved == source or (
                    source.is_dir() and source in resolved.parents
                ):
                    raise InputError(
                        "Write reports outside the inspected package and repository."
                    )
        for destination, contents in [
            (args.json_path, json.dumps(result, indent=2) + "\n"),
            (args.html_path, render_html(result)),
        ]:
            if destination:
                # Avoid overwriting an inspected source file or archive.
                resolved = destination.resolve()
                source = args.package.resolve()
                if resolved == source or (
                    source.is_dir() and source in resolved.parents
                ):
                    raise InputError("Write reports outside the inspected package.")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(contents, encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 1 if result["status"] == "local_checks_failed" else 0
    except (InputError, OSError, zipfile.BadZipFile, RuntimeError) as error:
        print(
            json.dumps(
                {
                    "status": "input_error",
                    "code": "input_unreadable_or_safety_limit",
                    "message": str(error),
                }
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())

