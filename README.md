# Codex Atlas

A local Codex plugin for connecting documents, decisions, implementation and verification in one live repository graph. Invoke an Atlas task to open the workspace, auto-label documents, ask a small decision model to select a compatible execution model, and launch the task in a separate Codex invocation.

## Install

Requires Python 3.11+, Node 20+, npm and the Codex CLI.

```sh
codex plugin marketplace add silent9669/codex-atlas --ref main
codex plugin add codex-atlas@codex-atlas
```

To install an edited local checkout instead:

```sh
python3 scripts/package_plugin.py
codex plugin marketplace remove codex-atlas  # only if this name is already registered
codex plugin marketplace add /absolute/path/to/Codex-Atlas/.atlas/plugin-marketplace
codex plugin add codex-atlas@codex-atlas
```

The package includes only source and assets. It excludes `.git`, `.atlas`, environment files, dependency caches and test artifacts. Rebuild and reinstall after editing the plugin.

Atlas needs localhost binding and model network access. A network-disabled Codex sandbox blocks these operations. On macOS, even a network-enabled enclosing sandbox can prevent a nested Codex process from initializing. Start Atlas from your terminal outside that enclosing sandbox; Atlas still gives its implementation child workspace-write and analysis child read-only permissions. Inference can alternatively use an explicit API key. Atlas does not automatically weaken a caller’s sandbox.

Start a new Codex session and use:

```text
$codex-atlas Explain the boundary between the city chat and Python grounding API
$codex-atlas Implement the requested feature and run its relevant checks
```

The skill runs dependency setup once (`atlas setup`, using `npm ci --ignore-scripts`). It opens a live loopback workspace with **Knowledge**, **Graph**, **Runs**, **Memory** and **Audit**. Knowledge places a searchable category library beside a Markdown reader; the Assistant opens alongside the selected document. The graph refreshes every seven seconds while visible. Documents get inferred type, topics and status labels without being moved or rewritten. Select a document to read its preview and ask about it. You can edit labels; reviewed overrides show as stale after their source changes. The graph groups documents, implementation, and verification; a keyboard-accessible list is the default on phones and tablets.

Native Codex uses `$codex-atlas` or `/skills`. On Codex 0.166.0, open `/presets` and choose the installed Atlas slot **1** to open this repository's workspace. Save the preset once through `/presets` on a new installation. This version rejects `/prompts:codex-atlas`; the bundled `prompts/codex-atlas.md` is for older clients that still support custom prompts.

Literal `/codex-atlas` is supported inside **Atlas chat**. Codex does not expose arbitrary root slash commands for plugins. A child run receives an explicit model; this does not change the parent session's model.

## Commands and categories

Open **Commands** (⌘K / Ctrl+K) or use Atlas chat:

```text
/codex-atlas organize RUN=true
/codex-atlas docs TASK="Update the API guide from current source" RUN=true ALLOW_EDITS=true
/codex-atlas audit TASK="Compare the API guide with implementation and checks" RUN=true
/codex-atlas memory RUN=true
```

The picker selects an assistant action. **Ask** and **Run audit** are read-only; **Run & edit files** authorizes implementation or docs edits. The browser builds the command flags for you. Without `RUN=true`, commands preview. Docs writing also requires `ALLOW_EDITS=true`. Audit stays read-only. Memory uses a successful implementation record and does not duplicate an already recorded completion.

**Organize with AI** creates project-specific category names using the configured small router model, at most 40 documents per request. Re-run for remaining documents. Categories are metadata; no source files move. Human-reviewed assignments win, and category assignments become stale when their document changes. Type, topics, status, and category provenance remain separate. If neither configured Codex authentication nor an explicit API key works, the result is blocked.

From the CLI, use the same command parser:

```sh
python3 skills/atlas/scripts/atlas command '/codex-atlas organize RUN=true' --open
python3 skills/atlas/scripts/atlas organize --json
```

## Authentication

By default, Atlas reuses your authenticated Codex CLI for chat, categories, routing, and implementation. Run `codex login status` to check your setup. Atlas never reads the saved credential file. Inference runs in an empty temporary directory with a read-only sandbox and a structured-output schema.

To use the Responses API directly for chat, categories and routing, provide `OPENAI_API_KEY` in the shell that starts Atlas, or in an untracked, Git-ignored repository-root `.env.local` (loaded automatically). Use `--env-file` to select another ignored file. Keys stay in local processes, never browser HTML, prompts, argv, graph data or public commits. Environment variables take precedence. Restart the local server after changing shell credentials; the local env file is read on each request.

The router defaults to `gpt-6-luna` and chooses from `gpt-6-luna`, `gpt-6.1-sol`, and `gpt-6-astra`, intersected with the installed Codex model catalog when available. Override with `ATLAS_ROUTER_MODEL` and ordered `ATLAS_EXECUTION_MODELS`, or supply `--model` for an explicit execution choice. API availability still depends on your account. Failed live routing blocks execution. Offline routing is explicitly labeled deterministic.

## CLI

From this checkout:

```sh
python3 skills/atlas/scripts/atlas setup
python3 skills/atlas/scripts/atlas --repo /path/to/repo dispatch "Inspect the chat boundary" --open
python3 skills/atlas/scripts/atlas --repo /path/to/repo dispatch "Implement the requested feature" --open --run --allow-edits
python3 skills/atlas/scripts/atlas --repo /path/to/repo start --open
python3 skills/atlas/scripts/atlas --repo /path/to/repo documents
python3 skills/atlas/scripts/atlas --repo /path/to/repo label docs/decision.md --topics api,verification --status needs-review
python3 skills/atlas/scripts/atlas --repo /path/to/repo audit
python3 skills/atlas/scripts/atlas --repo /path/to/repo context "change the chat API"
python3 skills/atlas/scripts/atlas --repo /path/to/repo impact backend/app/api/ai.py
python3 skills/atlas/scripts/atlas --repo /path/to/repo verify --commands .atlas/commands.json --run
python3 skills/atlas/scripts/atlas --repo /path/to/repo report
```

`dispatch` previews by default; `--run` starts a read-only child, and `--allow-edits` selects workspace-write. The skill starts execution for an invoked task and uses the user's actual authorization to choose write access. The direct Responses router is capped at 900 output tokens. Codex-backed inference disables inherited MCP servers, plugins, hooks and execution tools while preserving the configured provider and authentication. It has a 120-second timeout and bounded source snippets, but CLI system context and turn count are not capped by that API token setting. Chat uses the same authentication choice with cited source snippets. Child Codex usage includes its system instructions, tools and subsequent turns: total tokens are not capped by the router. Atlas records actual usage without claiming unmeasured savings.

Implementation children are instructed to update existing affected docs after checking the implementation. Successful implementation runs automatically write a generated update under `docs/atlas/updates/` and append project-local `.atlas/memory.md`. Repeated finalization of the same result is idempotent. Questions, failed children, missing completion artifacts and blocked results produce no feature completion note. No global Codex memory or hooks are changed. Child-reported checks remain distinct from reviewed command-map verification.

Every analysis command refreshes source state; add `--json` for machine-readable output. All source artifacts live under `.atlas/` except the generated documentation update. Keep `.atlas/` and env files ignored. The exported HTML is self-contained and offline; live chat talks only to the loopback server, which handles model calls. Do not publish the live workspace HTML containing its local session capability.

## Evidence and scope

Markdown links, Python AST, TypeScript compiler AST, and Git history establish structural relationships. They do not prove runtime integration, behavior coverage, deployment or business correctness. Missing or stale evidence is reported explicitly. Unsupported dynamic imports, oversized sources and absent generated assets remain extraction findings. Without dependency setup, TypeScript extraction is blocked.

The real-repository validation used a disposable clone of `silent9669/MegaDay_Twin`; Atlas does not modify that application's code or conflate `/api/pm/chat` with Python `/api/v1/ai/chat`. See [0.4 validation](docs/VALIDATION-0.4.md), [0.3 validation](docs/VALIDATION-0.3.md), [earlier validation evidence](docs/VALIDATION-0.2.md), [command behavior](docs/CODEX-ATLAS-COMMAND.md), and [graph schema](skills/atlas/references/graph-schema.md).

## Development

```sh
npm ci --ignore-scripts
npm run check
```

D3 and IBM Plex Sans are bundled with their licenses. No frontend framework or remote CDN is required.

## Direct workflows (0.5)

Open Atlas with `$codex-atlas` in Codex CLI. The Overview links to document categories, review findings, focused graph connections and the latest run. The same workflows are available in the app’s Commands dialog and as installed CLI skills:

| CLI skill | Workflow |
| --- | --- |
| `$atlas-organize` | Assign AI categories without moving documents |
| `$atlas-audit` | Compare code and docs in a read-only execution |
| `$atlas-docs` | Write or update docs for the requested task |
| `$atlas-memory` | Recover records for a successful implementation |
| `$atlas-graph` | Open the live relationship graph |

Reload Codex after updating the plugin to discover new skills. In Codex 0.166.0, use `$` or `/skills`; literal `/codex-atlas` is an Atlas chat command. Memory is project-local and never marks changed sources verified.
