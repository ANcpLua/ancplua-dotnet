"""Verify the committed catalog resolves to complete package identities."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
assert catalog['name'] == 'ancplua-dotnet'
seen = set()
for entry in catalog['plugins']:
    name = entry['name']
    assert name not in seen, f'Duplicate plugin: {name}'
    seen.add(name)
    source = entry['source']
    assert source['source'] == 'git-subdir'
    assert source['url'] == 'https://github.com/ANcpLua/ancplua-dotnet.git'
    package = (ROOT / source['path']).resolve()
    assert package.is_relative_to(ROOT)
    manifest = json.loads((package / 'plugin.json').read_text())
    assert manifest['name'] == name, f'Wrong identity at {package}'
    skills = list((package / 'skills').glob('*/SKILL.md'))
    assert len(skills) == {'ancplua-dotnet': 7, 'nami': 5, 'mstest-extensions': 9, 'prepare-plugin-submission': 1}[name]
    assert not any(p.is_symlink() for p in package.rglob('*')), f'Symlink in {name}'
    print(f"{name}: {manifest['version']}, {len(skills)} skills, {source['path']}")
assert seen == {'ancplua-dotnet', 'nami', 'mstest-extensions', 'prepare-plugin-submission'}
print('Marketplace: all package identities and source paths verified; all four sources are contained in this repository.')
