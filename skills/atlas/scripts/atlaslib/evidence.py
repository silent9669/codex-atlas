"""Explicit reviewed command execution and conservative snapshot-bound evidence."""
import datetime as dt
import json
import os
import pathlib
import platform
import re
import subprocess
import uuid
from .graph import digest, inventory


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def runtime():
    try:
        node = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        node = 'unavailable'
    return {'python': platform.python_version(), 'node': node, 'platform': platform.system(), 'atlas': '0.1.0'}


def redact(value):
    value = str(value)
    # Access-bearing URLs and common credential formats are never retained.
    value = re.sub(r'https?://[^\s<>"\']+', lambda m: m[0].split('?')[0].split('#')[0] + ('?[REDACTED]' if '?' in m[0] or '#' in m[0] else ''), value)
    value = re.sub(r'(?i)(https?://)[^/\s:@]+:[^/\s@]+@', r'\1[REDACTED]@', value)
    value = re.sub(r'(?i)(bearer\s+)[\w.\-]+', r'\1[REDACTED]', value)
    value = re.sub(r'(?i)((?:api[_-]?key|access[_-]?token|token|password|secret|cookie|authorization)\s*[=:]\s*)[^\s,;\"\']+', r'\1[REDACTED]', value)
    value = re.sub(r'\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{10,})\b', '[REDACTED]', value)
    value = re.sub(r'-----BEGIN [^-]*(?:PRIVATE KEY)[^-]*-----[\s\S]*?-----END [^-]*-----', '[REDACTED]', value)
    # Also scrub actual inherited secret values even when commands print them without labels.
    for key, secret in os.environ.items():
        if len(secret) >= 8 and re.search(r'(?i)(token|secret|password|api_?key)', key):
            value = value.replace(secret, '[REDACTED]')
    return value


def sanitize(value):
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, dict):
        return {key: sanitize(v) for key, v in value.items()}
    return value


def storage(root):
    path = root / '.atlas'
    if path.is_symlink():
        raise ValueError('Refusing symlinked .atlas output directory.')
    path.mkdir(exist_ok=True, mode=0o700)
    return path


def write_json(path, value):
    if path.is_symlink():
        raise ValueError('Refusing symlinked output file.')
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    path.chmod(0o600)


def verify(root, graph, command_file=None, execute=False, target=None, model=None, task_id=None):
    folder = storage(root) / 'evidence'
    if folder.is_symlink():
        raise ValueError('Refusing symlinked evidence directory.')
    folder.mkdir(exist_ok=True, mode=0o700)
    mapping = pathlib.Path(command_file) if command_file else root / '.atlas/commands.json'
    if not mapping.is_absolute():
        mapping = root / mapping
    if not mapping.resolve().is_relative_to(root):
        raise ValueError('Command map must be inside the repository root.')
    map_hash = digest(mapping.read_bytes()) if mapping.is_file() else None
    specs = json.loads(mapping.read_text()) if map_hash else []
    if not isinstance(specs, list) or any(not isinstance(s, dict) for s in specs):
        raise ValueError('Command map must be a list of reviewed {name, argv, cwd, behavior, claim_ids} objects.')
    for spec in specs:
        if not isinstance(spec.get('argv'), list) or not spec['argv'] or not all(isinstance(a, str) for a in spec['argv']) or not isinstance(spec.get('name'), str):
            raise ValueError('Every check needs a name and a nonempty string argv array.')
        if not isinstance(spec.get('cwd', '.'), str) or not isinstance(spec.get('timeout', 300), (int, float)) or spec.get('timeout', 300) <= 0:
            raise ValueError('cwd must be a string and timeout a positive number.')
    checks = []
    run_id = uuid.uuid4().hex
    if not specs:
        checks.append({'name': 'command-map', 'result': 'blocked', 'reason': 'No reviewed checks available.',
                       'started_at': now(), 'ended_at': now(), 'snapshot_hash': graph['snapshot']['hash'], 'argv': [], 'cwd': '.'})
    for index, spec in enumerate(specs):
        start_snapshot = inventory(root)
        check = {'name': spec['name'], 'argv': [redact(a) for a in spec['argv']], 'cwd': redact(spec.get('cwd', '.')),
                 'claim_ids': spec.get('claim_ids', []), 'behavior': redact(spec.get('behavior', 'Command execution only; no business behavior claim established.')),
                 'snapshot_hash': start_snapshot['hash'], 'started_at': now(), 'exit_code': None, 'result': 'not-run', 'freshness': 'current'}
        cwd = (root / spec.get('cwd', '.')).resolve()
        if not cwd.is_relative_to(root) or not cwd.is_dir():
            check.update(result='blocked', reason='Working directory is unavailable or outside this repository.')
        elif execute:
            stdout = stderr = ''
            try:
                process = subprocess.run(spec['argv'], cwd=cwd, capture_output=True, timeout=spec.get('timeout', 300))
                stdout, stderr = process.stdout, process.stderr
                check.update(result='passed' if process.returncode == 0 else 'failed', exit_code=process.returncode)
            except FileNotFoundError:
                check.update(result='blocked', reason='Executable not found.')
            except subprocess.TimeoutExpired as exc:
                stdout, stderr = exc.stdout or b'', exc.stderr or b''
                check.update(result='failed', reason='Check exceeded reviewed timeout.')
            except OSError as exc:
                check.update(result='blocked', reason=redact(str(exc)))
            for kind, content in [('stdout', stdout), ('stderr', stderr)]:
                if isinstance(content, bytes):
                    content = content.decode('utf-8', 'replace')
                output = redact(content)[:200_000]
                artifact = folder / f'{run_id}-{index}-{kind}.log'
                artifact.write_text(output)
                artifact.chmod(0o600)
                check[kind] = {'path': artifact.relative_to(root).as_posix(), 'hash': digest(artifact.read_bytes()), 'truncated': len(redact(content)) > 200_000}
        check['ended_at'] = now()
        check['end_snapshot_hash'] = inventory(root)['hash'] if execute else start_snapshot['hash']
        if check['end_snapshot_hash'] != start_snapshot['hash']:
            check['freshness'] = 'stale'
        checks.append(check)
    statuses = {c['result'] for c in checks}
    result = 'failed' if 'failed' in statuses else 'blocked' if 'blocked' in statuses else 'not-run' if not execute else 'passed'
    freshness = 'stale' if any(c.get('freshness') == 'stale' for c in checks) else 'current'
    if result == 'passed' and freshness == 'stale':
        result = 'blocked'
    record = {'schema_version': '1.0', 'kind': 'verification', 'run_id': run_id, 'snapshot': graph['snapshot'],
              'snapshot_hash': graph['snapshot']['hash'], 'checks': checks, 'result': result, 'freshness': freshness, 'recorded_at': now(),
              'command_map': {'path': str(mapping), 'hash': map_hash}, 'runtime': runtime(), 'target': target,
              'codex': {'model': model or 'unavailable', 'task_id': task_id or 'unavailable', 'usage': 'unavailable', 'cost': 'unavailable'},
              'human_approval': 'not-recorded'}
    # Redact metadata as well as logs. Hashes always describe the retained sanitized artifacts.
    record = sanitize(record)
    destination = folder / f'run-{run_id}.json'
    write_json(destination, record)
    record['record'] = destination.relative_to(root).as_posix()
    return record


def attach(root, graph):
    """Attach persisted run results to claim nodes without upgrading confidence."""
    folder = root / '.atlas/evidence'
    if not folder.exists() or folder.is_symlink():
        return graph
    nodes = {n['id']: n for n in graph['nodes']}
    edges = {e['id']: e for e in graph['edges']}
    stale_paths = {f['path'] for f in drift(root, graph)['findings'] if f['status'] == 'stale'}
    for path in sorted(folder.glob('run-*.json')):
        if path.is_symlink():
            continue
        record = json.loads(path.read_text())
        freshness = 'stale' if path.relative_to(root).as_posix() in stale_paths else record.get('freshness', 'current')
        run_id = 'runtime:' + record.get('run_id', path.stem[4:])
        nodes.setdefault(run_id, {'id': run_id, 'type': 'runtime-check', 'path': path.relative_to(root).as_posix(),
                                  'symbol': None, 'label': record.get('result', 'unknown'), 'line': 1,
                                  'end_line': 1, 'content_hash': digest(path.read_bytes()),
                                  'result': record.get('result'), 'freshness': freshness})
        claims = {claim for check in record.get('checks', []) for claim in check.get('claim_ids', [])}
        for claim in claims:
            if claim not in nodes:
                continue
            edge_id = 'edge:' + digest([claim, run_id, 'verified_by'])[:24]
            edges[edge_id] = {'id': edge_id, 'source': claim, 'target': run_id, 'type': 'verified_by',
                              'origin': 'parsed', 'confidence': 'observed', 'freshness': freshness,
                              'evidence': [{'path': path.relative_to(root).as_posix(), 'line': 1, 'content_hash': digest(path.read_bytes())}],
                              'explanation': 'A recorded command claimed this node; inspect the exact argv and evidence artifact.'}
    graph['nodes'] = sorted(nodes.values(), key=lambda n: n['id'])
    graph['edges'] = sorted(edges.values(), key=lambda e: e['id'])
    return graph


def drift(root, graph):
    findings = [{'status': 'needs-review', **d} for d in graph['diagnostics']]
    folder = storage(root) / 'evidence'
    if folder.is_symlink():
        raise ValueError('Refusing symlinked evidence directory.')
    for file in sorted(folder.glob('run-*.json')) if folder.exists() else []:
        if file.is_symlink():
            continue
        record = json.loads(file.read_text())
        reasons = []
        if record['snapshot_hash'] != graph['snapshot']['hash']:
            reasons.append('Repository commit or working-tree content changed.')
        if record['runtime'] != runtime():
            reasons.append('Runtime versions changed.')
        mapping = record.get('command_map', {})
        path = pathlib.Path(mapping.get('path', ''))
        if mapping.get('hash') and (not path.is_file() or digest(path.read_bytes()) != mapping['hash']):
            reasons.append('Reviewed command map changed or disappeared.')
        if any(c.get('freshness') == 'stale' for c in record['checks']):
            reasons.append('Files changed during execution.')
        for check in record['checks']:
            for stream in ('stdout', 'stderr'):
                artifact = check.get(stream)
                if artifact:
                    path = root / artifact['path']
                    if not path.resolve().is_relative_to(root) or not path.is_file() or path.is_symlink() or digest(path.read_bytes()) != artifact['hash']:
                        reasons.append('Evidence artifact missing or modified.')
        if reasons:
            findings.append({'status': 'stale', 'kind': 'verification', 'path': file.relative_to(root).as_posix(), 'message': ' '.join(sorted(set(reasons)))})
    return {'kind': 'drift', 'snapshot_hash': graph['snapshot']['hash'], 'findings': findings,
            'limitations': ['Missing or ambiguous evidence is not proof of an implementation defect. Semantic drift needs source review.']}
