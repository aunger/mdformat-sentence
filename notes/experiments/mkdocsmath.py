"""A paragraph opening with `\\[` under mdformat-mkdocs: DESIGN.md section 3.5, run.

It establishes:
  1. mdformat-mkdocs parses a paragraph whose first line opens with `\\[` as
     display math, whole or in part, by where its `\\]` falls among its
     lines: all of it when the first `\\]` is on a later line, the first
     line when that `\\]` is followed by a space there, and none when it is
     followed by another character there. A `\\[` opening a later line
     never opens math, because the block cannot interrupt a paragraph.
     This is math safety.
  2. Formatting the math reading drops what follows that `\\]`, so a line
     break that moves the `\\]` off the first line deletes text; plain
     mkdocs does it too, when its own wrap moves the `\\]`.

Needs mdformat 1.0.0 and mdformat-mkdocs 5.3.0.
"""
import mdformat
from mdformat._util import build_mdit
from mdformat.renderer import MDRenderer

mdit = build_mdit(MDRenderer, mdformat_opts={"wrap": "keep"}, extensions={"mkdocs"})


def blocks(md):
    return [t.type for t in mdit.parse(md) if t.nesting >= 0 and t.level == 0]


print("1. What mkdocs parses\n")
for label, md in (
    ("`\\]:` on the first line", "\\[ a. Then \\[Foo\\]: bar\n"),
    ("`\\]` and a space on line one", "\\[ a \\] b.\nThen more.\n"),
    ("`\\]` on a later line", "\\[ a.\nThen \\[Foo\\]: bar\n"),
    ("no `\\]` at all", "\\[ a.\nThen more.\n"),
    ("`\\[` opening a later line", "It ended.\n\\[ a.\nThen \\] b\n"),
):
    print(f"   {label:28} {md!r:36} {blocks(md)}")

print("\n2. What formatting it returns\n")
for label, md, wrap in (
    ("one line, --wrap keep", "\\[ a. Then \\[Foo\\]: bar\n", "keep"),
    ("broken after a., --wrap keep", "\\[ a.\nThen \\[Foo\\]: bar\n", "keep"),
    ("one line, --wrap 8", "\\[ a. Then \\[Foo\\]: bar\n", 8),
):
    out = mdformat.text(md, options={"wrap": wrap}, extensions={"mkdocs"})
    print(f"   {label:30} {md!r:32} -> {out!r}")
