# Atlas workspace, version 0.2

The first screen answers: which decisions, documents, source files and checks should Codex inspect next?

Use the framed-sheet direction from Design Taste Frontend: a pale green-grey frame, a white working sheet, thin rules, no shadow at rest, IBM Plex Sans for interface text, and monospace for paths and commands. Atlas's mark is a small connected constellation. The graph carries type color; chrome stays quiet.

The desktop frame contains a 204px repository navigator, a flexible graph, and a 300px inspector. Document organization, audit evidence, and model decisions open in tool drawers over the same graph; Ask Atlas is a compact chat drawer. At 320px the frame collapses into one column with a bounded graph and stacked controls. No essential operation depends on hovering or dragging.

Graph scope is deliberately bounded: start from file nodes, filter by type and query, use direct-neighborhood focus, and state the visible node/edge count and truncation. Pan/zoom/fit and keyboard node selection share the same selected state as the navigator. A list of relationships provides an accessible equivalent.

Documents are classified locally. Missing headings and acceptance text are review signals, not product defects. Audit shows origin, command result, and freshness separately. Model recommendations remain inferred. The browser never receives OpenAI credentials; the live page sends same-origin requests to the loopback server, which makes model calls. Offline exports have no API connection.

Motion uses Animate UI's plain-markup rules: quick press feedback at scale 0.97, opacity/transform entrances with ease.out (0.23, 1, 0.32, 1), a soft 350ms disclosure, and no travel under reduced motion. Frequent graph selection stays immediate. No framework migration is required for this standalone report.

Decision calls are explicit (`dispatch`, Atlas chat, or `atlas decide --live`). A local environment or explicitly named ignored env file supplies OPENAI_API_KEY. One bounded Responses API request uses a selected model and token cap, stores no server-side response, validates cited paths, and records actual usage when returned. The offline mode produces context/routing without claiming model inference.

The 0.2.0 real-repository proof used `silent9669/MegaDay_Twin` at snapshot `f7fd88e1`: the map is bounded to 26 nodes and 37 edges by default so the first viewport is legible; search and focus expand the neighborhood without making the whole repository a hairball. The public repository's city PM route `/api/pm/chat` remains visibly distinct from the Python grounded agent route; Atlas does not invent an integration edge between them.

Automatic labels combine a document kind, up to five topic labels and a status. Source declarations are inferred; manual edits are marked reviewed with a content hash. The label editor uses a native dialog, supports Escape, and never moves files. Filters work on type, topic, status and search.
