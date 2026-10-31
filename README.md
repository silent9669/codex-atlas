# Codex Atlas

A local Codex plugin for connecting documents, decisions, implementation and verification in one live repository graph. Invoke an Atlas task to open the workspace, auto-label documents, ask a small decision model to select a compatible execution model, and launch the task in a separate Codex invocation.

## Install

Requires Python 3.11+, Node 20+, npm and the Codex CLI.

```sh
codex plugin marketplace add silent9669/codex-atlas --ref main
codex plugin add codex-atlas@codex-atlas
```

Start a new Codex session and use:

```text
$codex-atlas Explain the boundary between the city chat and Python grounding API
$codex-atlas Implement the requested feature and run its relevant checks
```

The skill runs dependency setup once (`atlas setup`, using `npm ci --ignore-scripts`). It automatically opens a live loopback graph with **Docs**, **Audit**, **Decide**, and **Ask Atlas** drawers. The graph refreshes every seven seconds while visible. Documents get inferred type, topics and status labels without being moved or rewritten. You can edit labels; reviewed overrides show as stale after their source changes.

Native Codex uses `$codex-atlas` or `/skills`. For the optional CLI prompt menu, copy `prompts/codex-atlas.md` to `~/.codex/prompts/codex-atlas.md`, restart Codex, then use:

```text
/prompts:codex-atlas TASK="Inspect the chat API boundary" RUN=false
/prompts:codex-atlas TASK="Implement the requested feature" RUN=true ALLOW_EDITS=true
```

Literal `/codex-atlas` is supported inside **Atlas chat**. Codex does not expose arbitrary root slash commands for plugins. A child run receives an explicit model; this does not change the parent session's model.

## Local API key

Provide `OPENAI_API_KEY` in the shell that starts Atlas, or in an untracked, Git-ignored `.env.local` passed with `--env-file .env.local`. Keys stay in local processes, never browser HTML, prompts, argv, graph data or public commits. Environment variables take precedence. Restart the local server after changing shell credentials; an explicit env file is read on each request.

The router defaults to `gpt-6-luna` and chooses from `gpt-6-luna`, `gpt-6.1-sol`, and `gpt-6-astra`, intersected with the installed Codex model catalog when available. Override with `ATLAS_ROUTER_MODEL` and ordered `ATLAS_EXECUTION_MODELS`, or supply `--model` for an explicit execution choice. API availability still depends on your account. Failed live routing blocks execution. Offline routing is explicitly labeled deterministic.

## CLI

From this checkout:

```sh
python3 skills/atlas/scripts/atlas setup
python3 skills/atlas/scripts/atlas --repo /path/to/repo dispatch "Inspect the chat boundary" --open --env-file .env.local
python3 skills/atlas/scripts/atlas --repo /path/to/repo dispatch "Implement the requested feature" --open --run --allow-edits --env-file .env.local
python3 skills/atlas/scripts/atlas --repo /path/to/repo start --open
python3 skills/atlas/scripts/atlas --repo /path/to/repo documents
python3 skills/atlas/scripts/atlas --repo /path/to/repo label docs/decision.md --topics api,verification --status needs-review
python3 skills/atlas/scripts/atlas --repo /path/to/repo audit
python3 skills/atlas/scripts/atlas --repo /path/to/repo context "change the chat API"
python3 skills/atlas/scripts/atlas --repo /path/to/repo impact backend/app/api/ai.py
python3 skills/atlas/scripts/atlas --repo /path/to/repo verify --commands .atlas/commands.json --run
python3 skills/atlas/scripts/atlas --repo /path/to/repo report
```

`dispatch` previews by default; `--run` starts a read-only child, and `--allow-edits` selects workspace-write. The skill starts execution for an invoked task and uses the user's actual authorization to choose write access. Live routing is one request capped at 900 output tokens. Chat advice uses a separate cited Responses request with bounded snippets. Child Codex usage includes its system instructions, tools and subsequent turns: total tokens are not capped by the router. Atlas records actual usage without claiming unmeasured savings.

Successful implementation runs automatically write a generated update under `docs/atlas/updates/` and append project-local `.atlas/memory.md`. Repeated finalization of the same result is idempotent. Questions, failed children, missing completion artifacts and blocked results produce no feature completion note. No global Codex memory or hooks are changed. Child-reported checks remain distinct from reviewed command-map verification.

Every analysis command refreshes source state; add `--json` for machine-readable output. All source artifacts live under `.atlas/` except the generated documentation update. Keep `.atlas/` and env files ignored. The exported HTML is self-contained and offline; live chat talks only to the loopback server, which holds the API key. Do not publish the live workspace HTML containing its local session capability.

## Evidence and scope

Markdown links, Python AST, TypeScript compiler AST, and Git history establish structural relationships. They do not prove runtime integration, behavior coverage, deployment or business correctness. Missing or stale evidence is reported explicitly. Unsupported dynamic imports, oversized sources and absent generated assets remain extraction findings. Without dependency setup, TypeScript extraction is blocked.

The real-repository validation uses a disposable clone of `silent9669/MegaDay_Twin`; Atlas does not modify that application's code or conflate `/api/pm/chat` with Python `/api/v1/ai/chat`. See [validation evidence](docs/VALIDATION-0.2.md), [command behavior](docs/CODEX-ATLAS-COMMAND.md), and [graph schema](skills/atlas/references/graph-schema.md).

## Development

```sh
npm ci --ignore-scripts
npm run check
```

D3 and IBM Plex Sans are bundled with their licenses. No frontend framework or remote CDN is required.
