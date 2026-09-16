import re, types, mdformat, mdformat.plugins as P
SENT = re.compile(r'[.!?](?:["\'’”])?$')
CLAUSE = re.compile(r'[,;:—]$')          # rule 5's own punctuation

def make(mode):
    def pp(text, node, context):
        if node.parent is None or node.parent.type != "paragraph": return text
        parts, author = [], set()
        for c in node.children:
            if c.type == "softbreak": author.add(len("".join(parts)))
            parts.append(c.render(context))
        out, i = [], 0
        for m in re.finditer(r'\x00+', text):
            seg = text[i:m.start()]; out.append(seg)
            at = m.start() in author
            keep = bool(SENT.search(seg)) or (
                at if mode == "add-only" else (at and bool(CLAUSE.search(seg))))
            out.append("\n" if keep else " "); i = m.end()
        out.append(text[i:]); return "".join(out)
    return types.SimpleNamespace(CHANGES_AST=False, RENDERERS={},
        POSTPROCESSORS={"inline": pp}, add_cli_options=lambda p: None, update_mdit=lambda m: None)

P.PARSER_EXTENSIONS
CASES = {
 "hand-written sembr (clause breaks)":
   "Because the cascade picks by width,\nan edit upstream can change which candidate wins,\nand cascade down. Next sentence.\n",
 "hard-wrapped at ~62 cols (geometric)":
   "The quick brown fox jumps over the lazy dog and then keeps on\nrunning past the barn until it reaches the fence at the far\nend of the field. A second sentence follows.\n",
}
for label, src in CASES.items():
    print("="*66); print(label)
    for mode in ("add-only", "keep-clause-breaks-only"):
        P.PARSER_EXTENSIONS["probe"] = make(mode)
        o1 = mdformat.text(src, options={"wrap":"no"}, extensions={"probe"})
        o2 = mdformat.text(o1, options={"wrap":"no"}, extensions={"probe"})
        print(f"\n  [{mode}]  idempotent={o2==o1}")
        for line in o1.rstrip("\n").split("\n"): print("   |", line)
    print()
