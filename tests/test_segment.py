"""Segmentation (section 3.1), inline atoms and bracket pairing
(section 3.2), pinning (section 3.4) and the failure policy
(section 3.6), unit by unit."""

from __future__ import annotations

import logging

from markdown_it import MarkdownIt
import mdformat
from mdformat.renderer import LOGGER, RenderTreeNode
import pytest

from _gate import WIDTHS, run
from mdformat_sentence import _plugin
from mdformat_sentence._segment import BACK_OFF, FALLBACK, locate, paragraph_parts, scan


@pytest.fixture
def decided(monkeypatch):
    """What the renderer handed to emission: (text, pieces) per paragraph."""
    seen = []
    decide = _plugin.decide

    def spy(text, pieces):
        seen.append((text, pieces))
        return decide(text, pieces)

    monkeypatch.setattr(_plugin, "decide", spy)

    def decided(md, extensions=()):
        seen.clear()
        mdformat.text(md, options={"wrap": "no"}, extensions=[*extensions, "sentence"])
        return seen[0]

    return decided


def segments(text, pieces):
    return [p.segments for p in paragraph_parts(text, pieces)]


def depths(text, pieces):
    return [scan(text, p).depth for p in paragraph_parts(text, pieces)]


def test_atoms_keep_their_punctuation(decided):
    text, pieces = decided("See `a b`. Next [x y](u).\n")
    assert segments(text, pieces) == [["See", "`a b`.", "Next", "[x y](u)."]]
    assert [(text[p.start : p.end], p.atom) for p in pieces] == [
        ("See\x00", False),
        ("`a b`", True),
        (".\x00Next\x00", False),
        ("[x y](u)", True),
        (".", False),
    ]


def test_containers_are_located_and_atoms_inside_them_kept_whole(decided):
    text, pieces = decided(
        "Read *the [docs](https://ex.com/a.b.)* and **`x.y`** first.\n"
    )
    assert [(text[p.start : p.end], p.type) for p in pieces] == [
        ("Read\x00", "text"),
        ("the\x00", "text"),
        ("[docs](https://ex.com/a.b.)", "link"),
        ("\x00and\x00", "text"),
        ("`x.y`", "code_inline"),
        ("\x00first.", "text"),
    ]


def test_a_run_of_wrap_points_keeps_its_length(decided):
    text, pieces = decided("w \\*\t\n  z. Then more.\n")
    assert "\x00\x00" in text
    (part,) = paragraph_parts(text, pieces)
    for start, segment in zip(part.starts, part.segments):
        assert text[start : start + len(segment)] == segment


def test_paragraph_parts_end_at_hard_breaks_only(decided):
    text, pieces = decided(
        'Raw <span\nclass="x">HTML</span> here. A [link\\\nbreak](u) and '
        '[a](u "x\ny"). Line\\\nTwo. And  \nthree.\n'
    )
    assert [s[-1] for s in segments(text, pieces)] == ["Line\\", "And\\", "three."]


@pytest.mark.parametrize(
    "md, expected",
    [
        # An unclosed opener adopted across a sentence end (section 3.2).
        ("It failed :(. Then came a) and b).", [0, 0, 1, 1, 1, 0, 0]),
        # Unpaired brackets count nothing.
        ("Step 1) first. Label 1(a is open.", [0, 0, 0, 0, 0, 0]),
        # A bracket in a URL or a code span is never counted.
        ("See [docs](https://x.y/a)b) and (`x)` first) go.", [0, 0, 0, 1, 0]),
        # Each kind pairs with its own.
        ("A (b [c) d] e.", [0, 1, 1, 0]),
    ],
)
def test_bracket_depth(decided, md, expected):
    assert depths(*decided(md + "\n")) == [expected]


def test_brackets_pair_within_a_paragraph_part(decided):
    assert depths(*decided("A ( b\\\nc ) d.\n")) == [[0, 0], [0, 0]]


def test_each_paragraph_part_gets_its_own_pieces(decided):
    # Atoms that end at a hard break and that open the next part.
    text, pieces = decided("A `x)`\\\n[l](u) (b\\\nc) `d` e.\n")
    parts = list(paragraph_parts(text, pieces))
    assert [
        [(p.type, text[p.start : p.end]) for p in part.pieces] for part in parts
    ] == [
        [("text", "A\x00"), ("code_inline", "`x)`")],
        [("link", "[l](u)"), ("text", "\x00(b")],
        [("text", "c)\x00"), ("code_inline", "`d`"), ("text", "\x00e.")],
    ]
    assert [scan(text, part).atoms for part in parts] == [
        [p for p in part.pieces if p.atom] for part in parts
    ]


def test_every_gap_is_pinned():
    md = "One long sentence that runs well past twenty columns. Then another.\n"
    for wrap in WIDTHS:
        out = mdformat.text(md, options={"wrap": wrap}, extensions={"sentence"})
        assert out == md


def test_plain_mdformat_fails_width_independence():
    """Section 6.1 is the first row that fails without the plugin
    (section 6.4)."""
    md = "One long sentence that runs well past twenty columns. Then another.\n"
    plain = [mdformat.text(md, options={"wrap": w}, extensions=set()) for w in WIDTHS]
    assert len(set(plain)) > 1


def test_the_recorder_is_not_installed_under_keep(monkeypatch):
    def refuse(*args):
        raise AssertionError("recorder installed")

    monkeypatch.setattr(_plugin, "Recording", refuse)
    md = "It ended. Then *it* began.\n"
    assert mdformat.text(md, extensions={"sentence"}) == md


@pytest.mark.parametrize(
    "md, plugins, fallback",
    [
        (
            "Read https://en.wikipedia.org/wiki/Foo_(bar) first.\n",
            ("gfm",),
            "gfm_autolink",
        ),
        (
            "Then [a link](u){: .cls } and more.\n",
            ("mkdocs",),
            "python_markdown_attr_list",
        ),
    ],
)
def test_a_container_that_hides_its_children_is_an_atom(md, plugins, fallback):
    for extensions in ((*plugins, "sentence"), ("sentence", *plugins)):
        result = run(md, extensions, "no")
        assert result.fallbacks == [fallback] * 2
        assert result.back_offs == 0


def test_a_container_located_more_than_once_is_an_atom(caplog):
    root = RenderTreeNode(MarkdownIt().parse("x *a* y\n"))
    inline = root.children[0].children[0]
    x, em, y = inline.children
    records = {id(x): "x ", id(em): "aa", id(em.children[0]): "a", id(y): " y"}
    with caplog.at_level(logging.DEBUG, logger=LOGGER.name):
        pieces = locate(inline, records, "x aa y")
    assert [(p.type, p.atom) for p in pieces] == [
        ("text", False),
        ("em", True),
        ("text", False),
    ]
    assert caplog.messages == [f"{FALLBACK}: em"]


def test_backs_off_when_records_do_not_add_up(monkeypatch, caplog):
    """The tripwire of section 3.6: a render that stops consulting the
    postprocessor map leaves every child unrecorded."""

    def render(self, context):
        return context.renderers[self.type](self, context)

    monkeypatch.setattr(RenderTreeNode, "render", render)
    md = "One long sentence that runs well past twenty columns. Then another.\n"
    with caplog.at_level(logging.DEBUG, logger=LOGGER.name):
        outs = {
            mdformat.text(md, options={"wrap": w}, extensions={"sentence"})
            for w in WIDTHS
        }
    assert outs == {md}
    assert BACK_OFF in caplog.messages
