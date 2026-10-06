# Quirks: mdformat-mkdocs

A note, not a specification.
Behavior of mdformat-mkdocs that `DESIGN.md` works around, or that may be worth an upstream issue.
Version 5.3.0 with mdformat 1.0.0; *verified* means run, *read* means read from source.
It installs alongside mdformat-gfm 1.0.0 and mdformat-footnote 0.1.3 without dependency conflicts.
Nothing here has been filed.

______________________________________________________________________

## The spaced-URL fixer turns escaped text into a link

**Filing candidate.** *Verified* 2026-10-06, mkdocs alone.
`The term \[x\](see the y note) is escaped. Then more.` at `--wrap keep`, mdformat's default, becomes `The term [x](<see the y note>) is escaped.`, a link where the source had escaped text, so the render changes.
At `--wrap no` and `40` mkdocs alone leaves it alone, because its regex needs a literal space and sees wrap points.
With this plugin loaded, which pins gaps to literal spaces before mkdocs runs, the misfire happens at `--wrap no` and `40` too.
The CLI refuses the file; the API returns the changed text.
`TRADE-OFFS.md` records it as a known incompatibility.

## An abbreviation definition wrapped to a line start changes the document

**Filing candidate.** *Verified* 2026-10-06, mkdocs alone.
`Sentence one here. *[HTML]: Hyper Text Markup Language is the term.` at `--wrap 18` or `20` comes back with `*[HTML]:` at a line start, unescaped, split into separate paragraphs, and not render-equal; at `--wrap 10` and `15` mdformat escapes it to `\*\[HTML\]:`.
§3.5 refuses a break that would put `*[label]:` at a line start.

## Filler words in re-wrapped list items

**Compatibility risk.** *Verified* (`experiments/seam_mkdocs.py`).
At an integer `--wrap`, mkdocs's `inline` postprocessor re-wraps list-item text itself and inserts U+E000 filler words between real ones, at width-dependent positions.
An `inline` postprocessor loaded after it sees a different segmentation at each width, so it is width-dependent wherever the re-wrapped item holds a sentence end.
`DESIGN.md` §2.2 hooks a renderer, which runs before it.

## An attribute list is a container that does not render its children

**Compatibility risk.** *Read*, with the hook-point review's measurement.
`{ … }` parses as `python_markdown_attr_list`, rendered by `_render_meta_content` without rendering its children.
§3.1 makes such a node an atom.

## `%20` is rewritten after the inline render

**Compatibility risk.** The hook-point review's measurement.
mkdocs's `inline` postprocessor rewrites `%20` in link destinations back into `<… …>`, so text compared after the full paragraph pipeline differs from the text the plugin decided.
It matters to a dry-run check (`FUTURE-WORK.md`), not to the plugin as specified.
