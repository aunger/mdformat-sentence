"""The recorder: DESIGN.md §3.1's single-render atom map, against the re-render walk it replaced.

The plugin is the `inline` renderer (§2.2). Instead of rendering the children a second time to
learn where each piece sits, it renders them once, through a context whose postprocessor map ends
every node type's chain with a recorder that notes the node's final rendering and returns it
unchanged. Offsets come from the records: the top-level records concatenate to the text, and a
container's children are found by locating their joined records inside the container's record.
A node whose children were not rendered, or whose children cannot be located exactly once, is an
atom.

It establishes four things:
  1. the top-level records concatenate to the text the default inline renderer returns, and the
     pieces match what a re-render walk reports on ordinary input, atoms nested in emphasis included;
  2. the recorder adds no render of its own, where the walk renders the paragraph's children again;
  3. on the escaped-reference input of finding #3 both are consistent: the walk because it renders
     again against a copy of the state, the recorder because it renders nothing a second time;
  4. mdformat-gfm's bare URL renders its source and never its `text` child: the walk cannot find the
     child inside it and backs off, while the recorder sees no child record and makes it an atom.
Needs mdformat 1.0.0 and mdformat-gfm 1.0.0.
"""
import types

import mdformat
import mdformat.plugins as P
from mdformat.renderer import DEFAULT_RENDERERS, RenderTreeNode

KNOWN_ATOMS = {"link", "image", "code_inline", "html_inline"}
CALLS = {"render": 0}
SEEN = []
_render = RenderTreeNode.render


def counted_render(self, context):
    CALLS["render"] += 1
    return _render(self, context)


RenderTreeNode.render = counted_render


class Recording:
    """A postprocessor map that appends `record` to every node type's chain."""

    def __init__(self, inner, record):
        self.inner, self.record = inner, record

    def get(self, key, default=()):
        return tuple(self.inner.get(key, default)) + (self.record,)


def pieces(node, records, start):
    """(start, end, type, kind) for every piece under `node`, from the records alone."""
    out = []
    for child in node.children:
        text = records.get(id(child))
        if text is None:
            return None
        kinds = []
        if child.children and child.type not in KNOWN_ATOMS:
            joined = "".join(records.get(id(c), "\0missing") for c in child.children)
            if all(id(c) in records for c in child.children) and text.count(joined) == 1:
                kinds = pieces(child, records, start + text.index(joined))
        if kinds:
            out += kinds
        else:
            kind = "prose" if child.type == "text" else "atom"
            out.append((start, start + len(text), child.type, kind))
        start += len(text)
    return out


def recorder_hook(node, context):
    if node.parent is None or node.parent.type != "paragraph":
        return DEFAULT_RENDERERS["inline"](node, context)
    records = {}

    def record(text, n, ctx):
        records[id(n)] = text
        return text

    ctx = context._replace(postprocessors=Recording(context.postprocessors, record))
    text = DEFAULT_RENDERERS["inline"](node, ctx)
    top = "".join(records.get(id(c), "") for c in node.children)
    SEEN.append(("recorder", text, top == text, pieces(node, records, 0)))
    return text


def walk_hook(node, context):
    """The re-render walk this replaced, with the env copy, reduced to the top-level sum."""
    if node.parent is None or node.parent.type != "paragraph":
        return DEFAULT_RENDERERS["inline"](node, context)
    env = {**context.env, "used_refs": set(context.env["used_refs"])}
    text = DEFAULT_RENDERERS["inline"](node, context)
    again = context._replace(env=env)
    rendered = [c.render(again) for c in node.children]
    containers_found = all(
        "".join(g.render(again) for g in c.children) in r
        for c, r in zip(node.children, rendered) if c.children and c.type not in KNOWN_ATOMS)
    SEEN.append(("walk", text, sum(map(len, rendered)) == len(text) and containers_found, None))
    return text


def plugin(renderer):
    return types.SimpleNamespace(CHANGES_AST=False, RENDERERS={"inline": renderer},
                                 POSTPROCESSORS={}, update_mdit=lambda m: None)


P.PARSER_EXTENSIONS["rec"] = plugin(recorder_hook)
P.PARSER_EXTENSIONS["walk"] = plugin(walk_hook)


def run(md, ext):
    SEEN.clear()
    mdformat.text(md, extensions=ext, options={"wrap": "no"})
    return SEEN[0]


print("1. Pieces from the records\n")
md = "Read *the [docs](https://ex.com/a.b.)* and `x.y` first. Then go.\n"
name, text, adds_up, ps = run(md, ["rec"])
print(f"   text {text!r}\n   top-level records add up: {adds_up}")
for s, e, t, k in ps:
    print(f"   {s:3}-{e:<3} {t:12} {k:5} {text[s:e]!r}")
print()

print("2. Node renders for one document, both passes: the walk renders the paragraph's children again\n")
for hook in ("rec", "walk"):
    CALLS["render"] = 0
    mdformat.text("One *two* three. Four `five`.\n", extensions=[hook], options={"wrap": "no"})
    print(f"   {hook:5} {CALLS['render']} calls to RenderTreeNode.render")
print()

print("3. Finding #3's input\n")
md = "It cites \\[foo\\] early. Then [a link][foo] later.\n\n[foo]: https://x.y\n"
for hook in ("rec", "walk"):
    name, text, ok, _ = run(md, [hook])
    print(f"   {name:8} consistent: {ok}")
print()

print("4. A gfm bare URL whose source differs from its child's rendering\n")
md = "Read https://en.wikipedia.org/wiki/Foo_(bar) first. Then go.\n"
for hook in ("rec", "walk"):
    name, text, ok, ps = run(md, ["gfm", hook])
    print(f"   {name:8} consistent: {ok}")
    if ps:
        print("            " + ", ".join(f"{t}:{k}" for _, _, t, k in ps))
