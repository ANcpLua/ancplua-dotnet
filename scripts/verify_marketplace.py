"""Verify the committed catalog resolves to complete package identities."""
import json
import re
import yaml
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
    assert len(skills) == {'ancplua-dotnet': 7, 'nami': 3, 'mstest-extensions': 2, 'prepare-plugin-submission': 1}[name]
    for skill in skills:
        text = skill.read_text()
        assert text.startswith('---\n'), f'Missing frontmatter: {skill}'
        metadata = yaml.safe_load(text.split('---', 2)[1])
        assert isinstance(metadata, dict), f'Invalid frontmatter: {skill}'
        skill_name = metadata.get('name', '')
        assert isinstance(skill_name, str) and skill_name == skill.parent.name, f'Wrong skill identity: {skill}'
        assert len(skill_name) <= 64 and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', skill_name), f'Invalid skill name: {skill}'
        description = metadata.get('description')
        assert isinstance(description, str) and 0 < len(description.strip()) <= 1024, f'Invalid skill description: {skill}'
    assert not any(p.is_symlink() for folder in ['skills', 'assets'] for p in (package / folder).rglob('*')), f'Symlink in packaged resources of {name}'
    print(f"{name}: {manifest['version']}, {len(skills)} skills, {source['path']}")
assert seen == {'ancplua-dotnet', 'nami', 'mstest-extensions', 'prepare-plugin-submission'}
print('Marketplace: all package identities and source paths verified; all four sources are contained in this repository.')
