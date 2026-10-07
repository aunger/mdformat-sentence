"""Does a text-only inline postprocessor, with no walk and no re-render, survive mdformat-mkdocs?

DESIGN.md §2.2. Needs mdformat 1.0.0 and mdformat-mkdocs 5.3.0, which install together.

The probes are seam.py's `decide` (break after [.!?] before a capital) with no walk at all:
  pp = POSTPROCESSORS["inline"], reads only the text it is handed
  rr = RENDERERS["inline"], calls DEFAULT_RENDERERS["inline"], then decides
Both pin every other gap to a literal space, so mdformat's own wrap has nothing to act on.

It establishes three things:
  1. mdformat-mkdocs's inline postprocessor, at an integer --wrap and inside a list item, re-wraps the
     text itself and inserts U+E000 filler *words* between the real ones, so a postprocessor loaded after
     it sees a different segmentation than at --wrap no;
  2. a text-only postprocessor loaded after mkdocs therefore decides on different text per width
     (a filler segment can follow a sentence end, fails the capital test, and the break is lost):
     width independence fails with no walk involved; loaded before mkdocs it holds;
  3. the renderer variant is width independent in both orders.
"""
import re
import sys
import types

import mdformat
import mdformat.plugins as P
from mdformat.renderer import DEFAULT_RENDERERS


def decide(text):
    segs = re.split(r"\x00+", text)
    out = [segs[0]]
    for left, right in zip(segs, segs[1:]):
        brk = left[-1:] in (".", "!", "?") and right[:1].isupper()
        out += ["\n" if brk else " ", right]
    return "".join(out)


def applies(node, text):
    return node.parent is not None and node.parent.type == "paragraph" and "\x00" in text


def as_postprocessor(text, node, context):
    return decide(text) if applies(node, text) else text


def as_renderer(node, context):
    text = DEFAULT_RENDERERS["inline"](node, context)
    return decide(text) if applies(node, text) else text


def plugin(**surface):
    base = dict(CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS={},
                add_cli_argument_group=lambda g: None, update_mdit=lambda m: None)
    return types.SimpleNamespace(**{**base, **surface})


P.PARSER_EXTENSIONS["pp"] = plugin(POSTPROCESSORS={"inline": as_postprocessor})
P.PARSER_EXTENSIONS["rr"] = plugin(RENDERERS={"inline": as_renderer})

DOC = ("- First item has a long sentence that goes on for quite a while indeed. "
       "Then a second sentence follows it closely here.\n"
       "- Second item is short. And has two sentences.\n")

print("1. What a postprocessor loaded after mkdocs receives for the first item\n")
SEEN = []
P.PARSER_EXTENSIONS["spy"] = plugin(POSTPROCESSORS={"inline": lambda t, n, c: SEEN.append(t) or t})
for wrap in ("no", 40):
    SEEN.clear()
    mdformat.text(DOC, extensions=["mkdocs", "spy"], options={"wrap": wrap})
    print(f"   --wrap {wrap!s:3} {SEEN[0]!r}")
print()

print("2. The same item through each hook, mkdocs before and after\n")
for hook in ("pp", "rr"):
    for order in (["mkdocs", hook], [hook, "mkdocs"]):
        outs = {w: mdformat.text(DOC, extensions=order, options={"wrap": w}) for w in ("no", 20, 40, 80)}
        distinct = len(set(outs.values()))
        print(f"   {hook} {str(order):18} distinct outputs over --wrap no/20/40/80: {distinct}")
        if distinct > 1:
            for w, o in outs.items():
                if o != outs["no"]:
                    print(f"      --wrap {w}: {o!r}")
                    break
print()
print("3. Which order a caller gets through the API follows PYTHONHASHSEED (extensions is a set)")
import subprocess
code = "print(list({'mkdocs', 'pp'}))"
orders = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         env={"PYTHONHASHSEED": str(s)}).stdout.strip() for s in range(1, 5)}
print(f"   seeds 1 to 4: {sorted(orders)}")
