# Quirks: mdformat-sembr

A note, not a specification.
Behavior of `mdformat-sembr` 0.2.0, the other mdformat plugin that puts a newline after sentences, which `DESIGN.md` §2.2 positions this design against.

*Verified* means run on mdformat 1.0.0 in a separate virtual environment.
The plugin registers the entry point `sembr`, and the CLI enables every installed plugin when `--extensions` is absent, so installing it beside a baseline changes the baseline.
*Read* means read from the installed source.
Nothing here has been filed.
This plugin has no implementation yet, so how the two behave together is untested.

______________________________________________________________________

## A sentence followed by an enumerator becomes a list

**Filing candidate.** *Verified* 2026-10-07.

```python
import mdformat
from mdformat._util import is_md_equal

src = "First sentence here. 1. Two words follow along.\n"
opts = {"wrap": 80}
out = mdformat.text(src, options=opts, extensions={"sembr"})
print(repr(out), is_md_equal(src, out, options=opts, extensions={"sembr"}))
# 'First sentence here.\n\n1. Two words follow along.\n' False
```

The CLI refuses the file with exit 1 and "Formatted Markdown renders to different HTML than input Markdown".
The same input with `extensions=set()` comes back unchanged and renders the same.

The plugin's only hook is `POSTPROCESSORS["paragraph"]` (*read*, `_postprocess_paragraph`), which its docstring describes as inserting breaks "into an already-rendered paragraph string".
`paragraph()` has by then escaped line starts, so a newline the plugin inserts can create a line start that nothing escaped, which is what the output above shows.
§2.2 gives this as a reason for the `inline` hook point.

## `--wrap` is not honored

**Filing candidate.** *Verified* 2026-10-07.

```python
import mdformat

para = ("The quick brown fox jumps over the lazy dog and keeps running through the "
        "forest until it reaches the river bank where it finally stops to drink.\n")
for ext in (set(), {"sembr"}):
    out = mdformat.text(para, options={"wrap": 60}, extensions=ext)
    print([len(line) for line in out.rstrip().split("\n")])
# [53, 58, 32]
# [145]
```

The paragraph is 145 characters.
Plain mdformat wraps it at 60, and with the plugin it comes back as one 145-character line.
The cause was not investigated beyond the hook: `paragraph` again, so the plugin works on text mdformat has already wrapped.
