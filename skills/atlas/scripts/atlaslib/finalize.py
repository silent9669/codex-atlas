"""Create provenance-marked project docs and memory after a routed Codex task."""
import datetime as dt
import json
import os
import pathlib
import re
from . import evidence
from .graph import git, index_repository


def _slug(value):
    slug = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return slug[:64] or 'atlas-task'


def finalize(root, task, result='completed', result_file=None, note=None, memory_scope='project', changed_paths=None):
    if memory_scope not in {'project'}:
        raise ValueError('Only project memory is supported automatically; global memory needs explicit user review.')
    folder = evidence.storage(root)
    task = evidence.redact(' '.join(task.split()))[:1000]
    graph = index_repository(root)
    now = dt.datetime.now(dt.timezone.utc)
    changed = set(git(root, 'diff', '--name-only', 'HEAD').splitlines())
    changed.update(git(root, 'ls-files', '--others', '--exclude-standard').splitlines())
    changed = sorted(path for path in changed if path and not path.startswith('.atlas/'))
    if changed_paths is not None:
        changed = sorted(changed_paths)
    if result_file:
        source = pathlib.Path(result_file)
        if not source.is_absolute(): source = root / source
        if not source.resolve().is_relative_to(root) or not source.is_file() or source.is_symlink():
            raise ValueError('--result-file must be a regular file inside the repository.')
        if source.stat().st_size > 1_000_000: raise ValueError('Result file exceeds 1 MB.')
        raw = evidence.redact(source.read_text(errors='replace'))[:12000].replace('```', "'''")
    else:
        raw = ''
    # Generated update documents must not change the identity of a repeated call.
    identity = evidence.digest({'task': task, 'result': result, 'output': raw,
        'files': {p: h for p, h in graph['snapshot']['files'].items() if not p.startswith('docs/atlas/updates/')}})
    record = folder / 'completions' / (identity + '.json')
    if record.parent.is_symlink() or record.is_symlink():
        raise ValueError('Refusing symlinked completion storage.')
    if record.exists():
        return json.loads(record.read_text())
    memory = folder / 'memory.md'
    if memory.is_symlink(): raise ValueError('Refusing symlinked project memory.')
    stamp = now.strftime('%Y-%m-%d')
    slug = _slug(task)
    docs_dir = root / 'docs/atlas/updates'
    if any(path.is_symlink() for path in [docs_dir, docs_dir.parent, docs_dir.parent.parent]):
        raise ValueError('Refusing symlinked documentation output.')
    docs_dir.mkdir(parents=True, exist_ok=True)
    doc = docs_dir / f'{stamp}-{slug}-{identity[:12]}.md'
    if doc.is_symlink():
        raise ValueError('Refusing symlinked documentation output.')
    changed_lines = [f'- `{path}`' for path in changed] if changed else ['- No changed paths detected at finalization.']
    body = '\n'.join([
        f'# Atlas update — {task}', '',
        f'- Recorded: `{now.isoformat()}`', f'- Result: **{result}**', f'- Snapshot: `{graph["snapshot"]["hash"]}`',
        '- Origin: `codex-atlas routed task`', '',
        '## Task changed paths' if changed_paths is not None else '## Observed working-tree changes (may predate this task)', '',
        *changed_lines,
        '', '## Evidence', '',
        f'- Nodes: {len(graph["nodes"])}', f'- Relationships: {len(graph["edges"])}', f'- Diagnostics: {len(graph["diagnostics"])}',
        '- Semantic claims remain unverified until a human reviews the sources and command evidence.',
        '', '## Result excerpt', '', '```text', raw or 'No result file supplied.', '```',
        '', '## Note', '', evidence.redact(note or 'Generated record; not a human acceptance decision.'),
    ]) + '\n'
    # A task/snapshot pair is the durable identity. Re-running finalization
    # updates the same record instead of creating noisy duplicate notes.
    if doc.exists() and not doc.is_file():
        raise ValueError('Documentation output is not a regular file.')
    # O_NOFOLLOW also protects the final component against a symlink race.
    descriptor = os.open(doc, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        output.write(body)
    memory = folder / 'memory.md'
    if memory.is_symlink(): raise ValueError('Refusing symlinked project memory.')
    previous = memory.read_text() if memory.exists() and not memory.is_symlink() else '# Atlas project memory\n\n'
    marker = f'<!-- atlas:{identity} -->'
    entry = f'- `{now.isoformat()}` **{result}** — {task}. Snapshot `{graph["snapshot"]["hash"][:12]}`; update `{doc.relative_to(root).as_posix()}`. {marker}\n'
    if marker not in previous:
        memory.write_text(previous.rstrip() + '\n' + entry)
        memory.chmod(0o600)
    details = {}
    if raw:
        try: details = json.loads(raw)
        except ValueError: pass
    if not isinstance(details, dict): details = {}
    for field in ('checks', 'impact'):
        if not isinstance(details.get(field), list): details[field] = []
    result = {'task': task, 'checks': [v for v in details.get('checks', []) if isinstance(v, str)][:12],
            'summary': [v for v in details.get('impact', []) if isinstance(v, str)][:5], 'kind': 'finalize', 'result': result, 'snapshot_hash': graph['snapshot']['hash'],
            'documentation': doc.relative_to(root).as_posix(), 'memory': memory.relative_to(root).as_posix(), 'changed': changed,
            'recorded_at': now.isoformat(),
            'source_files': {p: h for p, h in graph['snapshot']['files'].items() if not p.startswith('docs/atlas/updates/')}}
    record.parent.mkdir(exist_ok=True, mode=0o700)
    evidence.write_json(record, result)
    return result
