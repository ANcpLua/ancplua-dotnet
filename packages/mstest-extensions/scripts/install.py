"""Link the plugin's skills into local Codex and optionally Claude discovery."""
import argparse
from pathlib import Path


def install(sources, destination_roots):
    sources = [source.resolve(strict=True) for source in sources]
    links = [(source, root / source.name) for root in destination_roots for source in sources]
    for source, destination in links:
        if destination.exists() or destination.is_symlink():
            if not destination.is_symlink() or destination.resolve() != source:
                raise FileExistsError(f"Refusing to replace existing skill: {destination}")
    for source, destination in links:
        if destination.is_symlink():
            print(f"Already linked: {destination}")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.symlink_to(source, target_is_directory=True)
            print(f"Linked: {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claude", action="store_true", help="Also install for Claude Code")
    parser.add_argument("--agents-dir", type=Path, default=Path.home() / ".agents" / "skills")
    parser.add_argument("--claude-dir", type=Path, default=Path.home() / ".claude" / "skills")
    args = parser.parse_args()
    sources = sorted(path.parent for path in (Path(__file__).resolve().parents[1] / "skills").glob("*/SKILL.md"))
    destinations = [args.agents_dir]
    if args.claude:
        destinations.append(args.claude_dir)
    install(sources, destinations)


if __name__ == "__main__":
    main()
