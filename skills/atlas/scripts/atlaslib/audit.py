from collections import Counter
from . import evidence


def summarize(root, graph):
    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])
    findings = evidence.drift(root, graph).get('findings', [])
    by_type = Counter(node.get('type', 'unknown') for node in nodes)
    by_origin = Counter(edge.get('origin', 'unknown') for edge in edges)
    by_freshness = Counter(edge.get('freshness', 'unknown') for edge in edges)
    return {
        'kind': 'audit',
        'snapshot_hash': graph['snapshot']['hash'],
        'counts': {'nodes': len(nodes), 'edges': len(edges), 'diagnostics': len(graph.get('diagnostics', [])), 'findings': len(findings)},
        'node_types': dict(sorted(by_type.items())),
        'edge_origins': dict(sorted(by_origin.items())),
        'edge_freshness': dict(sorted(by_freshness.items())),
        'findings': findings,
        'limits': [
            'Structural relationships do not prove product behavior or test coverage.',
            'Semantic implementations, contradictions, and document ownership remain needs-review until confirmed.',
            'A green command result is scoped to its recorded snapshot, command map, runtime, and claim IDs.',
        ],
    }
