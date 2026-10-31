#!/usr/bin/env python3
"""Build a clean local marketplace, excluding runtime data, credentials and Git history."""
import json
import pathlib
import shutil
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = ('plugin.json', 'package.json', 'package-lock.json', 'README.md', 'CHANGELOG.md')
FOLDERS = ('skills', 'prompts', 'docs', 'examples', 'schemas')


def build(root=ROOT):
    storage = root / '.atlas'
    destination = storage / 'plugin-marketplace'
    if storage.is_symlink() or destination.is_symlink():
        raise ValueError('Refusing symlinked package output.')
    storage.mkdir(exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix='package-', dir=storage) as temporary:
        staging = pathlib.Path(temporary)
        plugin = staging / 'plugins/codex-atlas'
        plugin.mkdir(parents=True)
        sources = [root / name for name in FILES]
        for name in FOLDERS:
            folder = root / name
            if folder.is_symlink(): raise ValueError('Refusing symlinked package source.')
            sources.extend(p for p in folder.rglob('*') if '__pycache__' not in p.parts)
        for source in sources:
            relative = source.relative_to(root)
            if any(part in {'.git', '.atlas', '.taste-skill', 'node_modules', '__pycache__'} or part.startswith('.env') for part in relative.parts) or source.suffix in {'.pem', '.key'}:
                continue
            if source.is_symlink(): raise ValueError('Refusing symlinked package source.')
            if not source.is_file() or source.suffix in {'.pyc', '.pyo'}: continue
            target = plugin / source.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        marketplace = staging / '.agents/plugins/marketplace.json'
        marketplace.parent.mkdir(parents=True)
        marketplace.write_text(json.dumps({
            'name': 'codex-atlas', 'interface': {'displayName': 'Codex Atlas'},
            'plugins': [{'name': 'codex-atlas', 'source': {'source': 'local', 'path': './plugins/codex-atlas'},
                         'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_USE'},
                         'category': 'Developer tools'}]}, indent=2) + '\n')
        if destination.exists(): shutil.rmtree(destination)
        shutil.copytree(staging, destination)
    return destination


if __name__ == '__main__':
    print(build())
