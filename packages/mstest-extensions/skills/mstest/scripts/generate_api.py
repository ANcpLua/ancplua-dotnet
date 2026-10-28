#!/usr/bin/env python3
"""Erzeugt die PublicAPI-Referenz aus den Release-Tags in versions.yaml.

Aus dem Repo-Root aufrufen: make update-mstest-api
"""
import os
import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import jinja2
import yaml

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "versions.yaml"
TEMPLATE_PATH = HERE / "api_table.md.j2"
OUTPUT_PATH = HERE.parent / "references" / "public-api.md"
EXPERIMENTAL_PREFIX = "[MSTESTEXP]"


def http_get(url: str, accept: str, allow_missing: bool = False) -> str:
    headers = {"User-Agent": "MSTest-PublicAPI-DocSync", "Accept": accept}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as resp:
            # utf-8-sig: die PublicAPI-Dateien beginnen mit einem BOM.
            return resp.read().decode("utf-8-sig")
    except urllib.error.HTTPError as err:
        if allow_missing and err.code == 404:
            return ""
        sys.exit(f"{url}: {err.code} {err.reason}")


def version_key(version: str) -> tuple[int, ...]:
    # Numerisch statt als String sortieren, sonst landet 3.10 vor 3.9.
    return tuple(int(part) for part in re.findall(r"\d+", version))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if generated output differs; do not write')
    args = parser.parse_args()
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    repo = config["repo"]
    target_files = config["target_files"]
    if isinstance(target_files, str):
        target_files = [target_files]
    versions = sorted(config["versions"], key=lambda e: version_key(str(e["version"])))

    for entry in versions:
        if not isinstance(entry["version"], str):
            sys.exit(f"version {entry['version']!r} in {CONFIG_PATH} in Anführungszeichen setzen "
                     "(YAML liest z. B. 3.10 sonst als Zahl 3.1).")

    current_version = versions[-1]["version"]
    apis: dict[str, dict] = {}

    for entry in versions:
        version, tag = entry["version"], entry["tag"]
        print(f"Lade {len(target_files)} Dateien für {version} ({tag})...")
        # Löst auch annotated Tags direkt auf den Commit auf.
        sha = http_get(f"https://api.github.com/repos/{repo}/commits/{tag}", "application/vnd.github.sha").strip()
        # Fehlende Dateien sind normal, wenn ein Paket erst in einer späteren Version dazukam.
        content = "\n".join(
            http_get(f"https://raw.githubusercontent.com/{repo}/{sha}/{path}", "text/plain", allow_missing=True)
            for path in target_files
        )

        # Pro Version erst sammeln: dasselbe Symbol kann in Shipped und Unshipped stehen.
        symbols: dict[str, bool] = {}
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith(("#", "*REMOVED*")):
                symbols[line.removeprefix(EXPERIMENTAL_PREFIX).strip()] = line.startswith(EXPERIMENTAL_PREFIX)

        for symbol, is_experimental in symbols.items():
            api = apis.setdefault(symbol, {"symbol": symbol, "introduced_in": version})
            api.update(is_experimental=is_experimental, last_version=version)

    for api in apis.values():
        if api["last_version"] != current_version:
            api["status"] = "removed"
        else:
            api["status"] = "experimental" if api["is_experimental"] else "stable"

    env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True, undefined=jinja2.StrictUndefined)
    markdown = env.from_string(TEMPLATE_PATH.read_text(encoding="utf-8")).render(
        repo=repo,
        versions=[e["version"] for e in versions],
        current_version=current_version,
        apis=sorted(apis.values(), key=lambda a: a["symbol"]),
    )

    if args.check:
        matches = OUTPUT_PATH.is_file() and OUTPUT_PATH.read_text(encoding='utf-8') == markdown
        print('MSTest API reference: ' + ('current' if matches else 'generation required'))
        return 0 if matches else 1
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")
    print(f"{len(apis)} APIs nach {OUTPUT_PATH} geschrieben.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
