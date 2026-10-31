# 0.3 validation record

Validated locally on 2026-10-31 with Codex CLI 0.166.0. The plugin was installed as `codex-atlas@codex-atlas`, version 0.3.0, from a clean local package of the checkout. No application repository was pushed or deployed.

## Installed plugin and real models

A disposable Git repository contained a Python calculator, a README and unittest checks. A fresh Codex session explicitly invoked `$codex-atlas` and loaded the installed skill from the plugin cache.

- Saved Codex authentication completed actual structured category, selected-document Q&A and routing requests. No credential contents were read or copied by Atlas.
- The small router chose `gpt-6-luna` with low reasoning effort for the focused implementation. A separate workspace-write child added `subtract(a, b)`, positive/negative-result tests, and updated the existing README.
- Independent `python3 -m unittest -v` passed all three tests; `git diff --check` passed. The child generated a completion note and project memory.
- A deliberately incorrect claim that `subtract(2, 5)` returns positive 3 was added to the fixture README. The installed read-only audit identified the contradiction with README, implementation and test line citations. It made no source edits.
- The installed docs command corrected the example to `-3`, passed the checks, changed only README.md before generated completion artifacts, and returned the explicit completed outcome.
- Repeated memory recovery did not duplicate the completion. A further installed run with source hashes returned current twice without changing memory, then reported stale after a controlled README change. Regression checks also establish that later source changes report stale memory, and older records without freshness hashes cannot claim current state.
- An independently reviewed command map ran the three calculator tests through Atlas verification and recorded a current pass with stdout/stderr hashes.

CLI inference uses configured providers/tools and includes system context. The first full implementation reported 84,242 input tokens (65,920 cached) and 715 output tokens for its child. This is observed usage, not a token-savings claim. Direct Responses token caps do not cap a Codex CLI session.

## Sandbox boundary

A fresh session using the default workspace-write enclosing sandbox failed before execution because localhost binding was denied. Enabling networking allowed localhost, but nested Codex initialization was still denied by the macOS sandbox. Both attempts left the source unchanged and generated no success note or memory.

The complete skill test passed with a terminal-level orchestrator matching the current host session's unrestricted permissions. Atlas's execution child still used workspace-write, and the audit used read-only. Atlas never changes a caller's sandbox automatically. For a restricted enclosing session, start Atlas from a host terminal; do not interpret the successful host test as proof of nested sandbox support.

## Browser and automated checks

- `npm run check`: 54 tests passed, plus Python compilation and JavaScript syntax checks.
- The completion regression was mutation-checked: disabling the failed-outcome guard caused the test to fail; restoring the guard passed.
- Both packaged skills passed the skill validator.
- Design inspector at 1440px, 768px and 390px: 0 failures and 0 warnings. All three screenshots were reviewed.
- Chrome DevTools exercised document selection, assistant modes, selected-document Q&A and AI organization through the live server, graph/list navigation and reduced-motion mobile behavior. No console errors or warnings were observed. Mobile inspection showed no horizontal overflow, inactive underlying content and no drawer animation under reduced motion.

Local test artifacts are retained in the disposable repository's `.atlas/smoke/` folder and the checkout's ignored `.taste-skill/simplified-workspace/` folder. Model outcomes establish these fixture runs only; arbitrary repositories, provider quotas and future model behavior remain outside this validation.
