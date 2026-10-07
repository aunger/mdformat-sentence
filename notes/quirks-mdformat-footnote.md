# Quirks: mdformat-footnote

A note, not a specification.
Behavior of mdformat-footnote that `DESIGN.md` works around, or that may be worth an upstream issue.
Version 0.1.3 with mdformat 1.0.0; *verified* means run.
Nothing here has been filed.

______________________________________________________________________

## A footnote definition wrapped to a line start deletes text

**Filing candidate.** *Verified* 2026-10-06, footnote alone.

```
Sentence one here. [^x]: not a definition, just text.

[^x]: real note.
```

at `--wrap 18` or `20` comes back as `Sentence one here.` and nothing else: mdformat's own wrap puts `[^x]:` at a line start, where the second render pass can read a definition, and both the paragraph's tail and the real note are gone.
At `--wrap 15` the wrap happens to fall elsewhere and the text survives.
§3.3 keeps a footnote reference from opening a sentence, and §3.5 refuses a break that would put `[label]:` at a line start; either alone prevents this.

## Footnote references are atoms

**Compatibility risk.**
With the plugin loaded, `[^1]` is a node of its own, so a test that a segment's last character lies inside an atom loses every footnoted sentence end, `hand.[^1] This`.
§3.2 tests the terminator's position instead.
