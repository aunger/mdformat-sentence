# Quirks: mdformat-gfm

A note, not a specification.
Behavior of mdformat-gfm that `DESIGN.md` works around, or that may be worth an upstream issue.
Version 1.0.0 with mdformat 1.0.0; *verified* means run, *read* means read from source.
Nothing here has been filed.

______________________________________________________________________

## `xxxx` is glued to a task item's first word at an integer width

**Compatibility risk.** *Verified* (`experiments/seam.py` §2 and §5).
gfm's `inline` postprocessor prefixes `xxxx` to the first paragraph of a task-list item to reserve the width of `[ ] `, and its `list_item` renderer removes the four characters again.
Any `inline` postprocessor loaded after gfm sees `xxxxMr.` as the first word, so `- [ ] Mr. Smith left early. Then he came back.` decides differently at `--wrap 40` than at `--wrap no`.
mdformat-openmmlab carries a copy of the same postprocessor (*read*).
`DESIGN.md` §2.2 hooks a renderer, which runs before every `inline` postprocessor.

## A task box at a line start is escaped

**Compatibility risk.** *Verified* (`experiments/seam.py` §4).
gfm's `paragraph` postprocessor turns a line-opening `[ ]`, `[x]` or `[X]` into `\[X\]`, whichever order the plugins load in, so a break before one changes the source.
§3.5 refuses that break, with or without gfm.

## A bare URL renders its source, not its child

**Compatibility risk.** *Verified* (`experiments/recorder.py` §4).
`gfm_autolink` has a `text` child, but its renderer returns the source text and never renders the child.
A tree walk that expects a container's rendering to contain its children's cannot place it; the hook-point review measured the old walk backing off on bare URLs containing `_(`, `__` or `*`.
§3.1 makes such a node an atom.

## `~~` is escaped in text

**Compatibility risk.** *Read.*
gfm's `text` postprocessor escapes `~~` to `\~~`, so the plugin always sees it escaped; it runs inside the children's render and needs no handling.
