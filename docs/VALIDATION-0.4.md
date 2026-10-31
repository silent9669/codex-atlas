# Atlas 0.4 validation — 2026-10-31

## Scope and reference sources

Evaluation uses a fresh clone of https://github.com/silent9669/MegaDay_Twin at `b14ed7c2ba19b8425de5ac7c1541c52ca03b160f`, under `.atlas/evaluation/MegaDay_Twin`. Existing MegaDay worktrees were not touched. No commit, push, merge or deployment was performed.

Reference project URLs, pinned revisions and adopted ideas are recorded in [workspace design](WORKSPACE-DESIGN.md). References were read as source material, not installed as tools or hooks.

## Real model workflows

- Indexed 468 files, 4,297 nodes, 5,917 edges and 53 Markdown documents before changes. Extraction reported 10 diagnostics, not a false all-clear.
- AI category assignment completed in two real CLI-authenticated inference batches: 40 documents, then 13; remaining count 0. No fake model responses were used for this evaluation.
- A live small-model route launched a separate read-only Codex audit. It found stale root README UI/AI status and distinguished Worker Milo `/api/pm/chat` from Python `/api/v1/ai/chat`. The child ran 27 mocked deployment regression tests successfully.
- A live docs route selected `gpt-6.1-sol`; its README edit and checks succeeded, but it incorrectly placed out-of-scope checks in its blocked field. Atlas withheld finalization. The handoff instructions now clarify blockers versus limitations; the original blocked result is retained.
- A second real docs verification route selected `gpt-6-luna`, corrected two remaining README details, passed 27 regression tests and `git diff --check`, and returned completed with an empty blocked list. Atlas created `docs/atlas/updates/2026-10-31-write-or-update-project-documentation-for-this-task-inspect-impl-32480155b912.md` and `.atlas/memory.md` automatically.
- Explicit memory recovery returned `current` without another completion record. Relevant recall for “README Milo Python” returned one current record. Unit coverage checks irrelevant and stale memory exclusion.
- Reviewed command-map verification independently ran deployment regression and whitespace checks, both exit 0. Deployment tests use mocks; these results establish neither production nor full frontend/Python correctness.

Local artifacts: `.atlas/evaluation/categories-first.json`, `categories-second.json`, `audit-live.json`, `docs-live.json`, `docs-verified.json`, `verification-live.json`, `memory-recovery.json`. They are excluded from the plugin package.

## Browser and regression checks

Knowledge is now a grouped library and safe Markdown reader. Chat stays beside the document on desktop. Graph has directional evidence, bounded grouping, focused neighborhoods and a list alternative. Runs and Memory expose durable outcomes and source freshness.

Chrome DevTools inspection covered document search, reader/chat coexistence, Runs, graph/list navigation and mobile Library. The design inspection at 1440, 768 and 390px reported **0 failures, 0 warnings**, with no horizontal overflow. Desktop, tablet and mobile screenshots were visually reviewed. Artifacts are under `.taste-skill/library-v4-final/` and excluded from packaging.

`npm run check` passed all 57 tests; `git diff --check` and skill quick validation passed. Installed UI/workflow files were byte-compared against source. New regressions cover relevant/current-only memory recall, malformed stored records, prompt exclusion, automatic local env loading, shell precedence, symlink rejection and activity endpoint authentication.

## Limits

Markdown is a safe bounded preview, not a complete CommonMark renderer. AI category assignment is capped at 40 pending docs per request. Memory freshness checks the indexed source map, not production state. Checks reported by a child are labeled separately from reviewed command verification. Confidence and process exit status alone cannot finalize implementation work.

Codex CLI inference inherits configured providers/tools and has no total-token cap. No cost-saving claim is made. An enclosing macOS sandbox can block localhost binding or nested Codex initialization; the terminal-level Atlas workflow succeeds, and Atlas never silently weakens caller sandbox policy.

## Installed plugin and CLI discovery

Codex CLI 0.166.0 lists `codex-atlas@codex-atlas` 0.4.0 installed and enabled. Its installed launcher reports Atlas 0.4.0; setup installed 40 packages with zero npm audit vulnerabilities. The installed workspace runs at the local URL recorded in `.atlas/server.json`.

A real TUI test rejected `/prompts:codex-atlas`, despite older official custom-prompt documentation describing it. This version exposes `/presets`; an empty slot 1 was selected for `$codex-atlas Open the live workspace for the current repository. Do not run an implementation or modify project files.` Native skill invocation remains `$codex-atlas`. The legacy prompt was backed up and installed for older compatible clients, but is not claimed to work in 0.166.0. Official reference consulted: https://developers.openai.com/codex/custom-prompts/ (deprecated).

Real browser document Q&A returned a cited answer distinguishing Milo from Python hosting. Chrome reported no console errors/warnings. Reduced-motion emulation disabled drawer animation; mobile chat made underlying content inert and had no horizontal overflow. Memory search showed the empty state. A temporary README edit marked the real memory stale and excluded recall; restoring exact bytes made it current again.

The TUI also rejected `/1`: presets are chosen by opening `/presets` and pressing **1**, not by inventing numeric slash commands. The saved preset expanded to the Atlas skill request, discovered the installed plugin and validated the existing local workspace health. The CLI required its normal approval for localhost access/browser opening; Atlas did not change that policy. The preset text was clarified to allow Atlas metadata maintenance while prohibiting implementation and source/docs edits.

Installed CLI category refresh assigned the changed README and new generated update (2 documents, 0 remaining). Memory and Runs showed the retained passed/blocked/passed history; opening the generated work record and filtering memory were verified.

## Compact layout, 0.4.1

Moved workspace navigation and Commands into a 44px top bar, reduced the library to 272px (240px on tablets), and combined document labels/actions. Graph, Runs, Memory and Audit use full width. Reader typography stays at 15px with tighter spacing.

Chrome DevTools verified the M1 adapter document, all workspace views, desktop document/chat coexistence, mobile Library search and selection, Commands, Escape/focus restoration and reduced motion. Additional checks at 650/651px caught and fixed a navigation overlap and aligned drawer inertness with the CSS breakpoint. No console errors/warnings or page overflow remained in these checks.

The final design inspection at 1440, 768 and 390px reported 0 failures and 0 warnings; all three screenshots were visually reviewed. Artifacts: `.taste-skill/compact-final/`. `npm run check` passed 57 tests and `git diff --check` passed. This layout pass did not repeat the real model evaluations recorded above.

## Reading and navigation, 0.4.2

Reader text is now 17px with a 700px maximum measure; tables are 15px. The bundled font previously contained only the Latin subset. The Vietnamese subset is now embedded alongside it, using its published Unicode ranges; Chrome confirmed both faces loaded locally. License remains `assets/PLEX-LICENSE.txt`.

Document metadata is under Details, with one Ask document action in the file toolbar. A Contents navigator moves focus and scrolls to document headings, appearing beside the reader on wide screens and in the document toolbar at smaller widths. Categories use 14px headings, counts and a selected state; only the current category starts expanded. Search reveals matching groups. Expand/collapse and category filters were exercised in Chrome.

Verified mobile search → selection restores reader interactivity (fixed stale `inert` state), long file paths stay within the toolbar, Details remains within the viewport, Contents jumps land below the toolbar, and chat restores focus on Escape. Graph, Runs, Memory and Audit navigation still works. The design inspector at 1440/768/390px reports 0 failures and 0 warnings; all three screenshots were reviewed in `.taste-skill/readable-final/`. An additional 651px check has no horizontal overflow. The 57-test regression suite passed. This pass changes presentation/navigation, not model execution behavior.
