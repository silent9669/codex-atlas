# 0.2 validation record

Validation used a disposable clone of `silent9669/MegaDay_Twin` and never modified its application source. The clone was indexed at Git commit `f7fd88e151a5f544e3e6492da51184080e90aea4`.

Observed graph totals were 4,234 nodes, 5,834 relationships, 52 text documents and 10 extraction findings. The default browser view bounds the first graph screen to 26 nodes and 37 edges; the search, scope, focus and inspector expose the rest. The public repository has separate city PM `/api/pm/chat` and Python `/api/v1/ai/chat` surfaces; Atlas keeps that boundary as an observed fact and does not add an inferred integration edge.

The one-page loopback workspace was checked in Chrome at 1,440px and 390px widths. The graph, tool buttons, document drawer, topic filter, status filter, audit drawer, decision drawer, chat drawer and keyboard close behavior rendered without console messages. The mobile page had no horizontal overflow; reduced-motion emulation removed transition travel. Design Taste Frontend's app inspector reported no FAIL findings; it reported the expected dense-text warning for a graph/audit screen.

The live API path was tested with a temporary process environment key that was not written to the repository or retained after the process. The router selected `gpt-6-luna` with low effort for a bounded README lookup. The router Responses call returned 279 input tokens and 76 output tokens. The explicit child `codex exec` used the selected model and returned a valid structured completion with exit code 0; its usage was recorded in the local handoff record. The task was read-only, so no feature completion note was generated. A separate earlier advisor test also accepted a strict cited response from `gpt-6-luna`; Atlas does not claim token savings without a measured baseline.

The offline suite covers labels and stale overrides, route schema validation, malformed provider responses, same-origin/Host checks, completion-artifact requirements, idempotent project memory, documentation symlink refusal, local env-file policy, browser graph data escaping, and the CLI. `npm run check` passed all 39 tests, Python compilation, and JavaScript syntax checks. The live server was restarted after source changes and rechecked in Chrome.

Live credentials are user-provided runtime state. Rotate a key that has been pasted into chat or terminal input; Atlas itself contains no key.
