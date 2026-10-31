# Changelog

## 0.5.2

- Disable inherited tool access during background Codex inference while retaining the configured provider and authentication.

## 0.5.1

- Unify repository identity, navigation, Commands and Assistant in one desktop header.
- Use a compact second navigation row on narrow screens, with accessible icon controls on phones.
- Remove the duplicate overview toolbar and preserve document-scoped chat and drawer focus.

## 0.5.0

- Add a compact Overview with document categories, review queue, focused connections and latest execution.
- Add graph relationship filters, neighbor highlighting and focused views that preserve the selected file.
- Provide direct `atlas-organize`, `atlas-audit`, `atlas-docs`, `atlas-memory` and `atlas-graph` skills alongside the same app workflows.
- Support workspace URL fragments and preserve keyboard focus when closing workflow drawers.

## 0.4.2

- Improve reading with 17px text, a 700px column, larger tables and bundled Vietnamese glyphs.
- Simplify document actions and metadata; add a heading navigator that adapts to narrow screens.
- Make category navigation clearer with larger headings, visible counts, selected-document expansion and expand/collapse controls.
- Restore reader interactivity after mobile library selection.

## 0.4.1

- Compact workspace navigation into a top bar and give the document library more vertical space.
- Combine document labels and actions, tighten reader spacing, and use full-width Graph, Runs, Memory and Audit views.
- Preserve mobile Library access, keyboard focus and reduced-motion drawer behavior.

## 0.4.0

- Replace the document table with a category library and safe Markdown reader; keep chat beside the selected document.
- Add Runs and Memory views, source-bound relevant recall, directional graph evidence and live execution stages.
- Auto-load ignored repository-root `.env.local`; preserve shell precedence and saved CLI authentication.
- Validate against an isolated MegaDay_Twin clone; install the supported Codex compatibility prompt.

## 0.2.0 — 2026-10-31

- Added one live graph page with responsive document, audit, decision and chat drawers, keyboard navigation and reduced motion.
- Added the canonical `$codex-atlas` skill, optional CLI prompt, automatic workspace startup and small-model routing to separate Codex execution.
- Added automatic document labels, topic/status filters, reviewed overrides and stale-source detection.
- Added idempotent project documentation and memory updates after successful implementation runs.
- Added local document classification, Vietnamese acceptance signals, extraction-audit findings, and bounded Codex handoffs.
- Added explicit model routing, optional OpenAI Responses API discovery/advice, strict cited-path validation, local env-file loading, capped output, usage records, and refusal/secret handling.
- Added safe Codex child launching with explicit model, reasoning effort, schema, sandbox, and stale-result checks.
- Validated against the public `silent9669/MegaDay_Twin` snapshot: 4,234 nodes, 5,834 relationships, 52 documents, and 10 extraction findings.


## 0.1.0 — 2026-10-31

- Local Markdown, Python AST, TypeScript compiler AST and Git graph extraction.
- Cited context, bounded structural impact, explanation, changed-file review and JSON reports.
- Reviewed check execution with sanitized artifacts, scoped evidence links and stale snapshot detection.
- Searchable keyboard-accessible static HTML report.
- Portable Codex plugin and Git-backed marketplace installation.

This release does not implement MegaDay's separate city-chat grounding integration or establish live model quality.

## 0.3.0

- Document-first workspace with Documents/Graph navigation, optional filters, one assistant/detail panel, and concise action selection.
- Saved Codex authentication for structured chat, category and routing calls; explicit API keys retain direct Responses behavior.
- AI-created document categories, selected-document questions, docs/audit/memory commands, and reviewed-label precedence.
- Explicit completion outcomes prevent failed child checks from creating success notes or memory.
- Clean local marketplace packaging excludes runtime files and Git history.
- Local marketplace installation and live model/CLI validation; nested macOS sandbox restrictions are reported without silently falling back.
