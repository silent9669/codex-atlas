"""Human-readable reports share the same facts as JSON output."""
import json

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
    if kind == 'audit':
        lines += [f"Nodes: **{report['counts']['nodes']}** · edges: **{report['counts']['edges']}** · diagnostics: **{report['counts']['diagnostics']}** · findings: **{report['counts']['findings']}**", '', '## Node types', '']
        lines += [f'- `{key}`: {value}' for key, value in report['node_types'].items()]
        lines += ['', '## Findings', ''] + [f"- **{f['status']}** `{f['kind']}` `{f.get('path', '')}` — {f.get('message', '')}" for f in report['findings']]
    if kind == 'documents':
        lines += [f"Documents: **{report['summary']['count']}**", '', '## By type', '']
        lines += [f'- `{key}`: {value}' for key, value in report['summary']['by_type'].items()]
        lines += ['', '## Document labels', '']
        for doc in report['documents']:
            label = doc.get('labels', {})
            lines += [f"- `{doc['path']}` — {label.get('kind', doc['type'])} · {', '.join(label.get('topics', []))} · {label.get('status', 'unclassified')} ({label.get('origin', 'rule-inferred')}{', stale' if label.get('freshness') == 'stale' else ''})"]
        lines += ['', '## Needs review', '']
        lines += [f'- Missing title: `{path}`' for path in report['summary']['missing_title']]
        lines += [f'- Decision/plan without acceptance criteria: `{path}`' for path in report['summary']['decision_or_plan_without_acceptance']]
    if kind == 'decision':
        lines += [f"Task: {report['task']}", f"Mode: **{report['mode']}** · status: **{report['status']}**", f"Model route: `{report['routing']['model']}` — {report['routing']['reason']}", '', '## Advisor output', '']
        advisor = report.get('advisor', {})
        lines += [f"- Recommendation: {advisor.get('recommendation', report.get('reason', ''))}", f"- Confidence: `{advisor.get('confidence', 'unavailable')}`"]
        lines += ['', '## Evidence paths', ''] + [f'- `{path}`' for path in report['evidence_paths']]
        lines += ['', '## Codex handoff', '', f"```text\n{advisor.get('codex_prompt', 'Set OPENAI_API_KEY locally and rerun atlas decide --live.') }\n```"]
    if kind == 'codex-handoff':
        lines += [f"Task: {report['task']}", f"Result: **{report['result']}**", f"Model route: `{report['model_route']['model']}` — {report['model_route']['reason']}", '', '## Candidate evidence', '']
        if report.get('reason'): lines += [report['reason'], '']
        if report.get('finalize'): lines += [markdown(report['finalize'])]
        lines += [f'- `{path}`' for path in report['evidence_paths']]
        lines += ['', '## Prompt', '', f"```text\n{report['prompt']}\n```", '', '## Structured command', '', f"`{report['command']}`"]
    if kind == 'models':
        lines += [f"Status: **{report['status']}**", '']
        if report.get('models'):
            lines += ['## Visible model IDs', ''] + [f'- `{model}`' for model in report['models']]
        for key in ('reason', 'limitation'):
            if report.get(key): lines.append(f"- {report[key]}")
    if kind == 'route':
        route = report['routing']
        lines += [f"Status: **{report['status']}**", f"Router: `{report['router_model']}`", f"Execution model: **{route['model']}** · `{route['effort']}`", route['reason'], '']
        if report.get('workspace'): lines += [f"Live graph: {report['workspace']['url']}", '']
        if report.get('reason'): lines += [report['reason'], '']
        if report.get('execution'): lines += [markdown(report['execution'])]
    if kind == 'label':
        lines += [f"Document: `{report['path']}`", json.dumps(report['labels'], ensure_ascii=False)]
    if kind == 'finalize':
        lines += [f"Result: **{report['result']}**", f"Snapshot: `{report['snapshot_hash']}`", '', f"- Documentation: `{report['documentation']}`", f"- Project memory: `{report['memory']}`"]
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
