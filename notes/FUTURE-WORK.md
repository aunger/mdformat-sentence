# Future work: what the design deferred, and why

A note, not a specification.
`DESIGN.md` prefers a first version small enough to build and test, and defers work to keep it that way (section 1).
Each entry here records a deferral: the observation that prompted it and the intention behind it.
**An intention is not a commitment.**
An entry leaves this file when `DESIGN.md` takes it up or a later decision drops it, and the commit that does so says which.

Costs the design accepts, rather than work it postpones, are in `TRADE-OFFS.md`.
Problems found in other projects, some of them candidates for an upstream issue, are in the `quirks-*.md` files.

______________________________________________________________________

## Configuration

### Paths in `include`

**Observed.** `include` takes names only, looked up among the shipped rules files and in `.mdformat-sentence/` beside the `.mdformat.toml` mdformat read (section 4).
A path would let the projects of a monorepo share one rules file; under names only, each project with its own `.mdformat.toml` keeps its own copy.

**Intention.** Add paths if monorepo users ask.
It breaks no configuration to add them later, where taking them away later would break every configuration that used one, which is why they start absent.

### String values of `base_rules`

**Observed.** `base_rules` is a boolean, and v1 refuses any other value with a load error, on the command line and in TOML (section 4).
The refusal keeps the meaning of a string free.

**Intention.** A string may later name a base other than the shipped default, which would give a project in another language a base of its own without a `language` key.
Nothing is designed for it yet, and the spec does not advertise it.

### Publishing `--sentence-include`

**Observed.** The flag exists but is hidden from `--help` and outside the versioning policy (section 4).
Its earlier design needed a separate `dest`, a working-directory base for paths and handling for when no table is configured; names-only lookup removed the path base.

**Intention.** Publish it if a use appears that the config file cannot serve, after settling the one wrinkle left: the plugin cannot tell `cli_include` written in TOML from the flag.

## The hook point

### A `paragraph` renderer contingency

**Observed.** The plugin owns `RENDERERS["inline"]`, and mdformat lets one plugin own a renderer slot.
None of 48 plugin sources read defines an `inline` renderer, and the `root` canary of section 2.2 reports it if one ever loads first.

**Intention.** If that happens, move to a `paragraph` renderer that hands mdformat's paragraph renderer a context with this plugin's inline renderer injected.
It composes with an `inline` owner but not with a `paragraph` owner; mdformat-hatena and mdformat-sentencebreak define `paragraph` renderers.

### Verify by dry run instead of a hand-kept list

**Observed.** Section 3.5's line-start checks are lists kept by hand, the co-plugin definitions among them.
The hook-point review (`DESIGN-REVIEW-HOOK-POINT-2026-10-06.md` at `9264f70`, section *8. Future work*, F1) prototyped a dry run of the real paragraph pipeline from the `inline` slot: it catches render-level hazards (the task box, enumerators, the `<div>` indent) and reproduced the hand-kept list exactly under mdformat-gfm and mdformat-mkdocs, but only when compared against a dry run of the all-pinned text.
Compared against the decided text it misfires under mkdocs, whose `inline` postprocessor rewrites `%20`.
It cannot see parse-level traps such as `[^x]:` and `*[HTML]:`, which `paragraph()` does not rewrite.

**Intention.** Use it as the oracle for section 6.2's source-equality row first, and consider it at run time only after it has been run against plugins that own `paragraph`.

## Detection

### More opening atoms

**Observed.** Only a code span, an image, an autolink or a tag-only raw HTML segment opens a sentence regardless of case (section 3.3).
A co-plugin's atoms open nothing, which costs breaks before inline math and wikilinks.
An mdformat-gfm bare URL as an opening atom was measured at 24 gaps in about 150,000 paragraphs and deferred.

**Intention.** `MATH-AND-OPENERS.md` sets out how named opening atoms could be added, as a rules-file key rather than as rules, and what has to be measured first.

### Clause breaks, sembr#5 and sembr#6

**Observed.** Section 5.1 declines sembr#5 because punctuation alone over-fires, and section 5.2 shows that sembr#6 is invisible to punctuation and mostly to vocabulary.

**Intention.** If clause breaks are ever added they are a separate decision, and a parse is the mechanism to evaluate first.
It would add a model dependency that this design's footprint, mdformat and `tomli` below Python 3.11, does not have.
It would also need an answer to section 1's promise and section 6.2's locality row: a decision made from the whole sentence is still a function of the text, but only if the model is deterministic and analyzes one sentence at a time, so that an edit in one sentence cannot move a break in another.

## Packaging and versions

### Widening the mdformat bound

**Observed.** The dependency is `mdformat>=1.0.0,<1.1`, because the hook point rests on facts mdformat does not promise (section 2): `WRAP_POINT`, the pipeline's order, and the postprocessor-map convention the recorder uses.
mdformat 0.7.17 and 0.7.22 were read and match, but only 1.0.0 was run.

**Intention.** Move the bound only after section 6's gate passes against the newer mdformat, which the non-blocking CI job runs.

## Upstream

### A line-breaking channel in mdformat

**Observed.** The plugin decides line layout from the `inline` slot and hands it to `paragraph()` through the wrap channel, because mdformat 1.0.0 lets no plugin supply that step, and mdformat-space-control shows what that costs (`quirks-mdformat-space-control.md`).
`MDFORMAT-WRAP-AND-OVERRIDES.md` sets out what could be asked upstream: named wrap modes in section 5.5, a split of wrap-point production from width wrapping in section 5.6, and a line-breaking step in `paragraph()` in section 5.8, with the existing issue to join in section 5.7.
Section 5.8 also records what such a step must be handed, since a node and its text do not give the offsets that `DESIGN.md` section 3.1's recorder supplies, and reasons, from the two injections `experiments/parahook.py` measures, that no `paragraph` placement in 1.0.0 reaches wrap points while keeping `paragraph()`'s escaping except through the `inline` slot.
Nothing has been filed, and the design does not wait on it.

### Issues for other projects

**Observed.** Several co-plugins damage documents on their own at an integer `--wrap`, independent of this plugin, and mdformat-dollarmath drops `\$` escapes.

**Intention.** Consider an issue for each entry marked as a filing candidate in the `quirks-*.md` files.
None has been filed.

## Repository tooling

### An mdformat plugin that checks local links

**Observed.** Issue #27 plans links from section mentions and from `sembr#N` to the headings of `DESIGN.md` and the rows of the table in its section 5, and a renamed heading would break every link to it without a warning.
No mdformat plugin checks links, going by mdformat's plugin list and a web search on 2026-10-28; that was read, not run.
Standalone checkers exist, among them linklint and a markdownlint rule for GitHub's anchors, but each is another tool beside mdformat with its own idea of what an anchor is.

**Intention.** Build a small plugin, separate from this one, that makes `mdformat --check` fail when a relative link names no file, or a fragment names no heading or `<a id>` anchor, in the same file or another, using GitHub's rules for heading anchors.
It would leave the text unchanged, so it would compose with this plugin and any other.
How a plugin can report a failure is not settled: mdformat 1.0.0's plugin interface is for rendering, and how mdformat treats a plugin that raises has been neither read nor run.
