"""mdformat-mkdocs block openers at a line start, run.

It establishes that mdformat-mkdocs neither escapes nor indents a caption
opener `///` or an mkdocstrings injection `:::` that its own word wrap
puts at the start of a paragraph line, and that both then interrupt the
paragraph and change the render. The plugin's capital test refuses both
words, so only a `split` rule broad enough to pass them
could let a break do the same (notes/FUTURE-WORK.md).

Needs mdformat 1.0.0 and mdformat-mkdocs 5.3.0.
"""
import mdformat
from mdformat._util import is_md_equal

for md in ("It ended. /// caption follows.\n", "It ended. ::: x.y is injected.\n"):
    out = mdformat.text(md, options={"wrap": 12}, extensions={"mkdocs"})
    same = is_md_equal(md, out, options={"wrap": 12}, extensions=["mkdocs"])
    print(f"   --wrap 12  {md!r:36} -> {out!r}  render {'equal' if same else 'CHANGED'}")
