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

**Observed.** §3.5's line-start rules are lists kept by hand, the co-plugin definitions among them.
The hook-point review prototyped a dry run of the real paragraph pipeline from the `inline` slot: it catches render-level hazards (the task box, enumerators, the `<div>` indent) and reproduced the hand-kept list exactly under mdformat-gfm and mdformat-mkdocs, but only when compared against a dry run of the all-pinned text.
Compared against the decided text it misfires under mkdocs, whose `inline` postprocessor rewrites `%20`.
It cannot see parse-level traps such as `[^x]:` and `*[HTML]:`, which `paragraph()` does not rewrite.

**Intention.** Use it as the oracle for §6.2's source-equality row first, and consider it at run time only after it has been run against plugins that own `paragraph`.

## Detection

### More sentence openers

**Observed.** Only a code span, an image, an autolink or a tag-only raw HTML segment opens a sentence regardless of case (§3.3).
A co-plugin's atoms open nothing, which costs breaks before inline math and wikilinks.
An mdformat-gfm bare URL as an opener was measured at 24 gaps in about 150,000 paragraphs and deferred.

**Intention.** `MATH-AND-OPENERS.md` sets out how named openers could be added, as a rules-file key rather than as rules, and what has to be measured first.

## Packaging and versions

### Widening the mdformat bound

**Observed.** The dependency is `mdformat>=1.0.0,<1.1`, because the hook point rests on facts mdformat does not promise (§2): `WRAP_POINT`, the pipeline's order, and the postprocessor-map convention the recorder uses.
mdformat 0.7.17 and 0.7.22 were read and match, but only 1.0.0 was run.

**Intention.** Move the bound only after §6's gate passes against the newer mdformat, which the non-blocking CI job runs.

## Upstream

### Issues for other projects

**Observed.** Several co-plugins damage documents on their own at an integer `--wrap`, independent of this plugin, and mdformat-dollarmath drops `\$` escapes.

**Intention.** Consider an issue for each entry marked as a filing candidate in the `quirks-*.md` files.
None has been filed.
