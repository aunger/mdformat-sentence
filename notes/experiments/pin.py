"""Pinning: DESIGN.md section 3.4's width-independence claim, run.

Two throwaway `inline` postprocessors break after every [.!?] at a wrap
point. The *pinned* one turns every other wrap point into a literal space,
which is section 3.4's rule; the *unpinned* one leaves them for mdformat's own
word wrap. A paragraph that is one 140-character sentence shows the
difference: pinned, it survives intact at --wrap 80 and the output is
byte-identical to --wrap no; unpinned, mdformat wraps it into two lines.

Needs mdformat 1.0.0.
"""
import re
import types

import mdformat
import mdformat.plugins as P


def make(pin):
    def pp(text, node, context):
        if node.parent is None or node.parent.type != "paragraph":
            return text

        def gap(m):
            if text[m.start() - 1] in ".!?":
                return "\n"
            return " " if pin else m.group()

        return re.sub(r"\x00+", gap, text)

    return types.SimpleNamespace(
        CHANGES_AST=False, RENDERERS={}, POSTPROCESSORS={"inline": pp},
        add_cli_argument_group=lambda g: None, update_mdit=lambda m: None)


SRC = ("The committee reviewed each submission it had received during the "
       "autumn cycle and found that nearly all of them followed the written "
       "rules.\n")
assert len(SRC.rstrip("\n")) == 140, len(SRC.rstrip("\n"))

for name, pin in (("pinned", True), ("unpinned", False)):
    P.PARSER_EXTENSIONS["probe"] = make(pin)
    at_no = mdformat.text(SRC, options={"wrap": "no"}, extensions={"probe"})
    at_80 = mdformat.text(SRC, options={"wrap": 80}, extensions={"probe"})
    print(f"=== {name} ===")
    print(f"--wrap no : {[len(l) for l in at_no.splitlines()]} characters per line")
    print(f"--wrap 80 : {[len(l) for l in at_80.splitlines()]} characters per line")
    print(f"identical : {at_no == at_80}")
    print(at_80)
