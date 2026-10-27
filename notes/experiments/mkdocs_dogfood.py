"""Why DESIGN.md is not dogfooded under mdformat-mkdocs. notes/quirks-mdformat-mkdocs.md, DESIGN.md §6.2.

Needs mdformat 1.0.0, mdformat-mkdocs 5.3.0 and mdformat-gfm 1.0.0, which install together.
Runs at mdformat's default --wrap keep, with compact tables, and without this plugin.
Takes the file to check as an argument; the default is DESIGN.md beside notes/.

It establishes:
  1. mkdocs's spaced-URL fixer reaches inside a code span: `\\[x\\](y z)` becomes `[x](<y z>)`,
     the rendered HTML changes, and mdformat's CLI would refuse the file; the same text in a fenced
     block is left alone;
  2. on DESIGN.md, with mkdocs loaded, alone or with gfm, the rendered HTML changes, and the HTML
     difference is the one table row that quotes that fixer's fixture inside a code span; with gfm
     alone the file comes back unchanged;
  3. every other changed line is a list continuation reindented from the marker's width to four
     spaces, and those lines render the same: with the fixture's escapes removed from the source,
     the output still differs line by line but is render-equal. With
     --align-semantic-breaks-in-lists fewer lines change, but not none.

It prints, per extension set, whether the output equals the source and whether it is render-equal,
the number of changed lines split into reindented and rewritten, the rewritten lines themselves and
the HTML lines that differ.
"""
import difflib
import pathlib
import re
import sys

import mdformat
from mdformat._util import build_mdit, is_md_equal
from markdown_it.renderer import RendererHTML

DEFAULT = pathlib.Path(__file__).resolve().parents[2] / "DESIGN.md"
FIXTURE = r"\[x\](see the y note)"
OPTS = {"compact_tables": True}


def fmt(src, exts, **extra):
    return mdformat.text(src, extensions=exts, options={**OPTS, **extra, "validate": False})


def html_lines(src, exts):
    html = build_mdit(RendererHTML, mdformat_opts=OPTS, extensions=exts).render(src)
    return [re.sub(r"\s+", " ", line) for line in html.splitlines()]


def changed(src, out):
    """(reindented, rewritten) line pairs, from a line diff of the source against the output."""
    reindent, rewrite = [], []
    sm = difflib.SequenceMatcher(None, src.splitlines(), out.splitlines(), autojunk=False)
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == "equal":
            continue
        a, b = src.splitlines()[a0:a1], out.splitlines()[b0:b1]
        for i, (x, y) in enumerate(zip(a, b)):
            (reindent if x.strip() == y.strip() else rewrite).append((a0 + i + 1, x, y))
        for i, x in enumerate(a[len(b):]):
            rewrite.append((a0 + len(b) + i + 1, x, None))
        for y in b[len(a):]:
            rewrite.append((None, None, y))
    return reindent, rewrite


def report(label, src, exts, **extra):
    out = fmt(src, exts, **extra)
    reindent, rewrite = changed(src, out)
    print(f"{label}: {'unchanged' if out == src else 'changed'}, "
          f"render-equal {is_md_equal(src, out, options=OPTS, extensions=exts)}, "
          f"{len(reindent)} lines reindented, {len(rewrite)} rewritten")
    for n, x, y in rewrite:
        print(f"    line {n}: {x!r}\n         -> {y!r}")
    hd = [l for l in difflib.unified_diff(html_lines(src, exts), html_lines(out, exts), lineterm="", n=0)
          if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    for l in hd:
        print(f"    html {l[:160]}")
    return out


print("1. the code-span rewrite, mkdocs alone")
for src in ("`\\[x\\](y z)`\n", "```\n\\[x\\](y z)\n```\n"):
    out = fmt(src, ["mkdocs"])
    print(f"  {src!r} -> {out!r}, render-equal {is_md_equal(src, out, extensions=['mkdocs'])}")

path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
src = path.read_text(encoding="utf-8")
print(f"\n2. {path.name} as it stands")
for exts in (["gfm"], ["mkdocs"], ["gfm", "mkdocs"]):
    report("  " + "+".join(exts), src, exts)

print(f"\n3. {path.name} with the fixture's escapes removed, gfm+mkdocs")
masked = src.replace(FIXTURE, "x (see the y note)")
print(f"  fixture found {src.count(FIXTURE)} time(s)")
report("  default", masked, ["gfm", "mkdocs"])
report("  --align-semantic-breaks-in-lists", masked, ["gfm", "mkdocs"], align_semantic_breaks_in_lists=True)
