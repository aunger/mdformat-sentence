import re, types, mdformat, mdformat.plugins as P
from mdformat.renderer import WRAP_POINT

SENT = re.compile(r'[.!?](?:["\'’”])?$')

def make(add_only):
    def pp(text, node, context):
        if node.parent is None or node.parent.type != "paragraph":
            return text
        # rebuild the rendered string per child, marking author softbreaks
        parts, author = [], set()
        for child in node.children:
            if child.type == "softbreak":
                author.add(len("".join(parts)))      # offset of this wrap point
            parts.append(child.render(context))
        rebuilt = "".join(parts)
        assert rebuilt == text, (rebuilt, text)
        out, i = [], 0
        for m in re.finditer(r'\x00+', text):
            seg = text[i:m.start()]
            out.append(seg)
            keep = SENT.search(seg) or (add_only and m.start() in author)
            out.append("\n" if keep else " ")
            i = m.end()
        out.append(text[i:])
        return "".join(out)
    return types.SimpleNamespace(CHANGES_AST=False, RENDERERS={},
        POSTPROCESSORS={"inline": pp},
        add_cli_argument_group=lambda g: None, update_mdit=lambda m: None)

P.PARSER_EXTENSIONS
SRC = ("Because the cascade picks by width,\n"
       "an edit upstream can change which candidate wins,\n"
       "and cascade down. The next sentence starts here and runs on a while.\n")
print("SOURCE\n" + SRC)
for name, ao in (("sentence-only", False), ("ADD-ONLY", True)):
    P.PARSER_EXTENSIONS["probe"] = make(ao)
    o1 = mdformat.text(SRC, options={"wrap": "no"}, extensions={"probe"})
    o2 = mdformat.text(o1,  options={"wrap": "no"}, extensions={"probe"})
    o80 = mdformat.text(SRC, options={"wrap": 80}, extensions={"probe"})
    print(f"=== {name} ===")
    print(o1)
    print("  idempotent (re-run):", o2 == o1)
    print("  width-independent (no vs 80):", o80 == o1)
    print()

print("#" * 60)
P.PARSER_EXTENSIONS["probe"] = make(True)
HARD = ("The quick brown fox jumps over the lazy dog and then keeps on\n"
        "running past the barn until it reaches the fence at the far\n"
        "end of the field. A second sentence follows it here.\n")
print("A file someone hard-wrapped at ~62 columns:\n" + HARD)
print("--- add-only output ---")
print(mdformat.text(HARD, options={"wrap": "no"}, extensions={"probe"}))

print("--- same text, two layouts ---")
A = "One sentence that is fairly long and keeps going for a while here.\n"
B = "One sentence that is fairly long\nand keeps going for a while here.\n"
oa = mdformat.text(A, options={"wrap": "no"}, extensions={"probe"})
ob = mdformat.text(B, options={"wrap": "no"}, extensions={"probe"})
print("  layout A ->", repr(oa))
print("  layout B ->", repr(ob))
print("  same output for same text:", oa == ob)
