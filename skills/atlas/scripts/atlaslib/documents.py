import re
from collections import Counter
from .graph import SECRET


def classify(path, text):
    lower = path.lower()
    if '/prompts/' in '/' + lower or lower.startswith('prompts/'):
        return 'prompt'
    if any(part in lower for part in ('quyet-dinh', 'decision', 'adr')):
        return 'decision'
    if any(part in lower for part in ('dev-plan', 'plan', 'roadmap', 'spec')):
        return 'plan'
    if any(part in lower for part in ('runbook', 'deploy', 'release', 'operations')):
        return 'runbook'
    if any(part in lower for part in ('api', 'reference', 'schema')):
        return 'reference'
    if path.lower().endswith('readme.md'):
        return 'overview'
    if re.search(r'(?im)^#{1,2}\s+(decision|status|acceptance|requirement|runbook)', text):
        return 'working-doc'
    return 'document'


def inspect(root, graph):
    docs = []
    by_path = {node['path']: node for node in graph['nodes'] if node.get('symbol') is None}
    for path, content_hash in graph['snapshot']['files'].items():
        if not path.lower().endswith(('.md', '.mdx', '.txt')) or not path in by_path:
            continue
        if SECRET.search(path) or (root / path).is_symlink():
            continue
        text = (root / path).read_text(encoding='utf-8', errors='replace')
        headings = []
        links = []
        for line_no, line in enumerate(text.splitlines(), 1):
            match = re.match(r'^#{1,6}\s+(.+?)\s*#*\s*$', line)
            if match:
                headings.append({'title': match.group(1).strip(), 'line': line_no})
            links.extend({'target': m.group(1), 'line': line_no} for m in re.finditer(r'\[[^]]+\]\(([^)]+)\)', line))
        docs.append({'path': path, 'type': classify(path, text), 'headings': headings, 'links': links,
                     'content_hash': content_hash, 'line_count': len(text.splitlines()),
                     'signals': {'has_title': bool(headings), 'has_acceptance': bool(re.search(r'(?i)acceptance|done when|success criteria|cách kiểm|kiểm thử|tiêu chí|nghiệm thu|điều kiện đạt|test:', text)),
                                 'has_owner': bool(re.search(r'(?i)owner|maintainer|responsible|phụ trách|người chịu trách nhiệm', text)),
                                 'has_status': bool(re.search(r'(?i)status|draft|proposed|approved|deprecated|trạng thái|đề xuất|đã duyệt', text))}})
    types = Counter(doc['type'] for doc in docs)
    from .labels import apply
    apply(root, docs)
    missing_title = [doc['path'] for doc in docs if doc['type'] != 'prompt' and not doc['signals']['has_title']]
    missing_acceptance = [doc['path'] for doc in docs if doc['type'] in {'decision', 'plan'} and not doc['signals']['has_acceptance']]
    return {'kind': 'documents', 'snapshot_hash': graph['snapshot']['hash'], 'documents': docs,
            'summary': {'count': len(docs), 'by_type': dict(sorted(types.items())), 'missing_title': missing_title,
                        'decision_or_plan_without_acceptance': missing_acceptance},
            'policy': ['Classification is a review aid, not an authorization to move or rewrite files.',
                       'Use explicit human confirmation before renaming, moving, deleting, or merging documents.',
                       'Broken links and conflicting status signals stay needs-review.']}
