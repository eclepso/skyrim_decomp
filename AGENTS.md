# Agent entry point

**External contributor:** follow [docs/contributing-agent.md](docs/contributing-agent.md) and
[the contributor card](docs/contributor-card.md). Use `tools/contrib.py` on your own machine.
Read the common publication and evidence rules below. Internal runners, queues and role briefs
are not prerequisites for drafting or submitting a function.

**Flow for everyone:** open a PR touching only `reconstruction/**`; checks run (scope and leak scan,
Windows CI-hash compile); the bot compares on a second host, makes one review and squash-merges.
A function is `matched` on a byte match on two hosts plus one admitted review
([docs/verification.md](docs/verification.md), [docs/threat-model.md](docs/threat-model.md)).

**Internal project worker:** also read [the internal agent workflow](docs/internal-agent-workflow.md)
before operating verifier hosts or publication. It preserves the role, gate, staged-check,
tooling-push and exact-SHA CI requirements. Its lane, queue, review-group and claims sections are
superseded and pending deletion.

Read `LEGAL.md`, `PROVENANCE.md` and `docs/clean-room.md` before research or publication.
[The full acceptance specification](docs/verification.md) remains authoritative; the contributor
card explains the local-pass boundary. Follow `docs/anti-eu-bureaucracy.md`. This repository is
independent of Mudcrab; never apply another checkout's build/cache instructions here.

## Keep private inputs private

- Use `.local/` for legally obtained executables, toolchains, databases, raw decompiler output,
  traces, saves and generated objects. Never force-add ignored paths.
- No game files, binary bytes, disassembly, dumps, proprietary symbols/SDKs, leaked code or
  unlicensed copied code in commits, PRs, issues, logs, releases or CI artifacts. Maintainer
  exceptions: names, declarations and code from the FNV decompilation `momusdigital/fnv_decomp@91e1b6e8`
  may be reused in reconstructions, labelled `SIBLING(...)`, although its LICENSE grants none
  (`docs/authorizations.md`, Notes; `LEGAL.md`). The anonymous private Fallout 4 sibling
  `fo4-private@1b765c70` is also permitted for game-code folders only, with author permission conditional on anonymity, labelled
  `SIBLING(fo4-private@1b765c70, author-permission)` (same policy references). Its middleware
  folders and mixed generated aggregates are excluded. Neither sibling is
  evidence about the Skyrim binary.
- Do not upload game-derived material to an AI/cloud service without explicit owner authorization
  and assessment of the service terms. Permission to research locally is not permission to upload.
  An external contributor may let their own coding agent read listings made locally from their own
  legally obtained copy, under their own account and their AI provider's terms; that is their
  decision and responsibility, and the contributor docs say so and ask once. Nothing game-derived
  goes into the repository, PRs, issues or CI either way (`docs/authorizations.md`, Notes).
- Analyze your own legally obtained inputs. Do not download game binaries from anyone else or
  unofficial PDBs, acquire cracks, or add copy-protection removal instructions/tools. An owner
  fetching their own purchased copy with their own account through Valve's Steam client or SteamCMD
  is fine; the project itself never distributes a game file.
- Stop the affected publication if provenance is uncertain. Record the question without reproducing
  suspect content. Unrelated original tooling work may continue.

## Be precise about evidence

- The target is pinned by `builds/target.json`, including its locally measured hash.
  Do not invent a version, checksum, compiler, address, test result, cost or completion denominator.
- Address identity is `(build id, RVA)`; never transfer an address between versions without proof.
- Every finding identifies sources, revisions, source exposure, method, limitations and confidence.
  Label inferred names as guesses. Preserve unknowns rather than filling them plausibly.
- Byte match, semantic equivalence, inferred behavior and layout-size agreement are different claims.
- Mark a function `matched` only under the implemented matching gate and acceptance rule in
  `docs/verification.md`: byte match on two hosts plus one Reviewer
  approval, integration. Bootstrap CI checks only publication hygiene, metadata and site
  generation; it does NOT compare against the game. The separate CI-hash job (docs/verification.md, "CI hash check as the second host") does compare compiled functions against published target hashes and counts as the second verifier host.
- Progress comes only from `data/progress.json`; totals are derived, not manually entered into HTML.
  Unknown scope means no completion percentage. No dummy success records or fake history.
