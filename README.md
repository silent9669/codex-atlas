# Codex Atlas

Codex Atlas turns a repository into a bounded, evidence-aware context and verification graph for Codex. It connects decisions, plans, source, APIs, UI, tests, evaluations, replay artifacts, commits, and runtime checks without presenting guesses as facts.

The first release is a local Python CLI bundled as a portable Codex plugin. It has deterministic Markdown, Python `ast`, TypeScript compiler-AST, and Git extraction; focused context, impact and explanation reports; reviewed command-map verification; stale evidence and drift reporting; and an accessible static HTML report.

## Install in Codex CLI

The repository includes a marketplace entry. After publishing or cloning it:

```bash
codex plugin marketplace add silent9669/codex-atlas --ref main
codex plugin add codex-atlas@codex-atlas
```

Start a new Codex session after installation and invoke the bundled skill with `Use $atlas to inspect the impact of this change.`

Requirements: Python 3.11+, Node 20+, and npm. The skill runs `atlas setup` once after install/update to install the pinned TypeScript compiler with lifecycle scripts disabled. Marketplace installation alone does not run npm. Without setup, Python/Markdown/Git still work and TS extraction is explicitly **blocked**, never silently presented as complete.

## Run locally

```bash
python3 skills/atlas/scripts/atlas setup
python3 skills/atlas/scripts/atlas --repo /path/to/repo index
python3 skills/atlas/scripts/atlas --repo /path/to/repo context "add grounding citations to city chat"
python3 skills/atlas/scripts/atlas --repo /path/to/repo impact backend/app/ai/grounding.py
python3 skills/atlas/scripts/atlas --repo /path/to/repo explain docs/dev-plan/07-lop-ai.md
python3 skills/atlas/scripts/atlas --repo /path/to/repo verify --commands .atlas/commands.json
python3 skills/atlas/scripts/atlas --repo /path/to/repo drift
python3 skills/atlas/scripts/atlas --repo /path/to/repo report --output .atlas/report.html
```

`index` writes `.atlas/graph.json`. The default command is read-only apart from that local artifact. Verification executes nothing without `--run`, and command maps must contain reviewed argument vectors. Never put credentials in a command map or evidence output.

Every command refreshes the graph. Add `--json` for machine-readable reports. `verify` exits nonzero for failed, blocked, or stale execution; planning without `--run` executes nothing. Report output and reviewed command maps must remain inside the target repository.

## Scope and limits

The extractor reports unsupported dynamic imports, generated routes, parse errors, missing links, excluded paths and other diagnostics. An import proves a structural dependency only. A test import does not prove behavior coverage. Missing evidence is “not established”, not automatically a defect. Semantic relationships need Codex analysis and human review.

The implementation is independent of Graphtify and reuses no unverified upstream code or assets. The MegaDay citation integration described in the development brief is a separate authorized product change and is not performed by this repository.

## Development

```bash
npm install --ignore-scripts
npm run check
```

See [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) for the contract and [graph schema](skills/atlas/references/graph-schema.md) for evidence semantics.
