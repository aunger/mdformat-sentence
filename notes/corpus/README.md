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

## Do not let mdformat reformat this file

`sembr.md` is verbatim third-party content pinned by the checksum above, and it
does not satisfy `mdformat --check`. Running mdformat over this directory will
rewrite it and break both the attribution and every measurement taken against it.

**mdformat's own `exclude` cannot protect it.** The feature requires Python
3.13+, and on anything earlier an `exclude` list in `.mdformat.toml` is a hard
error that stops mdformat formatting *anything* in the repository, including
when a file is named explicitly on the command line. Measured against mdformat
1.0.0 on Python 3.11, which this project supports (`requires-python >= 3.10`).
Reading `is_excluded` in `_cli.py`, an explicitly named file stays excluded on
3.13+ as well, so the feature would not give back a way to format this file on
purpose; that half was read rather than run.

Until this repository has a pre-commit config, whose own `exclude:` is
independent of mdformat's Python floor, the protection is this paragraph.
