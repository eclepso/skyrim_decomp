# Contributor drafting card

Use `./sr` (Windows: `.\sr.cmd`) in your own clone: `go --drafted-by "<person>, assisted by
<model>"`, edit the two source files it creates, `compare`, then `submit --dry-run` and `submit`.
Open a PR that touches only `reconstruction/**`; checks run; the bot reviews and merges.

Batch several functions in a PR when you can; any classes are fine; a first PR or a single large
function alone is fine.

Read only the private pack named by the helper, after the owner has agreed to model exposure.
Never post listings, pseudo-C, Ghidra projects, bytes, objects, raw diagnostics or paths. Keep the
skeleton's provenance and licence fields; name your actual model. Fill the `Code origin:`
placeholder truthfully in each file, including adaptations and sources. Community headers are
hypotheses, not binary proof. Never write `asm`, `##`, `#pragma` (except `once`), byte arrays or
`\x` strings, and never edit verifier inputs, tools, flags or another unit to force a pass.

For FNV reuse use `SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence)` and cite each reused
body in a `Sibling source: momusdigital/fnv_decomp@91e1b6e8 <path>:<line>` header line. Another
game proves no Skyrim offset, layout or behavior. Follow LEGAL.md and PROVENANCE.md.

Source rules:
- A label line is `// <names>: <LABEL>`; LABEL is `COMMUNITY(<owner>/<repo>@<rev>, <licence>)`,
  `GUESS(low)`, `EXE_RTTI`, `OBSERVED`, or `STANDIN` plus one of those. One label per line.
- Includes: own header `#include "X.h"`; shared headers by reconstruction-root path such as
  `"area/Y.h"`. Parent steps and host paths are refused.
- Declare, do not define, a function the target calls; `compare` binds the call.
- Write assignments in the order the listing stores them; keep a repeated null test as a repeat read.
- `static_assert` needs a message.
- A tail jump (`JMP <function>`) is `return Callee(...);` as the last statement.

Diagnostics: read `functions[].reason`, sizes, `first_mismatch` and `hint` from `compare`. An
unbound symbol needs the helper's bind hint, using an RVA from your own pack. A compile or include
failure is not comparison evidence. Under `cheap`, stop after 3 attempts without an improvement in
matching bytes (hard cap 6 comparisons); under `full`, 4 and 10. Keep the source and the sanitized
reason when you stop.

A local PASS is a candidate, not acceptance: the project confirms on two hosts and one review
approves the source before a function counts as `matched`. Ask once before reading listings or
pseudo-C; see [the guide](contributing-agent.md).
