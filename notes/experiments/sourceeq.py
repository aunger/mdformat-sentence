"""Source equality: DESIGN.md §6.2's document-level row, run.

A plugin that only turns wrap points into newlines leaves a document that,
with each added break undone, is byte-identical to plain mdformat's at
--wrap no. Undoing a break means joining the line to the one before it with
a space, after removing the prefix mdformat writes on every later line of
the paragraph's containers: "> " for a blockquote, and for a list item as
many spaces as its marker is wide. Nothing else is undone.

The postprocessor here breaks after every [.!?] with no line-start rule, so
§3.5's hazards happen. It establishes three things:
  1. the prefix rule is exact: every container case passes, nested too, and
     so does a numbered list, whose markers mdformat pads to one width;
  2. the row fails where §3.5's line-start rule is the only guard, the
     four-space HTML indent and the backslash escape, and render equality
     passes both; a break before ~~~ fails both, because mdformat's second
     render turns the damaged render into damaged source;
  3. stripping every leading run of > and whitespace, the obvious way to
     remove a container's prefix, also removes the four-space indent and
     passes it.
"""
import re
import types

import mdformat
import mdformat.plugins as P
from markdown_it import MarkdownIt
from mdformat._util import is_md_equal


def pp(text, node, context):
    if node.parent is None or node.parent.type != "paragraph":
        return text
    return re.sub(r"\x00+", lambda m: "\n" if text[m.start() - 1] in ".!?" else " ", text)


P.PARSER_EXTENSIONS["probe"] = types.SimpleNamespace(
    CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS={"inline": pp},
    add_cli_argument_group=lambda g: None, update_mdit=lambda m: None)


def continuation(base):
    """Line number -> the prefix mdformat writes on a later line of the paragraph there."""
    prefix, stack = {}, []
    for tok in MarkdownIt("commonmark").parse(base):
        if tok.type == "blockquote_open":
            stack.append("> ")
        elif tok.type == "list_item_open":
            stack.append(" " * len(tok.info + tok.markup + " "))
        elif tok.type in ("blockquote_close", "list_item_close"):
            stack.pop()
        elif tok.type == "paragraph_open":
            for n in range(*tok.map):
                prefix[n] = "".join(stack)
    return prefix


def source_equal(base, plug, loose=False):
    prefix, b, p, i = continuation(base), base.splitlines(), plug.splitlines(), 0
    for n, line in enumerate(b):
        acc, i = p[i], i + 1
        while acc != line and n in prefix and i < len(p):
            rest = re.sub(r"^[>\s]+", "", p[i]) if loose else p[i].removeprefix(prefix[n])
            if not line.startswith(acc + " " + rest):
                break
            acc, i = acc + " " + rest, i + 1
        if acc != line:
            return False
    return i == len(p)


def fmt(src, exts, **opts):
    return mdformat.text(src, options={"wrap": "no", **opts}, extensions=exts)


CASES = [
    ("paragraph", "One here. Two here. Three here.\n", True),
    ("blockquote", "> One here. Two here. Three here.\n", True),
    ("nested blockquote", "> > One here. Two here.\n", True),
    ("bullet item", "- One here. Two here. Three here.\n", True),
    ("ordered item 10.", "10. One here. Two here.\n", True),
    ("numbered 9. and 10.", "9. One here. Two here.\n9. Three here. Four here.\n", True),
    ("second paragraph of an item", "- First.\n\n  One here. Two here.\n", True),
    ("list in blockquote", "> - One here. Two here.\n", True),
    ("blockquote in list", "- > One here. Two here.\n", True),
    ("hard break", "One here.\\\nTwo here. Three here.\n", True),
    ("HTML opener", "Do not use it. <div> is a block element.\n", False),
    ("HTML opener in an item", "- Do not use it. <div> is a block element.\n", False),
    ("dash", "It ends. - then a dash.\n", False),
    ("tilde run", "It ends. ~~~ more text after it.\n", False),
]
print(f"{'case':30}{'source':>8}{'render':>8}{'loose':>8}")
ok = True
for label, src, want in CASES:
    opts = {"number": True} if "numbered" in label else {}
    base, plug = fmt(src, set(), **opts), fmt(src, {"probe"}, **opts)
    got = source_equal(base, plug)
    loose = source_equal(base, plug, loose=True)
    ok &= got == want
    print(f"{label:30}{'pass' if got else 'FAIL':>8}{'pass' if is_md_equal(base, plug) else 'FAIL':>8}"
          f"{'pass' if loose else 'FAIL':>8}")
print(f"\nevery case as expected: {ok}")
