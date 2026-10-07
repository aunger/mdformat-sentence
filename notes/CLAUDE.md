# notes/

Working material behind `DESIGN.md`: research, measurements, deferrals, accepted trade-offs and third-party quirks.
Nothing here is normative; `README.md` lists the files.

## Linking to these files

Notes may be linked to from `DESIGN.md`, from commits, from issues and from other notes.
The preferred granularity for an incoming link is a commit SHA plus a heading, for example
`https://github.com/aunger/mdformat-sentence/blob/7b7f12bc9cb8c295cb246697f848a65424aeea26/notes/QUOTE-ROLES.md#0-the-answer`,
or in prose, "`QUOTE-ROLES.md` at `7b7f12b`, section *0. The answer*".
Do not link to line numbers: these files are edited in place, and a heading survives an edit that moves every line below it.
A link without a SHA is fine between files in the same commit.

## Conventions

- `quirks-<project>.md` records behavior of one third-party project that the design works around or that may deserve an upstream issue. Each entry says which, and whether it was run or read.
- `FUTURE-WORK.md` records deferrals as observation plus intention; an intention is not a commitment.
- `TRADE-OFFS.md` records costs the design accepts on purpose.
- A claim that was measured says so and names the program in `experiments/` that reproduces it.
