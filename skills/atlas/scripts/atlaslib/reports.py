"""Human-readable reports share the same facts as JSON output."""

def cite(node):
    return f"`{node['path'] or node['id']}{'::' + node['symbol'] if node.get('symbol') and node['type'] != 'commit' else ''}{':' + str(node['line']) if node.get('line') and node['path'] else ''}`"


def markdown(report):
    kind = report['kind']
    lines = [f"# Atlas {kind}", '', f"Snapshot: `{report.get('snapshot_hash', 'unavailable')}`", '']
    if kind == 'context':
        lines += [f"Task: {report['task']}", '', '## Read first', '']
        lines += [f"- {cite(n)} — {n['type']} (lexical candidate; inspect source)" for n in report['nodes']] or ['No lexical matches; inspect repository entry points.']
        for title, key in [('Constraints', 'constraints'), ('Verify', 'verify')]:
            lines += ['', f'## {title}', ''] + ['- ' + s for s in report[key]]
    if kind in {'context', 'impact'}:
        if kind == 'impact':
            lines += ['Target: ' + ', '.join(cite(n) for n in report['selected'])]
        for title, key in [('Direct candidates', 'direct'), ('Indirect candidates', 'indirect')]:
            nodes = report[key]
            lines += ['', f'## {title}', ''] + [f"- {cite(n)} — {n['type']}" for n in nodes[:30]]
            if len(nodes) > 30:
                lines += [f'- {len(nodes) - 30} more nodes; use `--json` for the complete set.']
            if not nodes:
                lines += ['- None established by this graph.']
    if kind == 'explain':
        lines += [f"- {cite(n)} — {n['type']}" for n in report['nodes']]
        lines += ['', '## Observed relationships', '']
        lines += [f"- `{e['type']}` `{e['source']}` → `{e['target']}` ({e['origin']}, {e['confidence']}) — {e['explanation']}" for e in report['edges'][:30]]
        lines += ['', 'Semantic meaning: **not established**.']
    if kind == 'verification':
        lines += [f"Result: **{report['result']}**", '']
        for check in report['checks']:
            lines += [f"- **{check['result']}** `{check['name']}` — {check.get('reason', check.get('behavior', ''))}"]
            for key in ('stdout', 'stderr'):
                if key in check:
                    lines += [f"  - {key}: `{check[key]['path']}`"]
        lines += ['', f"Run record: `{report['record']}`"]
    if kind in {'drift', 'review'}:
        if kind == 'review':
            lines += ['## Changed paths', ''] + ['- `' + p + '`' for p in report['changed']]
        lines += ['', '## Findings', '']
        lines += [f"- **{f['status']}** `{f['kind']}` `{f.get('path', '')}` — {f.get('message', '')}" for f in report['findings']]
        if not report['findings']:
            lines += ['- No structural gaps or stale runs found. Semantic coverage remains unestablished.']
    if report.get('limitations'):
        lines += ['', '## Limits', ''] + ['- ' + s for s in report['limitations']]
    return '\n'.join(lines) + '\n'
