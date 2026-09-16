# Corpus

## `sembr.md`

The Semantic Line Breaks specification, verbatim and unmodified.

Source: <https://github.com/sembr/specification>, `main` at `84355c8`, fetched 2026-09-12.
sha256 of this copy begins `a729bc02`.
Licence: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), by Mattt.

**Why it is here.** It is the only document available to this project that is
genuine hand-written *clause-level* Semantic Line Breaks, written by the
specification's own author.

That matters more than it sounds. `DESIGN.md` is written one sentence per line,
so it scores perfectly against any detector that asks whether line breaks fall
at sentence or clause boundaries, and a detector evaluated against it looks
flawless at every threshold. Every measurement in `../experiments` that produced
a decisive result produced it against this file and a misleading one against
`DESIGN.md`.

If you evaluate a layout heuristic, evaluate it here.
