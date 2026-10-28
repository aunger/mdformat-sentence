# Quirks: mdformat-sembr

A note, not a specification.
Behavior of `mdformat-sembr` 0.2.0, the other mdformat plugin that puts a newline after sentences.

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
Section 2.2 gives this as a reason for the `inline` hook point.

## `--wrap` is not honored

**By design.** *Verified* 2026-10-07; cause *read*.

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
The plugin's hook is `paragraph` again, so it works on text mdformat has already wrapped, and `insert_breaks` (`_sembr.py`) begins by undoing that wrapping: `_collapse_whitespace` returns `re.sub(r"\s+", " ", text).strip()`.
Its docstring says this is deliberate: "Collapse-then-rebreak is what makes the transform deterministic and idempotent regardless of any existing soft breaks in the input."
This plugin does not honor an integer width either (section 2.5), and a mode that honors it is declined (section 4.1).

## A no-break space becomes a plain space

**Filing candidate.** *Verified* 2026-10-12; cause *read*.

```python
import mdformat
from mdformat._util import is_md_equal

src = "Aaa bbb.\u00a0Ccc ddd eee.\n"
for ext in (set(), {"sembr"}):
    print(repr(mdformat.text(src, extensions=ext)))
# 'Aaa bbb.\xa0Ccc ddd eee.\n'
# 'Aaa bbb. Ccc ddd eee.\n'
print(is_md_equal(src, mdformat.text(src, extensions={"sembr"}), extensions={"sembr"}))
# True

long = "This is a fairly long first sentence here.\u00a0And this is another one.\n"
print(repr(mdformat.text(long, extensions={"sembr"})))
# 'This is a fairly long first sentence here.\nAnd this is another one.\n'
```

```
$ printf 'Aaa bbb.\302\240Ccc ddd eee.\n' > nb.md
$ mdformat nb.md; echo $?
0
$ mdformat --check nb.md; echo $?
0
```

Plain mdformat keeps the U+00A0, and with the plugin it becomes U+0020.
The plugin can then break there, as the longer first sentence shows.
`is_md_equal` returns `True` on `src` and its output, so the CLI writes the change with exit 0, and `--check` then passes on the written file; `--check` on the original reports only that the file is not formatted.
The cause is the collapse in the entry above: `\s` in a `str` pattern matches U+00A0, so `_collapse_whitespace` replaces it like any other whitespace, before any break is decided.
