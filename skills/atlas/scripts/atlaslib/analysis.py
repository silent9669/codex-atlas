"""Bounded structural context. History never becomes a dependency bridge."""
import re


def select(graph, target):
    exact = [n for n in graph['nodes'] if n['id'] == target]
    if exact:
        return exact
    files = [n for n in graph['nodes'] if n['path'] == target and n['id'].startswith('file:')]
    if files:
        return files
    return [n for n in graph['nodes'] if n.get('symbol') == target]


def neighbors(graph, seeds, depth=3):
    # contains connects declarations to their file only; commits are historical metadata.
    usable = [e for e in graph['edges'] if e['type'] in {'depends_on', 'tested_by', 'references', 'exposes', 'renders', 'implements'}]
    seen, layers, frontier = set(seeds), [], set(seeds)
    for _ in range(depth):
        found = set()
        for edge in usable:
            # For dependency impact, propagate to consumers, never through shared imports.
            if edge['target'] in frontier and edge['type'] == 'depends_on':
                found.add(edge['source'])
            elif edge['type'] != 'depends_on':
                if edge['source'] in frontier:
                    found.add(edge['target'])
                if edge['target'] in frontier:
                    found.add(edge['source'])
        frontier = found - seen
        seen.update(frontier)
        layers.append(frontier)
    by_id = {n['id']: n for n in graph['nodes']}
    return [[by_id[i] for i in sorted(layer) if i in by_id] for layer in layers]


def impact(graph, target):
    chosen = select(graph, target)
    if not chosen:
        raise ValueError(f'No indexed node matches {target!r}. Use a repository-relative path or node ID.')
    seeds = {n['id'] for n in chosen}
    # Symbol changes affect their containing module.
    seeds.update('file:' + n['path'] for n in chosen)
    layers = neighbors(graph, seeds)
    return {'kind': 'impact', 'target': target, 'selected': chosen, 'direct': layers[0],
            'indirect': [n for layer in layers[1:] for n in layer],
            'limitations': ['Affected nodes are structural candidates, not confirmed runtime behavior.',
                            'Three dependency hops; shared Git history is excluded.']}


def context(graph, query, root, limit=12):
    stop = {'add', 'the', 'and', 'for', 'with', 'this', 'that', 'from', 'into', 'what', 'must', 'change'}
    terms = {t.lower().rstrip('s') for t in re.findall(r'[\w/-]+', query) if len(t) > 2 and t.lower() not in stop}
    scored = []
    for node in graph['nodes']:
        if not node['id'].startswith('file:'):
            continue
        name = (node['path'] + ' ' + node['label']).lower()
        score = sum(4 for term in terms if term in name)
        # Search is local and only metadata/citations are returned, never raw file contents.
        file = root / node['path']
        if file.suffix in {'.md', '.py', '.ts', '.tsx', '.js', '.jsx'} and file.stat().st_size <= 1_000_000:
            body = file.read_text(errors='replace').lower()
            score += sum(1 for term in terms if term in body)
        if score:
            scored.append((score, node))
    scored.sort(key=lambda item: (-item[0], item[1]['path']))
    if not scored:
        scored = [(0, node) for node in graph['nodes'] if node.get('id', '').startswith('file:') and node.get('type') in {'decision', 'plan', 'source', 'api', 'ui', 'test'}]
    selected = []
    # Keep independent repository layers represented before filling by lexical relevance.
    for kinds in ({'decision'}, {'plan'}, {'source'}, {'ui'}, {'test'}):
        for _, node in scored:
            if node['type'] in kinds and node not in selected:
                selected.append(node)
                break
    for _, node in scored:
        if len(selected) >= limit:
            break
        if node not in selected:
            selected.append(node)
    api_candidates = [n for n in graph['nodes'] if n['type'] == 'api' and any(t in n['label'].lower() for t in terms)]
    if api_candidates:
        selected = selected[:limit-1] + api_candidates[:1]
    layers = neighbors(graph, {n['id'] for n in selected}, depth=2)
    return {'kind': 'context', 'task': query, 'nodes': selected, 'selection_origin': 'lexical-candidate',
            'direct': layers[0][:20], 'indirect': layers[1][:20],
            'constraints': ['Open cited source and confirm the actual call path before editing.',
                            'Graph relationships never expand user authorization.',
                            'Imports and test references do not establish behavior or coverage.',
                            'Semantic implements/renders/contradicts claims remain unestablished.'],
            'verify': ['Review the repository command map, then run targeted and project checks.',
                       'Record missing runtime/browser/model prerequisites as blocked.']}


def explain(graph, target):
    nodes = select(graph, target)
    if not nodes:
        raise ValueError(f'No indexed node matches {target!r}.')
    ids = {n['id'] for n in nodes}
    return {'kind': 'explain', 'nodes': nodes, 'edges': [e for e in graph['edges'] if e['source'] in ids or e['target'] in ids],
            'semantic_status': 'not-established', 'limitations': ['Inspect actual cited sources; structural relationships do not prove a product decision.']}
