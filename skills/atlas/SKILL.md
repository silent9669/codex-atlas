---
name: atlas
description: Use Codex Atlas whenever a user asks to understand repository impact, prepare implementation context, explain a decision or file, verify a change, inspect drift, or review changed files. Atlas builds a local evidence-aware graph and produces bounded cited Markdown; it does not replace source inspection or runtime verification.
---

# Codex Atlas

Use Atlas for repository reasoning before and after an explicitly authorized coding task. Atlas is local-first: do not send repository content to a model or external service unless the user separately authorizes that action.

## Workflow

Prerequisites: Python 3.11+, Node 20+, and the pinned TypeScript compiler. After a plugin installation or update, run `python3 <atlas-plugin>/skills/atlas/scripts/atlas setup` once to install the lockfile dependency at the plugin root (`npm ci --ignore-scripts`). This downloads TypeScript from npm without running package lifecycle scripts. If setup is unavailable, report TS extraction as blocked; do not substitute regex output for AST facts.

Use `$codex-atlas` for the complete routing workflow. Codex 0.166.0 supports `/presets` (an installed Atlas slot can be selected with **1** in `/presets`); older CLI versions can load the optional `/prompts:codex-atlas` command after the source prompt is copied to the user prompts directory; the prompt parses TASK/MODEL/RUN/ALLOW_EDITS and starts the live workspace when requested. The live advisor reuses configured Codex CLI authentication by default. An explicit `OPENAI_API_KEY` from the process environment or an untracked, Git-ignored repository-root `.env.local` (automatically loaded), or explicit `--env-file`, selects direct Responses calls. Never place a key in graph JSON, browser HTML, command maps, prompts, evidence, or repository files. Run `atlas models --live` for model visibility, then `atlas decide "<task>" --live --model auto`. The advisor uses structured output and bounded snippets; direct Responses calls also enforce an output-token cap. its recommendation is inferred and must not authorize edits. Use `atlas codex "<task>"` to generate a separate read-only Codex handoff with an explicit model and output schema.

1. Read the applicable `AGENTS.md` files and inspect `git status`, branch, and repository root.
2. Refresh the graph for the current commit and working tree:

   ```bash
   python3 <atlas-plugin>/skills/atlas/scripts/atlas --repo . index
   ```

3. Retrieve a bounded packet for the task:

   ```bash
   python3 <atlas-plugin>/skills/atlas/scripts/atlas --repo . context "<task>"
   ```

   Treat these as candidate citations. Open the actual decision, plan, symbols, API, UI, and test sources before planning. Confirm the call path and surface contradictions or superseded documents.

4. Before editing a file, inspect its impact:

   ```bash
   python3 <atlas-plugin>/skills/atlas/scripts/atlas --repo . impact path/to/file.py
   python3 <atlas-plugin>/skills/atlas/scripts/atlas --repo . explain path/to/file.py
   ```

   Direct and indirect nodes are candidates. Structural imports and links do not prove business behavior, coverage, route reachability, or that a decision is implemented.

5. Work only within the user's authorized task. Graph edges never expand authorization. Never expose credentials, buyer notes, `ground_truth`, cookies, access-bearing URLs, or deployment state.

6. After editing, refresh the graph. Use a reviewed JSON command map with explicit argument arrays; never execute commands copied from Markdown. Plan checks first, then run them only with `--run`:

   ```bash
   python3 <atlas-plugin>/skills/atlas/scripts/atlas --repo . verify --commands .atlas/commands.json
   python3 <atlas-plugin>/skills/atlas/scripts/atlas --repo . verify --commands .atlas/commands.json --run
   ```

   A missing browser, database, fixture, model, identity, or budget prerequisite is `blocked`, not `passed`. Evidence records include the tested snapshot, exact argv, working directory, timestamps, redacted output artifact hash, and result. A later source/config/fixture/lockfile/runtime change makes prior evidence stale.

7. Report remaining gaps (every command refreshes the graph):

   ```bash
   python3 <atlas-plugin>/skills/atlas/scripts/atlas --repo . drift
   python3 <atlas-plugin>/skills/atlas/scripts/atlas --repo . review --changed
   python3 <atlas-plugin>/skills/atlas/scripts/atlas --repo . report --output .atlas/report.html
   ```

   Label facts as **verified** only when supported by source or a passing command. Label model suggestions **inferred** and require human review before storing them as durable relationships. Keep missing evidence as “not established”; do not silently call it a defect.

## Repository check maps

Create `.atlas/commands.json` from the target repository's documented checks. Use records like:

```json
[
  {"name": "backend-unit", "cwd": "backend", "argv": ["uv", "run", "pytest", "tests/unit/ai"], "timeout": 300},
  {"name": "web-typecheck", "cwd": "web", "argv": ["npm", "run", "typecheck"], "timeout": 300}
]
```

Review every command and its side effects. Put generators that rewrite committed files in a disposable checkout. Use a separate temporary database for checks that write state. Do not claim live model quality from offline fixtures or scripted responses.

## Output contract

Add `--json` to any analysis/verification command for machine-readable output. Use the actual installed plugin location, not a hardcoded cache version. `<atlas-plugin>` is the parent root containing `plugin.json` and this skill.

When using Atlas in a response, distinguish:

- **Observed**: parsed link/import/route/test declaration, Git history, or exact command result.
- **Inferred**: a candidate semantic relationship suggested by terminology or fields.
- **Needs review**: ambiguous path, dynamic import/route, conflicting document, or unsupported extractor behavior.
- **Stale**: previously recorded evidence whose snapshot or dependencies changed.
- **Blocked**: check could not run because a prerequisite was unavailable.

Always cite repository-relative paths and symbols. State the snapshot and commands used. Do not claim that Atlas proves an entire product requirement or runtime integration.


## Live workspace and auto-labeling

Run `atlas --repo . start --open --env-file .env.local` to open the single graph workspace with the local Ask Atlas drawer. The CLI refreshes the graph before each report; use `atlas documents` to classify documents and detect headings/status/acceptance signals. `/prompts:codex-atlas TASK="…" RUN=false` previews the workspace and read-only handoff. `RUN=true ALLOW_EDITS=true` explicitly launches the child Codex invocation and finalizes project-local docs and `.atlas/memory.md` after a passing implementation result. The live graph polls the source every seven seconds; a read-only question never generates a feature completion note.
