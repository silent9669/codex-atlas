# Atlas workspace, version 0.5

Overview opens with four workflow actions, the eight largest document categories (four on phones), three review candidates, four connected documents and the latest execution. Counts come from the current repository snapshot. Categories open the matching library; review paths open their document and Investigate prepares a scoped read-only audit. Full categories and findings remain in Documents and Audit. The overview fits its key content at 1440×900 without reducing reader typography.

Documents opens a searchable library beside a Markdown reader. Categories group notes without moving files. The selected document stays visible while using the Assistant. Graph, Runs, Memory and Audit have separate working surfaces. Workspace URL fragments reopen the chosen surface.

A 64px header groups repository identity, plain navigation tabs, Commands and Assistant. Below 1100px it becomes two rows totaling 104px; phone controls retain accessible names while showing icons. The overview has no duplicate repository toolbar. The 300px navigator (260px on tablets) contains repository identity, categories, search and the library. A 48px page toolbar identifies the selected file; Ask document stays in the header and keeps its selected-document context. Category/type/topic/status filters share one disclosure; document metadata and editing actions sit under Details. Categories start collapsed except for the selected document; search opens matching groups. Overview, Graph, Runs, Memory and Audit use the full workspace width. A 380px Assistant or graph inspector shares the screen above 1200px, overlays on tablets, and fills the working area on phones. At widths up to 850px, the library becomes a drawer and navigation scrolls horizontally. Phones open the library with a visible Library button. Type, topic and status filters sit behind Filters. No essential action requires hover or dragging.

IBM Plex Sans with Latin and Vietnamese glyph subsets, a pale green-grey frame, thin rules and flat surfaces retain the existing identity. Motion uses short drawer entrances and dialog fades, disabled by reduced-motion preferences. Animate UI and shadcn composition guidance informs these native controls; standalone HTML, Python and bundled D3 remain the existing stack.

## Reference projects

- [obsidian-mind](https://github.com/breferrari/obsidian-mind), reviewed at `fae7be467fc5e23bf9d51df7207d41f0c07e2754`: linked Markdown notes, durable recall and bounded context. Atlas adopts a library/reader, source-linked connections and searchable project memory.
- [building-with-decision-models](https://github.com/aaddrick/building-with-decision-models), reviewed at `aa9e881ae8fd30fc50cc2387df97c23df2c23176`: a reference/skill library, not a UI app. Atlas keeps the small routing decision separate from execution and records observed checks rather than treating confidence as completion.
- [Graphify](https://github.com/Graphify-Labs/graphify), reviewed at `a0946f962af31b19bff941b453f6dae9a7077c7a`: graph exploration, communities and explained relationships. This is the likely project intended by “Graphtify”; the user did not confirm an exact third URL. Atlas uses existing AST/import/Markdown evidence, directional edges, category groups and focused neighborhoods. No Graphify runtime or hooks are installed, and no token-saving claim is made.

## Reading and graph exploration

The reader uses a 700px maximum column, 17px body text and 15px tables. A heading navigator sits beside the article on wide screens and under Contents alongside document actions on narrower screens. It moves keyboard focus to the selected heading and respects reduced motion.

The Markdown reader supports headings, lists, tables, code fences, blockquotes, emphasis and document links. It builds DOM nodes with text content; raw HTML and remote images do not execute or load. It is a bounded preview, not a full CommonMark editor. Source excerpts are redacted and capped at 16,000 characters.

The graph groups files into Documents, Implementation and Verification, or into AI document categories. Edges expose direction, source paths and extraction explanation. Focus, pan, zoom and fit are keyboard accessible. Phones/tablets default to an equivalent grouped list. Graph counts explicitly label bounded subsets. The relationship filter limits both edges and connected nodes, and hover/keyboard focus emphasizes neighbors. Focused neighborhoods retain the selected file and cap the view at 14 nodes. Relationship evidence is not a coverage or implementation claim.

AI organization assigns project-specific categories to up to 40 pending documents per request. Type/topics/status also have deterministic labels. Categories are metadata; human overrides win and source changes make labels stale. Selected documents are prioritized in the assistant's bounded context.

## Execution and memory

The Assistant offers Ask, Implement, Write docs, Audit, Organize and Save memory. Editing actions use **Run & edit files**; Ask/Audit remain read-only. Commands are available through the command dialog and literal `/codex-atlas` chat messages. The dialog also exposes five installed CLI skills: `$atlas-organize`, `$atlas-audit`, `$atlas-docs`, `$atlas-memory` and `$atlas-graph`. They share the launcher workflows; Codex CLI discovers them through `$` or `/skills`, not arbitrary root slash commands. During browser runs, activity reports reading, routing, execution and finalization stages.

Runs shows the selected models, outcome, reported checks and generated work record. Memory shows completed project records with current/stale/unknown freshness. Bounded lexical recall includes only relevant records whose source hashes still match. Generated Atlas update files are excluded from freshness identity. Memory is project-local, not global Codex memory; records and repository text remain untrusted context.

Atlas automatically reads an untracked, Git-ignored repository-root `.env.local`, or an explicitly selected `--env-file`; shell variables win. Without a key it uses configured Codex CLI authentication. With `OPENAI_API_KEY`, inference uses the official Responses endpoint. Credentials never enter browser HTML. CLI inference runs with an empty temporary working directory, read-only sandbox, schema and 120-second timeout; it inherits configured tools and is not an isolated API endpoint or total-token cap.

The router launches a separate `codex exec`. An implementation child updates affected owning docs and runs checks. Only completed outcomes with reported checks and no blocked prerequisites create an update and memory record. Child-reported checks remain distinct from reviewed command-map verification. Repeating memory recovery is idempotent. An enclosing sandbox can block nested Codex or localhost; Atlas reports this without weakening it.

## Validation

See [0.5 validation](VALIDATION-0.5.md) for the current UI, Open Design and skill checks, and [0.4 validation](VALIDATION-0.4.md) for real MegaDay repository results. [0.3 validation](VALIDATION-0.3.md) records the preceding installed-plugin and disposable implementation checks.

## Open Design review

The local Open Design MCP generated an isolated prototype and design notes in project `atlas-workspace-implementation-be4c`, run `f0fc54fb-43c5-42f0-88f2-39f89f720fff`. Adopted guidance: categories beside compact review rows, connections and latest run on a second row, findings reduced to title/path/status/action, 44px category targets, a two-by-two mobile action grid, consistent outlined icons, and shared app/CLI workflow names. The existing top navigation and bundled D3/Python stack are retained. The prototype uses sample data; Atlas uses the real indexed repository and existing execution/memory contracts.
