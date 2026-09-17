import types, mdformat, mdformat.plugins as P
from mdformat.renderer import WRAP_POINT
ENDS = lambda s: s.rstrip().endswith((".","!","?"))
SRC = ("Because the cascade picks by width,\n"
       "an edit upstream can change which candidate wins. The tool reports success.\n")

def build(override_wrap, root_second_pass):
    state = {"depth": 0, "inline_calls": 0}
    def inline_pp(text, node, context):
        if node.parent is None or node.parent.type != "paragraph": return text
        state["inline_calls"] += 1
        if WRAP_POINT not in text: return text
        segs = text.split(WRAP_POINT); out=[segs[0]]
        for s in segs[1:]:
            out.append("\n" if ENDS(out[-1]) else " "); out.append(s)
        return "".join(out)
    def root_pp(text, node, context):
        if not root_second_pass or state["depth"]: return text
        state["depth"] += 1
        try:
            return mdformat.text(text.rstrip("\n"), options={"wrap":"keep"}, extensions={"probe"}).rstrip("\n")
        finally:
            state["depth"] -= 1
    post = {"inline": inline_pp}
    if root_second_pass: post["root"] = root_pp
    return types.SimpleNamespace(CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS=post,
        add_cli_options=lambda p: None,
        update_mdit=(lambda m: m.options["mdformat"].__setitem__("wrap","no")) if override_wrap else (lambda m: None)), state

P.PARSER_EXTENSIONS
print("reference: honest --wrap no, mdformat's own double render")
plug, st = build(False, False); P.PARSER_EXTENSIONS["probe"]=plug
ref = mdformat.text(SRC, options={"wrap":"no"}, extensions={"probe"})
print(f"   inline seam calls: {st['inline_calls']}")
print(f"   output: {ref!r}\n")

for label, rsp in (("route B alone (no second pass)", False),
                   ("route B + root postprocessor re-render", True)):
    plug, st = build(True, rsp); P.PARSER_EXTENSIONS["probe"]=plug
    out = mdformat.text(SRC, options={"wrap":"keep"}, extensions={"probe"})
    print(label)
    print(f"   inline seam calls: {st['inline_calls']}")
    print(f"   matches reference: {out == ref}")
    print(f"   output: {out!r}\n")

# The same three cases over a document that is not one bare paragraph, since
# the point of the re-render is the escaping and indentation that only blocks
# exercise. Also shows the trailing-newline caveat: the root postprocessor is
# handed already-finalised output, so re-rendering it finalises twice.
RICH = """Because the cascade picks by width, an edit upstream can change which candidate wins. The tool reports success.

- A list item. It has two sentences.
- Another item with one.

> A blockquote. Two sentences here too.

```python
x = 1  # a fenced block. Not prose.
```

Trailing paragraph. Second sentence.
"""

def build2(override, second, strip):
    st = {"depth": 0, "inline": 0}
    def inline_pp(text, node, context):
        if node.parent is None or node.parent.type != "paragraph": return text
        st["inline"] += 1
        if WRAP_POINT not in text: return text
        segs = text.split(WRAP_POINT); out = [segs[0]]
        for s in segs[1:]:
            out.append("\n" if ENDS(out[-1]) else " "); out.append(s)
        return "".join(out)
    def root_pp(text, node, context):
        if not second or st["depth"]: return text
        st["depth"] += 1
        try:
            src = text.rstrip("\n") if strip else text
            res = mdformat.text(src, options={"wrap": "keep"}, extensions={"probe"})
            return res.rstrip("\n") if strip else res
        finally:
            st["depth"] -= 1
    pp = {"inline": inline_pp}
    if second: pp["root"] = root_pp
    return types.SimpleNamespace(CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS=pp,
        add_cli_options=lambda p: None,
        update_mdit=(lambda m: m.options["mdformat"].__setitem__("wrap", "no"))
                    if override else (lambda m: None)), st

print("lists, blockquotes and a fenced block\n")
plug, st = build2(False, False, False); P.PARSER_EXTENSIONS["probe"] = plug
ref2 = mdformat.text(RICH, options={"wrap": "no"}, extensions={"probe"})
print(f"   reference, honest --wrap no  : inline calls {st['inline']}")
for label, ov, sec, strip in (
        ("route B alone               ", True, False, False),
        ("B + root re-render, no strip", True, True, False),
        ("B + root re-render, rstrip  ", True, True, True)):
    plug, st = build2(ov, sec, strip); P.PARSER_EXTENSIONS["probe"] = plug
    out = mdformat.text(RICH, options={"wrap": "keep"}, extensions={"probe"})
    print(f"   {label} : inline calls {st['inline']}  "
          f"matches reference {out == ref2}  ends {out[-3:]!r}")
print("""
   Route B alone already matches on both documents. The re-render restores
   the *pass*, not a known output difference: no input has been exhibited
   here where one pass and two disagree. mdformat runs two because escaping
   depends on wrapping (_api.py:35-40), so this is insurance.""")
