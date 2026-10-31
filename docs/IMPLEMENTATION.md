# Implementation contract

Version 0.1 implements the three CLI slices from the development brief: extraction, context/impact, and verification/drift. A static searchable graph report provides the first browser flow. Python 3.11+ and Node 20+ are required. Python extraction uses `ast`; TypeScript extraction uses the pinned TypeScript compiler AST after `atlas setup`. Missing dependencies are blocked diagnostics, not a silent regex fallback. All analysis is local.

Success criteria:

1. Deterministic, versioned graph with stable path/symbol IDs and content hashes; decisions, plans, source, tests, APIs, UI and Git history.
2. Every relationship records origin, confidence, evidence and explanation. Semantic candidates remain inferred. Imports do not prove behavior or coverage.
3. Bounded cited context and direct/indirect impact, with unresolved extraction reported explicitly.
4. Verification is planned by default, executes only an explicitly supplied reviewed argument-vector mapping with `--run`, and retains passed/failed/blocked results, sanitized artifacts and snapshot hashes. Any snapshot change makes a run historical.
5. Drift reports broken explicit links, unresolved imports and stale evidence without calling missing evidence a defect.
6. Unit and CLI integration tests use disposable repositories. A deliberate missing-link and stale-evidence exercise must be detected. Browser QA covers search, selection, keyboard access and responsive layout.
7. A portable plugin manifest, repository marketplace and bundled Atlas skill install through the actual Codex CLI.

The separate MegaDay citation integration, live model evaluations, comparison experiments and human patch acceptance remain outside this plugin implementation. The original brief does not authorize modifying or deploying the target application. Do not describe those demonstration goals as completed.

No Graphtify code or assets are reused. The graph concept is inspiration only; no comparison of unverified upstream capabilities is asserted.
