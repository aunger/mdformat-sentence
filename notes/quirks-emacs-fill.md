# Quirks: GNU Emacs `fill-paragraph-semlf`

A note, not a specification.
`DESIGN.md` §4.1 cites `fill-paragraph-semlf` as the existing product that honors the fill width inside a sentence.
This records what it does, and unlike the other `quirks-*.md` files it records prior art rather than something the design works around.

*Read* means read from source: `lisp/textmodes/fill.el` and `lisp/textmodes/paragraphs.el` on the `emacs-31` branch of the `emacs-mirror/emacs` mirror at `65dc4f1c6d91c85911daea3e913adcb91e0e65b2`.
Nothing in Emacs was run.

______________________________________________________________________

## Sentence ends break, and everything else is ordinary filling

**Prior art.** *Read.*
`fill-region-as-paragraph-semlf` binds `fill-column` to `most-positive-fixnum` for its first call only, which joins the paragraph into one line.
It then finds each sentence end with `forward-sentence` and fills that sentence with `fill-region-as-paragraph-default` under the ambient `fill-column`.
Its docstring says so: "The variable `fill-column` controls the width for filling."
A sentence longer than the column therefore wraps at whitespace on width alone, which is the mode §4.1 declines, and the output is not a function of the text.

## A single space does not end a sentence by default

**Prior art.** *Read.*
The docstring says: "If `sentence-end-double-space` is non-nil, period followed by one space is not the end of a sentence."
`sentence-end-double-space` defaults to `t` (`paragraphs.el`, "Non-nil means a single space does not end a sentence").
On ordinary single-spaced Markdown the command breaks nothing until the user sets it to `nil`.

## Two projects are called semlf

**Prior art.** *Read* (the README, fetched 2026-10-07; PyPI metadata).
The standalone Emacs package, `jroimartin/semlf`, says in its README: "This repository has been archived. The package is now part of GNU Emacs."
A different project of the same name, `semlf` 1.0.1 on PyPI by Arlo Liu, is described as "A diff-aware prose guardrail: one-thought-per-line linefeeds in comments, docstrings, and Markdown".
It has a different author and a different purpose.
