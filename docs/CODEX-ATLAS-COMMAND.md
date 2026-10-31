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

After a successful implementation child returns a valid completion without blocked prerequisites, Atlas records a generated note under `docs/atlas/updates/` plus `.atlas/memory.md`. The note identifies files changed since task start and the tested source snapshot. It does not upgrade model-reported checks to verified command evidence. Repeated finalization of the same result does not duplicate records. Passive questions do not create implementation notes. Automatic completion applies to Atlas-launched tasks; it is not a global hook for arbitrary Codex sessions.

The workspace is one graph page with supporting tool drawers and Ask Atlas chat. It polls the source every seven seconds. The browser makes same-origin requests to the local server; only that server calls the model API. Users provide `OPENAI_API_KEY` via the process environment or an explicit ignored local env file. There is no browser key field.
