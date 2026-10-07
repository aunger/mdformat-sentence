# Quirks: CPython

A note, not a specification.
Behavior of the Python interpreter and standard library that `DESIGN.md` works around.
*Verified* means run on Python 3.11.

______________________________________________________________________

## Case predicates follow the interpreter's Unicode version

**Compatibility risk.** *Verified.*
`str.islower`, `str.isupper` and `str.isalpha` use the interpreter's own Unicode data, UCD 14.0.0 on Python 3.11, and its case properties rather than UAX #29's Sentence_Break.
`'ა'.islower()` is `True`, so a capital test written with them would never break ordinary Georgian prose.
`DESIGN.md` §3.3 reads vendored Sentence_Break tables instead.

## `unicodedata` has no Sentence_Break

**Compatibility risk.** *Read.*
The property is not exposed at all, so the tables are generated from a vendored `SentenceBreakProperty.txt` (§3.3).

## `tomllib` arrived in 3.11

**Compatibility risk.**
The plugin parses rules files itself, so it depends on `tomli` on Python 3.10 (§2).
