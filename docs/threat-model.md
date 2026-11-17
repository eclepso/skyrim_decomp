# Threat model

Defences answer a plausible threat or they are removed. Defences aim at fairness, not
punishment; no one is banned for being active.

## Plausible threats and their controls

| Threat | Control |
|---|---|
| Game-derived text (disassembly, decompiler names, byte runs, inline assembly) published in a PR | `tools/leakgrep.py` over added lines only, blocking, rule codes and line numbers only; the single review also reports `leak: yes/no` and cannot override a grep hit; squash merge with a bot-written message, so contributor history and commit messages are never published |
| A false byte match (the claim that matters most) | Byte match on two independent hosts: the GitHub Windows CI-hash job and the Mac Wine or PC comparator against the real binary; neither host trusts the PR's own tools |
| A PR edits `.github/` or `tools/` to fake host 1, or edits anything outside the function source | `scope` job and the bot's own path check: only `reconstruction/**` merges automatically; tooling changes take the normal reviewed route |
| A push after review swaps the content | Merge with `--match-head-commit`: a changed head fails the merge and the bot starts over |
| A shared header edit silently breaks matched functions elsewhere | CI recompiles matched functions whose include closure contains a changed header; a regression blocks |
| Provenance: unlicensed code, pasted decompiler output, byte steering | The one review (blocking grounds in `docs/verification.md`), `Origin` and label lint, family template plus sample review |
| Untrusted C++ makes the verifier host leak host files via `#include` or diagnostics | Include allowlist (repository-relative paths and standard headers) in `leakgrep.py`; compiler diagnostics are never published |
| PR text instructs the reviewing model | The review treats PR text as untrusted; it can block but never override the byte match |
| Fork CI abuse | Workflows hold no secrets and a read-only token; the bot approves pending fork runs |

## Controls removed

These existed to answer threats that the controls above already answer, and no plausible threat
justified them:

- Reviewing only after a multi-stage leak screen (a deterministic grep plus the review replaces
  it).
- Per-function CI confirmation dispatch, frozen intake trees and per-commit history screening
  (replaced by exact-head merge and bot-written squash messages).
- The sampling second review, review groups and from-scratch reruns (Terra calibration showed
  0 missed rejects in 67; the byte match does not depend on them).
- The global lane with its lock, full-repo rebuild and wait for green main, one in-flight PR per
  author, round-robin intake, strike counts and daily caps (they answered load and ordering, not a
  threat to the published record).
- Claims and queues as gates (an open draft PR is the claim, advisory only).

## Later

- Sandboxed build user for outside PRs.
- Similarity check against public sources.
