"""Named Atlas commands, with the same explicit execution boundary as task routing."""
import json
from . import evidence


def run_command(root, graph, message, env_file=None, progress=None):
    result = _run_command(root, graph, message, env_file, progress)
    result.setdefault('kind', 'command')
    result.setdefault('snapshot_hash', graph['snapshot']['hash'])
    return result


def _run_command(root, graph, message, env_file=None, progress=None):
    from .command import parse
    from .routing import execute
    task, options = parse(message)
    action = options.pop('action', 'task')
    if action == 'organize':
        if not options['run']:
            return {'status': 'preview', 'reason': 'Organize documents with AI-created categories. Add RUN=true to apply category metadata; source files stay in place.'}
        from .categories import organize
        if progress: progress('organizing')
        result = organize(root, graph, env_file)
        if result.get('status') == 'organized':
            result['reason'] = f"Organized {result['categorized']} documents. {result['remaining']} remain in the next batch."
        return result
    if action == 'memory':
        if progress: progress('remembering')
        if not options['run']:
            return {'status': 'preview', 'reason': 'Record docs and project memory from the latest successful implementation. Add RUN=true.'}
        folder = evidence.storage(root) / 'handoffs'
        if folder.is_symlink(): raise ValueError('Refusing symlinked handoffs.')
        for path in sorted(folder.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True):
            if path.is_symlink(): continue
            try: record = json.loads(path.read_text())
            except (ValueError, OSError): continue
            if not isinstance(record, dict) or record.get('kind') != 'codex-handoff': continue
            if record.get('result') != 'passed' or record.get('sandbox') != 'workspace-write' or record.get('analysis', {}).get('outcome', 'completed') != 'completed' or record.get('analysis', {}).get('blocked') or not record.get('analysis', {}).get('checks'):
                continue
            if record.get('finalize'):
                recorded = record['finalize'].get('source_files')
                current = {p: h for p, h in graph['snapshot']['files'].items() if not p.startswith('docs/atlas/updates/')}
                if recorded is None:
                    return {'status': 'recorded', 'reason': 'This run is already recorded. Its older record cannot establish current source freshness; audit before relying on it.', 'execution': record}
                if recorded != current:
                    return {'status': 'stale', 'reason': 'Sources changed after this recorded run. Audit the current implementation and docs before relying on its memory.', 'execution': record}
                return {'status': 'current', 'reason': 'This successful run is already recorded in docs and project memory.', 'execution': record}
            if record.get('result_snapshot_hash') != graph['snapshot']['hash'] or not record.get('final_artifact'):
                return {'status': 'blocked', 'reason': 'The implementation snapshot has changed or its completion artifact is missing. Audit the current sources first.'}
            from .finalize import finalize
            record['finalize'] = finalize(root, record['task'], result_file=record['final_artifact'], changed_paths=record.get('changed_paths'))
            evidence.write_json(path, record)
            return {'status': 'recorded', 'reason': 'Updated project documentation and memory.', 'execution': record}
        return {'status': 'blocked', 'reason': 'No successful implementation run is available. Complete and verify an implementation first.'}
    if action == 'docs':
        task = 'Write or update project documentation for this task, inspect implementation first, cite relevant paths, and distinguish tested behavior from gaps: ' + task
    elif action == 'audit':
        if options['allow_edits']: raise ValueError('Audit is read-only. Use a separate implementation task for fixes.')
        task = 'Audit implementation against project documents. Point out concrete contradictions, stale claims, missing checks and problems with file and line citations. Do not edit files or claim unrun checks passed. ' + task
    result = execute(root, graph, task, live=True, env_file=env_file, progress=progress, **options)
    return result
