---
description: Open the live Atlas graph, auto-label docs, route a task to a compatible Codex model, and record implementation results.
argument-hint: TASK="<task>" [MODEL=auto] [RUN=true] [ALLOW_EDITS=false] [ENV_FILE=.env.local]
---

Use the installed `$$codex-atlas` skill for this request.

Request: $ARGUMENTS

Parse named TASK/MODEL/RUN/ALLOW_EDITS/ENV_FILE arguments when supplied; otherwise treat the request as the task. MODEL defaults to auto; RUN defaults to true. ALLOW_EDITS defaults to false unless the actual user task explicitly requests implementation. Forward ENV_FILE only when provided. Follow the skill's dispatch workflow: automatically open the live graph, label documents, call the small router, launch the chosen model for authorized execution, and let the launcher finalize successful implementation runs. RUN=false requests a preview. Show blocked prerequisites honestly. Do not run finalization twice or change global Codex memory.
