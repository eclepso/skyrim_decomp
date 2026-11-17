# Guide for a contributor's coding agent

You are helping an **external contributor** match functions of Skyrim Special Edition. Everything
here runs on the contributor's computer. Do not use the project's internal runners, queues or
verifier hosts.

## The flow

1. Draft the reconstruction locally and get a local comparator PASS.
2. Open a pull request that touches only `reconstruction/**`.
3. Checks run on the PR: a path and leak scan, and a Windows compile whose hashes are compared to
   the published target hashes (host 1). The project's bot compares on a second host, reviews the
   source once and squash-merges the PR with its own message. Nothing else is needed from you.

A function counts as `matched` only after both host comparisons and one review; a local pass is a
candidate. A function that fails stays a draft and the bot comment names a reason code. Fix it and
push to the same branch. Batch several functions in a PR when you can; any classes are fine; a
first PR or a single large function alone is fine.

## Tooling

Drive one tool, `tools/contrib.py` (macOS/Linux: `./sr`; Windows: `.\sr.cmd`), always with
`--json`. Each call prints one JSON object with `ok`, `exit_code`, `error` and `next` (the one next
action); do what `next` says. Exit codes: 0 ok, 1 a check failed, 2 usage, 3 compile failed, 4 unit
or include problem, 5 input missing, 7 a person must decide, 8 offline.

```sh
./sr --json --yes go [--exe "<path>"] [--accept-microsoft-license] \
    --drafted-by "<person>, assisted by <your model id>"
./sr --json compare
./sr --json submit --dry-run
./sr --json submit
```

`go` installs and checks the toolchain (idempotent; finished steps are skipped), picks a function
and prepares a skeleton and a private pack. Then edit the unit under `reconstruction/`, run
`compare` until it passes, and `submit` (it needs a fork remote; if none, ask the person to fork
the repository on GitHub). When you show output publicly, add `--redact`.

The contributor card has the source, label and stopping rules. The
[matching cookbook](matching-cookbook.md) and [declaration kit](declaration-kit.md) are optional
references.

## When to ask the person

Ask when the helper reports these decisions; account, fork and sign-in steps also need them.

1. The path to their `SkyrimSE.exe`, if `setup` cannot find it (exit 5).
2. Microsoft's licence for the Visual Studio 2017 Build Tools (exit 7, `licence` field). Show
   the link; pass `--accept-microsoft-license` only after they accept. Never accept it yourself.
3. System prompts such as Rosetta 2, a `sudo` password or winget source terms. Package installs
   themselves need no decision: pass `--yes`.

**Ask once before reading any listing or pseudo-C.** Reading a pack made from their own copy sends
parts of it to your AI provider. That is their decision and responsibility under their provider's
terms; the project grants no rights in the game. Continue only if they agree.

## Privacy

Packs, listings, pseudo-C, Ghidra projects, bytes, objects, raw diagnostics and paths never go
into a commit, PR, issue or comment. A PR containing disassembly or decompiler names (`FUN_`,
`param_1`, `local_28`), inline assembly, byte arrays or host paths is blocked by an automatic scan
that reports only rule codes and line numbers. Squash merging replaces your commit messages with the
bot's, so your history is not published.

## The game executable

The pinned build is in `builds/target.json` (Steam, 1.7.104.0). If `setup` reports another build,
tell the person; never obtain or modify game files yourself. Their own purchased copy fetched with
their own account through the Steam client or SteamCMD (`setup --steamcmd`) is fine. Never handle
Steam credentials.

## Recommended local decompiler

`go` installs a hash-pinned Ghidra and Temurin privately and analyses in the background (about
1.8 GiB on disk; skipped below about 18 GiB of free RAM; `--no-decompiler` skips it). `start` then
adds a private `decomp.c`. Treat it as an untrusted hint for control flow and types; write your own
source, because `compare` decides the match.

## While a PR is open

Leave **Allow edits by maintainers** on and pull before continuing. Run `./sr feedback --json` at
the start of each session; push fixes to the same branch and never force-push over reviewed commits.
