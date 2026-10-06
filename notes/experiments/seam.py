"""The seam: an `inline` postprocessor against an `inline` renderer. DESIGN.md §2.2, §3.1.

Both probes break after [.!?] before a capital or a `[`, and back off (one
line, every gap a space) when the children's renderings do not add up to the
text they decide, as §3.6 says. The postprocessor re-renders the children
against the live render state; the renderer copies that state before its
children render and re-renders against the copy. mdformat-gfm is the
co-plugin, loaded before and after each probe.

It establishes four things:
  1. the order postprocessors run in is the order plugins load in, which a
     plugin cannot choose; under the API it is a set's iteration order, which
     varies with PYTHONHASHSEED;
  2. with gfm loaded first, the postprocessor backs off on a task-list item at
     an integer width and not at --wrap no, because gfm's own inline
     postprocessor has already prefixed "xxxx"; the renderer runs before every
     inline postprocessor and backs off in no order and no mode;
  3. re-rendering against the live state is not pure: a reference link marks
     its label used, and text before it then escapes `[foo]` the second time
     where it did not the first, 47 characters against 49; the copy makes the
     two renderings equal;
  4. gfm's paragraph postprocessor escapes a task box `[X]` at the start of a
     line a break created, whichever seam broke it, so §3.5 must refuse it.
Needs mdformat 1.0.0 and mdformat-gfm 1.0.0.
"""
import re
import subprocess
import sys
import types

import mdformat
import mdformat.plugins as P
from mdformat.renderer import DEFAULT_RENDERERS

BACKOFFS = []
VETO_TASK_BOX = [False]


def decide(text):
    segs = re.split(r"\x00+", text)
    out = [segs[0]]
    for left, right in zip(segs, segs[1:]):
        brk = left[-1:] != "" and left[-1:] in ".!?" and (right[:1].isupper() or right[:1] == "[")
        if VETO_TASK_BOX[0] and re.match(r"\[[ xX]\]", right):
            brk = False
        out += ["\n" if brk else " ", right]
    return "".join(out)


def walk_adds_up(node, context, text):
    pieces = sum(len(c.render(context)) for c in node.children)
    if pieces != len(text):
        BACKOFFS.append((len(text), pieces))
        return False
    return True


def applies(node, text):
    return node.parent is not None and node.parent.type == "paragraph" and "\x00" in text


def as_postprocessor(text, node, context):
    if not applies(node, text):
        return text
    if not walk_adds_up(node, context, text):
        return re.sub(r"\x00+", " ", text)
    return decide(text)


def as_renderer(node, context):
    env = {**context.env, "used_refs": set(context.env["used_refs"])}
    text = DEFAULT_RENDERERS["inline"](node, context)
    if not applies(node, text):
        return text
    if not walk_adds_up(node, context._replace(env=env), text):
        return re.sub(r"\x00+", " ", text)
    return decide(text)


def plugin(**surface):
    base = dict(CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS={},
                add_cli_argument_group=lambda g: None, update_mdit=lambda m: None)
    return types.SimpleNamespace(**{**base, **surface})


P.PARSER_EXTENSIONS["pp"] = plugin(POSTPROCESSORS={"inline": as_postprocessor})
P.PARSER_EXTENSIONS["rr"] = plugin(RENDERERS={"inline": as_renderer})


def fmt(md, extensions, wrap):
    BACKOFFS.clear()
    out = mdformat.text(md, extensions=extensions, options={"wrap": wrap})
    return out, list(BACKOFFS)


print("1. Load order under the API follows the set\n")
code = "print(list({'gfm', 'probe', 'footnote'}))"
orders = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         env={"PYTHONHASHSEED": str(seed)}).stdout.strip() for seed in range(1, 5)}
print(f"   PYTHONHASHSEED 1 to 4 give {len(orders)} distinct orders: {sorted(orders)}\n")

print("2. A task-list item, gfm before and after each seam\n")
TASK = "- [ ] Do the first thing. Then do the second thing.\n"
for seam in ("pp", "rr"):
    for order in (["gfm", seam], [seam, "gfm"]):
        for wrap in ("no", 40):
            out, backoffs = fmt(TASK, order, wrap)
            print(f"   {seam} {str(order):16} --wrap {wrap!s:3} backoffs={len(backoffs)} {out!r}")
print()

print("3. A reference used after text that names it\n")
REF = "It cites \\[foo\\] early. Then [a link][foo] later.\n\n[foo]: https://x.y\n"
for seam in ("pp", "rr"):
    out, backoffs = fmt(REF, [seam], "no")
    print(f"   {seam} backoffs={backoffs} {out.splitlines()[:2]}")
print()

print("4. A task box at the start of a line a break created\n")
BOX = "It is done. [X] marks a finished task.\n"
for veto in (False, True):
    VETO_TASK_BOX[0] = veto
    for order in (["gfm", "rr"], ["rr", "gfm"]):
        out, _ = fmt(BOX, order, "no")
        print(f"   veto={veto!s:5} {str(order):15} {out!r}")
