# Atlas 0.5 validation — 2026-10-31

## Scope

This release changes the live workspace and adds five direct CLI skills. Evaluation continues in the isolated `silent9669/MegaDay_Twin` clone at `b14ed7c2ba19b8425de5ac7c1541c52ca03b160f`, under `.atlas/evaluation/MegaDay_Twin`. Existing MegaDay worktrees are untouched. No push, merge or deployment. Prior real AI category, audit, docs, Q&A and completion results remain in [0.4 validation](VALIDATION-0.4.md); those full model workflows were not repeated for presentation changes.

## Open Design

Connected to the user-supplied Open Design 0.26.1 stdio MCP. The first run returned a plan without an artifact. A follow-up failed with an active-writer session conflict; it was stopped. A fresh project `atlas-workspace-implementation-be4c` generated `index.html`, `styles.css`, `app.js`, and `design-notes.md` through its `frontend-design` skill. Run: `f0fc54fb-43c5-42f0-88f2-39f89f720fff`. Its design notes informed the compact review rows, two-row desktop organization, consistent workflow names and mobile action grid. Prototype data is explicitly sample; it does not replace Atlas runtime behavior. No global MCP configuration was changed.

## Verification

- `npm run check`: 57 tests passed. Python compilation, JavaScript syntax checks and `git diff --check` passed.
- All five new skills passed the system skill validator using the existing isolated validator environment.
- Design inspector at 1440, 768 and 390px: 0 failures, 0 warnings. Screenshots visually reviewed in `.taste-skill/workspace-v5-installed/`. Desktop key overview sections fit at 1440×900.
- Chrome DevTools verified overview workflow selection, read-only audit context, docs edit labeling, Escape focus restoration, category navigation, mobile All categories → search → selection, reader interactivity, reduced motion, and Commands skill discovery. Additional 850/851px checks showed no page overflow or navigation collision.
- Graph relationship filtering restricted the sample view from 14 nodes / 29 edges to 6 nodes / 9 document-link edges. Focused views retain the selected file; matching nodes and edges share the filter.
- Real-repository memory recovery returned `current` and did not duplicate completion records. CLI organize preview returned `preview`; docs/audit preview routed without starting execution.
- No Chrome console errors or warnings in the checked app state.

## Boundaries

Findings are extraction/review signals, not confirmed defects. AI categories remain limited to 40 pending documents per batch. Project memory remains bound to eligible successful implementation records and current source hashes. Browser actions prepare a command; the user submits execution. Codex 0.166.0 uses `$skill-name` or `/skills`, while literal `/codex-atlas` is supported inside Atlas chat.

## Installed plugin

Codex CLI 0.166.0 reports `codex-atlas@codex-atlas` 0.5.0 installed and enabled. A fresh real TUI session showed all five `atlas-*` skills in `$atlas-` autocomplete. All 41 installed skill/code/asset files byte-match source. Installed setup completed with zero npm audit vulnerabilities. Installed extraction returned 4,304 nodes, 5,946 relationships, 54 documents and the same 10 extraction diagnostics as the source.

The installed browser workspace passed the responsive inspector at 1440/768/390px (0 failures, 0 warnings), and all three final screenshots were reviewed. Clicking README from Overview produced a focused graph retaining README among 14 nodes; hovering a test node highlighted 3 relationships and dimmed 11 unrelated nodes.

Open Design returned a valid completed HTML artifact. Its own browser check was blocked by its session policy; the parent session opened the actual prototype through Chrome DevTools, visually inspected it at 1440×900, and found no page overflow or console errors. Atlas itself received the interaction and responsive checks above. The design prototype remains separate and is not packaged as production code.

The installed Save memory browser action also returned the existing current record without writing a duplicate. The drawer labels reused completion paths as previously recorded, rather than implying a fresh update.

## Header refinement, 0.5.1

The desktop header no longer inherits the library grid's 300px offset. Repository identity, navigation tabs, Commands and Assistant share one 64px row. Below 1100px, navigation occupies a second row; all six tabs fit at the tested 390px phone width. The overview's duplicate repository toolbar is hidden; document views retain their file toolbar and document-scoped header action.

- `npm run check`: 57 tests passed; JavaScript syntax and whitespace checks passed.
- Reviewed screenshots at 1440, 768 and 390px under `.taste-skill/header-v5.1/`. Also checked 1099/1100px: no overlap or page overflow. The inspector reports a `no-title` false positive because it reads the first h1 in the hidden document toolbar; Chrome's accessibility tree and visible DOM confirm the Overview h1 is present. No other inspector findings.
- Verified mobile library placement below the toolbar, document chat scope, drawer inertness, Escape restoration, reduced motion, and the relocated Commands control.
- Installed version 0.5.1 runtime and skill files byte-match source. Repeated installed CLI `start` returned the same URL with `reused: true`. Installed CLI `/codex-atlas memory RUN=true` returned `current` and reused that same workspace.
- In the isolated MegaDay clone, a temporary `atlas-cli-sync-check.md` was indexed by the installed CLI (55 documents) and appeared through the browser's live polling without reload. Removing the exact temporary file restored 54 documents, snapshot `f867ad82be23`, and one current memory record. Existing MegaDay worktrees were untouched.

This pass changes presentation, not model routing/execution contracts. Earlier full model evaluations remain documented above and in the 0.4 validation.

## Merge review, 0.5.2

The merge review found that background Codex inference inherited tool configuration. Inference now enumerates and disables configured MCP servers, disables plugins, apps, hooks and execution tool features, and preserves the configured provider and authentication. Invalid or unavailable server enumeration blocks inference. An empty `mcp_servers` override was verified insufficient because Codex merges that table.

- `npm run check`: 59 tests passed, including new regression tests for tool isolation, malformed server metadata and enumeration failure. Python compilation, JavaScript syntax and whitespace checks passed.
- Actual Codex CLI configuration check returned zero enabled MCP servers under the inference flags.
- A real `gpt-6-luna` structured inference returned `{"status":"ready"}` through saved CLI authentication and the existing provider.
- The package-source symlink mutation failed its test as expected; original bytes were restored and the tests passed. A category freshness mutation also failed its regression test.
- All seven skill manifests passed validation. No credential-pattern matches were found in tracked or intended untracked files.
- Reopened the installed workspace against the isolated MegaDay clone: 54 documents, snapshot `f867ad82be23`, no Chrome console errors or warnings.
- Installed plugin 0.5.2; dependency setup reported zero vulnerabilities.

GitHub has no configured Actions workflows or required branch checks for this repository. Merge validation is local; the earlier full model and responsive evaluations remain documented above.
