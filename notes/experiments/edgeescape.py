"""Escapes a newline causes beside a mark: DESIGN.md section 3.5, run.

Each input in 1 is what a break at a sentence end would hand mdformat's
second pass (section 2.3), formatted at --wrap keep so that mdformat itself
moves no line break.

It establishes:
  1. mdformat's `text()` leaves a lone `*` or `_` unescaped between
     spaces and escapes it beside a line break, at the end of a line or at
     the start of one, because the edge of a text leaf is not whitespace to
     it; the render is the same, so only the source changes. Emphasis
     markup is not escaped beside a line break. This is edge safety's
     second entry.
  2. mdformat-mkdocs's `paragraph` postprocessor escapes `~` or `:` and a
     space at the start of a line, a definition-list marker, wherever the
     line break came from; plain mdformat leaves it alone. This is
     line-start safety's definition-list entry.

Needs mdformat 1.0.0 and, for 2, mdformat-mkdocs 5.3.0.
"""
import mdformat
from mdformat._util import is_md_equal


def fmt(md, extensions=()):
    return mdformat.text(md, options={"wrap": "keep"}, extensions=set(extensions))


def show(label, md, extensions=()):
    out = fmt(md, extensions)
    same = is_md_equal(md, out, options={"wrap": "keep"}, extensions=list(extensions))
    verdict = "unchanged" if out == md else "CHANGED, render " + ("equal" if same else "differs")
    print(f"   {label:34} {md!r:34} -> {out!r}  {verdict}")


print("1. A lone * or _ beside a line break, no plugin\n")
show("* mid-line", "It ended. * Then more.\n")
show("* ending a line", "It ended. *\nThen more.\n")
show("_ mid-line", "It ended. _ Then more.\n")
show("_ ending a line", "It ended. _\nThen more.\n")
show("_ opening a line", 'It ended. "\n_ Then more.\n')
show("emphasis ending a line", "It *ended.*\nThen more.\n")
show("emphasis opening a line", "It ended.\n*Then* more.\n")

print("\n2. A definition-list marker, put at a line start by mdformat's own wrap\n")
for md in ('It ended. " ~ Then more.\n', "It ended. a : Then more.\n"):
    for extensions in ((), ("mkdocs",)):
        out = mdformat.text(md, options={"wrap": 12}, extensions=set(extensions))
        print(f"   {'+'.join(extensions) or 'no plugin':10} --wrap 12  {md!r:30} -> {out!r}")
