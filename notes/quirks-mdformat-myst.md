# Quirks: mdformat-myst

A note, not a specification.
Behavior of mdformat-myst that `DESIGN.md` works around.
Version 0.3.0 with mdformat 1.0.0; *verified* means run.
It depends on mdformat-footnote, mdformat-front-matters and mdformat-gfm.
Nothing here has been filed.

______________________________________________________________________

## A target wrapped to a line start may gain a backslash

**Compatibility risk.** *Verified* 2026-10-06, myst alone.
`Sentence one here. (Label)= then more words.` at `--wrap 10` comes back with `\(Label)=` at a line start: render-equal, but the source gains a backslash.
At `--wrap 18` and `20` the target lands at a line start unescaped, also render-equal.
§3.5 refuses a break that would put `(label)=` at a line start, and the source-equality row of §6.2 is what would see the backslash.
