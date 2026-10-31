> Tested CLI: 0.166.0. Use `$codex-atlas <task>` or `/presets`, then **1** (the installed Atlas preset). This CLI rejects legacy `/prompts:codex-atlas`; examples of that syntax below apply only to older compatible clients. Literal `/codex-atlas` remains the Atlas browser command.

# Atlas task invocation

Use `$codex-atlas <task>` in Codex. The skill automatically opens the live graph, labels documents, calls the small decision router, and launches the selected execution model for the user's authorized task. Questions use a read-only child; implementation requests may use workspace-write. `RUN=false` previews without executing.

The optional prompt template can be copied from `prompts/codex-atlas.md` into the user's Codex prompts directory:

```text
/prompts:codex-atlas TASK="Inspect the city chat and Python grounding boundary" RUN=false
/prompts:codex-atlas TASK="Implement the requested feature" RUN=true ALLOW_EDITS=true ENV_FILE=.env.local
```

Inside the Atlas chat, use:

```text
/codex-atlas TASK="Inspect the chat boundary"
/codex-atlas TASK="Implement the requested feature" RUN=true ALLOW_EDITS=true
```

Atlas chat defaults to preview and parses arguments as data, never shell code. Native Codex does not register an arbitrary root `/codex-atlas` plugin command. Its skill and prompt extension mechanisms are documented at [Skills](https://developers.openai.com/codex/skills) and [Custom prompts](https://developers.openai.com/codex/custom-prompts).

`dispatch` starts/reuses a detached loopback server and returns its URL before preparing a chosen-model handoff. Its CLI defaults to preview; pass `--run` and optionally `--allow-edits` for an explicit child invocation. `--offline` selects deterministic routing without an API call. No live router failure silently falls back to execution. A model override does not override the user's authorization.

The decision model selects from the configured candidate pool filtered by the installed Codex catalog when available. This catalog is compatibility evidence, not proof of API quota or access. The child uses `codex exec --model`, a schema, sandbox and explicit effort, documented in [Non-interactive mode](https://developers.openai.com/codex/noninteractive). With a local API key, a per-invocation provider targets the fixed official OpenAI endpoint. Global provider configuration is preserved.

After a successful implementation child returns a valid completed outcome, nonempty checks, and no blocked prerequisites, Atlas records a generated note under `docs/atlas/updates/` plus `.atlas/memory.md`. The note identifies files changed since task start and the tested source snapshot. It does not upgrade model-reported checks to verified command evidence. Repeated finalization of the same result does not duplicate records. Passive questions do not create implementation notes. Automatic completion applies to Atlas-launched tasks; it is not a global hook for arbitrary Codex sessions.

The workspace opens Overview; Documents provides a category library and Markdown reader. Graph, Runs, Memory and Audit have separate views; the Assistant opens alongside the current document. It polls the source every seven seconds. The browser makes same-origin requests to the local server; only that server calls the model API. Atlas uses saved Codex CLI authentication by default. An explicit `OPENAI_API_KEY` in the process environment or an ignored repository-root `.env.local` (auto-loaded), or explicit `--env-file`, selects direct Responses calls. There is no browser key field.

## Named operations

`atlas command '<message>' --open` and Atlas chat share the same parser. Supported messages:

- `/codex-atlas organize RUN=true`: one bounded AI request categorizes up to 40 pending documents, preserving reviewed labels.
- `/codex-atlas docs TASK="..." RUN=true ALLOW_EDITS=true`: routes a docs-writing task to a separate Codex execution; source inspection precedes writing.
- `/codex-atlas audit TASK="..." RUN=true`: routes a read-only source/document audit; citations and missing checks are part of the task.
- `/codex-atlas memory RUN=true`: records the latest successful implementation, or reports that its completion was already recorded. Changed unrecorded snapshots are blocked.

Omitting RUN previews the operation. Docs and audit still use the small routing model before a separate execution model. Organize uses only the small model, and memory is local. The browser action selector builds these commands; Run & edit files explicitly authorizes writes. Raw slash commands remain supported. Native Codex uses the packaged `$codex-atlas` skill or optional `/prompts:codex-atlas` compatibility prompt; literal `/codex-atlas` is the Atlas chat syntax.

## Direct CLI skills

The plugin also installs `$atlas-organize`, `$atlas-audit`, `$atlas-docs`, `$atlas-memory`, and `$atlas-graph`. Select them with `/skills` or `$` completion after reloading Codex. The app’s Commands dialog lists the equivalent workflows and offers copyable skill names. Audit remains read-only; docs-writing follows the requested scope; memory recovery requires an eligible successful implementation record.
