"""Readable task and project-memory records, with source-bound freshness."""
import json
import re
from . import evidence


def records(root, folder, limit=100):
    directory = evidence.storage(root) / folder
    if directory.is_symlink(): return []
    candidates = []
    for path in directory.glob('*.json'):
        try:
            if not path.is_symlink() and path.is_file() and path.stat().st_size <= 2_000_000:
                candidates.append((path.stat().st_mtime, path))
        except OSError: continue
    entries = []
    for _, path in sorted(candidates, reverse=True)[:limit]:
        try:
            value = json.loads(path.read_text())
            if isinstance(value, dict): entries.append((path.name, value))
        except (OSError, ValueError): continue
    return entries


def strings(value):
    return [v[:4000] for v in value if isinstance(v, str)][:40] if isinstance(value, list) else []


def mapping(value):
    return value if isinstance(value, dict) else {}


def string(value, default=''):
    return value[:4000] if isinstance(value, str) else default


def summary(root, graph):
    current = {p: h for p, h in graph['snapshot']['files'].items() if not p.startswith('docs/atlas/updates/')}
    memories = []
    for name, record in records(root, 'completions'):
        if record.get('result') != 'completed': continue
        source = record.get('source_files')
        memories.append({
            'id': name, 'task': string(record.get('task')) or string(record.get('documentation'), 'Previous task'),
            'summary': strings(record.get('summary')), 'checks': strings(record.get('checks')),
            'paths': strings(record.get('changed')), 'document': record.get('documentation'),
            'recorded_at': record.get('recorded_at'),
            'freshness': 'unknown' if source is None else 'current' if source == current else 'stale',
            'origin': 'codex-reported',
        })
    runs = []
    for name, record in records(root, 'routes', 40):
        execution = mapping(record.get('execution'))
        analysis = mapping(execution.get('analysis'))
        runs.append({
            'id': name, 'task': string(record.get('task')), 'recorded_at': record.get('recorded_at'),
            'status': execution.get('result', record.get('status', 'unknown')),
            'router': record.get('router_model'), 'route': mapping(record.get('routing')),
            'model': mapping(execution.get('model_route')).get('model'),
            'checks': strings(analysis.get('checks')), 'impact': strings(analysis.get('impact')),
            'reason': execution.get('reason') or record.get('reason'),
            'paths': strings(execution.get('changed_paths')), 'completion': mapping(execution.get('finalize')) or None,
            'sandbox': execution.get('sandbox'), 'usage': execution.get('usage'),
        })
    return evidence.sanitize({'runs': runs, 'memories': memories})


def recall(root, graph, query, limit=4):
    terms = set(re.findall(r'\w{3,}', query.lower()))
    candidates = []
    for memory in summary(root, graph)['memories']:
        if memory['freshness'] != 'current': continue
        words = set(re.findall(r'\w{3,}', ' '.join([memory['task'], *memory['paths'], *memory['summary']]).lower()))
        score = len(terms & words)
        if score: candidates.append((score, memory))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [dict(task=m['task'], summary=m['summary'][:3], checks=m['checks'][:3], document=m['document'])
            for _, m in candidates[:limit]]
