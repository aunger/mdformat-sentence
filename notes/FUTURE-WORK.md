# Future work: what the design deferred, and why

A note, not a specification.
`DESIGN.md` prefers a first version small enough to build and test, and defers work to keep it that way (§1).
Each entry here records a deferral: the observation that prompted it and the intention behind it.
**An intention is not a commitment.**
An entry leaves this file when `DESIGN.md` takes it up or a later decision drops it, and the commit that does so says which.

Costs the design accepts, rather than work it postpones, are in `TRADE-OFFS.md`.
Problems found in other projects, some of them candidates for an upstream issue, are in the `quirks-*.md` files.

______________________________________________________________________

## Configuration

### Paths in `include`

**Observed.** `include` takes names only, looked up among the shipped sets and in `.mdformat-sentence/` beside the `.mdformat.toml` mdformat read (§4).
A path would let the projects of a monorepo share one set; under names only, each project with its own `.mdformat.toml` keeps its own copy.

**Intention.** Add paths if monorepo users ask.
It breaks no configuration to add them later, where taking them away later would break every configuration that used one, which is why they start absent.

### String values of `base_rules`

**Observed.** `base_rules` is a boolean, and v1 refuses any other value with a load error, on the command line and in TOML (§4).
The refusal keeps the meaning of a string free.

**Intention.** A string may later name a base other than the shipped default, which would give a project in another language a base of its own without a `language` key.
Nothing is designed for it yet, and the spec does not advertise it.

### Publishing `--sentence-include`

**Observed.** The flag exists but is hidden from `--help` and outside the versioning policy (§4).
Its earlier design needed a separate `dest`, a working-directory base for paths and a rule for when no table is configured; names-only lookup removed the path base.

**Intention.** Publish it if a use appears that the config file cannot serve, after settling the one wrinkle left: the plugin cannot tell `cli_include` written in TOML from the flag.

## The hook point

### A `paragraph` renderer contingency

**Observed.** The plugin owns `RENDERERS["inline"]`, and mdformat lets one plugin own a renderer slot.
None of 48 plugin sources read defines an `inline` renderer, and the `root` canary of §2.2 reports it if one ever loads first.

**Intention.** If that happens, move to a `paragraph` renderer that hands mdformat's paragraph renderer a context with this plugin's inline renderer injected.
It composes with an `inline` owner but not with a `paragraph` owner; mdformat-hatena and mdformat-sentencebreak define `paragraph` renderers.

### Verify by dry run instead of a hand-kept list

**Observed.** Section 3.5's line-start rules are lists kept by hand, the co-plugin definitions among them.
The hook-point review (`DESIGN-REVIEW-HOOK-POINT-2026-10-06.md` at `9264f70`, section *8. Future work*, F1) prototyped a dry run of the real paragraph pipeline from the `inline` slot: it catches render-level hazards (the task box, enumerators, the `<div>` indent) and reproduced the hand-kept list exactly under mdformat-gfm and mdformat-mkdocs, but only when compared against a dry run of the all-pinned text.
Compared against the decided text it misfires under mkdocs, whose `inline` postprocessor rewrites `%20`.
It cannot see parse-level traps such as `[^x]:` and `*[HTML]:`, which `paragraph()` does not rewrite.

**Intention.** Use it as the oracle for §6.2's source-equality row first, and consider it at run time only after it has been run against plugins that own `paragraph`.

## Detection

### More sentence openers

**Observed.** Only a code span, an image, an autolink or a tag-only raw HTML segment opens a sentence regardless of case (§3.3).
A co-plugin's atoms open nothing, which costs breaks before inline math and wikilinks.
An mdformat-gfm bare URL as an opener was measured at 24 gaps in about 150,000 paragraphs and deferred.

**Intention.** `MATH-AND-OPENERS.md` sets out how named openers could be added, as a rules-file key rather than as rules, and what has to be measured first.

### Clause breaks, rules 5 and 6

**Observed.** Section 5.1 declines rule 5 because punctuation alone over-fires, and §5.2 shows that rule 6 is invisible to punctuation and mostly to vocabulary.

**Intention.** If clause breaks are ever added they are a separate decision, and a parse is the mechanism to evaluate first.
It would add a model dependency that this design's footprint, mdformat and `tomli` below Python 3.11, does not have.
It would also need an answer to §1's promise and §6.2's locality row: a decision made from the whole sentence is still a function of the text, but only if the model is deterministic and analyzes one sentence at a time, so that an edit in one sentence cannot move a break in another.

## Packaging and versions

### Widening the mdformat bound

**Observed.** The dependency is `mdformat>=1.0.0,<1.1`, because the hook point rests on facts mdformat does not promise (§2): `WRAP_POINT`, the pipeline's order, and the postprocessor-map convention the recorder uses.
mdformat 0.7.17 and 0.7.22 were read and match, but only 1.0.0 was run.

**Intention.** Move the bound only after §6's gate passes against the newer mdformat, which the non-blocking CI job runs.

## Upstream

### A line-breaking channel in mdformat

**Observed.** The plugin decides line layout from the `inline` slot and hands it to `paragraph()` through the wrap channel, because mdformat 1.0.0 lets no plugin supply that step, and mdformat-space-control shows what that costs (`quirks-mdformat-space-control.md`).
`MDFORMAT-WRAP-AND-OVERRIDES.md` sets out what could be asked upstream: named wrap modes in §5.5, a split of wrap-point production from width wrapping in §5.6, and a line-breaking step in `paragraph()` in §5.8, with the existing issue to join in §5.7.
Section 5.8 also records what such a step must be handed, since a node and its text do not give the offsets that `DESIGN.md` §3.1's recorder supplies, and measures that no `paragraph` placement in 1.0.0 reaches wrap points while keeping `paragraph()`'s escaping, except by injecting an `inline` renderer (`experiments/parahook.py`).
Nothing has been filed, and the design does not wait on it.

### Issues for other projects

**Observed.** Several co-plugins damage documents on their own at an integer `--wrap`, independent of this plugin, and mdformat-dollarmath drops `\$` escapes.

**Intention.** Consider an issue for each entry marked as a filing candidate in the `quirks-*.md` files.
None has been filed.
