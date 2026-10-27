#!/usr/bin/env python3
"""Generate a local view of the one catalog, linking explicit source checkouts."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', action='append', required=True, metavar='NAME=PATH')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / '.agents/plugins/marketplace.json').read_text())
    sources = {}
    for value in args.source:
        name, separator, location = value.partition('=')
        if not separator or name in sources:
            raise ValueError(f'Expected one NAME=PATH per package: {value}')
        sources[name] = Path(location).resolve(strict=True)
    names = {entry['name'] for entry in catalog['plugins']}
    if set(sources) != names:
        raise ValueError(f'Source names must match catalog: {sorted(names)}')
    destination = root / '.local/marketplace'
    links = destination / 'plugins'
    for entry in catalog['plugins']:
        source = sources[entry['name']]
        manifest = json.loads((source / 'plugin.json').read_text())
        if manifest['name'] != entry['name']:
            raise ValueError(f'Wrong plugin identity at {source}')
        link = links / entry['name']
        if link.exists() and not link.is_symlink():
            raise ValueError(f'Refusing to replace a real directory: {link}')
    links.mkdir(parents=True, exist_ok=True)
    for entry in catalog['plugins']:
        name = entry['name']
        link = links / name
        if link.is_symlink():
            link.unlink()
        link.symlink_to(sources[name], target_is_directory=True)
        entry['source'] = {'source': 'local', 'path': './plugins/' + name}
    manifest_path = destination / '.agents/plugins/marketplace.json'
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(catalog, indent=2) + '\n')
    print(destination)


if __name__ == '__main__':
    main()
