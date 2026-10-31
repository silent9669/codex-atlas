# Atlas graph schema

The graph is JSON with `schema_version`, a `snapshot`, `nodes`, `edges`, `diagnostics`, and `limitations`.

Nodes have stable IDs, `type`, repository-relative `path`, optional `symbol`, `content_hash`, and line navigation hints. Supported node types include `decision`, `plan`, `source`, `test`, `api`, `ui`, `replay`, `eval`, and `commit`.

Edges have `source`, `target`, `type`, `origin`, `confidence`, `freshness`, cited evidence, and an explanation. Imports, explicit links, route declarations, test imports, and Git history are observed. Semantic `implements`, `renders`, and `contradicts` edges are not emitted by the deterministic extractor.

Verification records separately store snapshot identity, exact argv/cwd, times, status, sanitized artifact hash, and result. Passing an old snapshot is historical evidence and must be reported stale after a relevant change.
