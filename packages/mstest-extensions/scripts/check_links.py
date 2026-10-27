"""Validate repository-local Markdown file links without following web URLs."""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
checked = 0
for document in [root / "README.md", root / "AGENTS.md", root / "PRIVACY.md", root / "TERMS.md", *(root / "skills").rglob("*.md")]:
    for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
        if "://" in target or target.startswith("#"):
            continue
        linked = document.parent / target.split("#", 1)[0]
        if not linked.exists():
            raise SystemExit(f"Broken link in {document.relative_to(root)}: {target}")
        checked += 1
print(f"Validated {checked} local Markdown links.")
