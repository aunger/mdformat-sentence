"""mdformat-space-control turns an authored line break into a literal space. notes/quirks-mdformat-space-control.md.

Needs mdformat 1.0.0 and mdformat-space-control 0.5.0, which install together.

The probe is a stand-in `inline` renderer, as DESIGN.md §2.2 places the plugin: it calls
DEFAULT_RENDERERS["inline"], breaks at a wrap point after [.!?] before a capital, and pins every
other wrap point to a space. It runs alone and beside space-control, in both load orders.

It establishes:
  1. with space-control loaded, the `softbreak` between two authored lines reaches the `inline`
     renderer as a literal space, not a wrap point, at --wrap no and 40, so the sentence end there
     is not a gap the probe can break; without it the same position is a wrap point;
  2. mdformat.text() renders twice, and the second pass reads each break the first pass made as a
     `softbreak`, which space-control joins again: a paragraph on one line comes back unbroken,
     one already broken at its sentence ends comes back as it was, and one with an authored break
     at one sentence end and a missing break at another keeps the first and gains none, in either
     load order: every break in the output is one the author made;
  3. at --wrap keep, where the probe does nothing, space-control joins the author's lines.

It prints, first, every text the probe is handed during one mdformat.text() call, with the child
node types, for each source alone and beside space-control; then a table of source, extensions,
--wrap, output and whether formatting the output again is stable.
"""
import re

import mdformat
from mdformat.renderer import DEFAULT_RENDERERS

TRACE = []


def inline(node, ctx):
    text = DEFAULT_RENDERERS["inline"](node, ctx)
    out = re.sub(r"(?<=[.!?])\x00+(?=[A-Z])", "\n", text).replace("\x00", " ") if ctx.do_wrap else text
    TRACE.append(([c.type for c in node.children], text, out))
    return out


class Probe:
    RENDERERS = {"inline": inline}
    POSTPROCESSORS = {}

    @staticmethod
    def update_mdit(mdit):
        pass


mdformat.plugins.PARSER_EXTENSIONS["probe"] = Probe
SOURCES = ("One here. Two here.\n", "One here.\nTwo here.\n", "One here. Two\nhere.\nThree here.\n")

print("1. what the probe is handed, --wrap no, pass by pass")
for exts in (["probe"], ["probe", "space_control"]):
    for src in SOURCES:
        TRACE.clear()
        out = mdformat.text(src, extensions=exts, options={"wrap": "no"})
        print(f"  {'+'.join(exts)} {src!r} => {out!r}")
        for n, (kids, text, decided) in enumerate(TRACE, 1):
            print(f"    pass {n}: {kids} {text!r} -> {decided!r}")

print("\n2. outputs")
for src in SOURCES:
    for exts in (["probe"], ["probe", "space_control"], ["space_control", "probe"]):
        for wrap in ("no", 40, "keep"):
            out = mdformat.text(src, extensions=exts, options={"wrap": wrap})
            again = mdformat.text(out, extensions=exts, options={"wrap": wrap})
            print(f"  {src!r:38} {'+'.join(exts):20} {str(wrap):5} {out!r:38} "
                  f"{'stable' if again == out else 'UNSTABLE'}")
