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

## `str.strip()` and `str.splitlines()` act on far more than ASCII whitespace

**Compatibility risk.** *Verified* 2026-10-07 on Python 3.11.15, by testing every codepoint.
`str.strip()` deletes 29 codepoints.
Space, tab and line feed are the three that mdformat turns into wrap points.
The other 26 are not, and 8 of those are missing from `mdformat.codepoints.UNICODE_WHITESPACE`: U+000B, U+001C through U+001F, U+0085, U+2028 and U+2029.
A character list copied from `UNICODE_WHITESPACE` would therefore miss eight of the 26, which supports §3.5's instruction to test with `.strip()` itself.

`str.splitlines()` splits on 10 codepoints: U+000A, U+000B, U+000C, U+000D, U+001C through U+001E, U+0085, U+2028 and U+2029.
Code that splits Markdown source into lines should read it in text mode, which already turns `\r\n` and a lone `\r` into `\n`, and then use `split("\n")`.
`splitlines()` would also end the line at U+000B, U+000C, U+001C through U+001E, U+0085, U+2028 and U+2029, none of which Markdown treats as a line ending.
