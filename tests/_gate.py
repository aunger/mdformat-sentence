"""The harness behind the rows of section 6.2: fixtures, load orders and one
instrumented render per input, order and width."""

from __future__ import annotations

from functools import lru_cache
import logging
from pathlib import Path
import re
from typing import NamedTuple

import mdformat
from mdformat.renderer import DEFAULT_RENDERERS, LOGGER, WRAP_POINT

import mdformat_sentence
from mdformat_sentence import _plugin, _segment
from mdformat_sentence._segment import BACK_OFF, FALLBACK, Piece

ROOT = Path(__file__).resolve().parent.parent

# Section 6.1's widths.
WIDTHS = ("no", 20, 40, 80, 120, 1000)


class Fixture(NamedTuple):
    name: str
    # `None` where the file it is read from is absent (`_read`).
    md: str | None
    plugins: tuple[str, ...] = ()


def _read(path: str) -> str | None:
    """A repository file, or `None` where it is absent: the sdist ships
    `tests/` without `DESIGN.md` and `notes/`."""
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


FIXTURES = [
    Fixture(
        "sentences",
        "One long sentence that runs well past twenty columns. Then another.\n",
    ),
    Fixture(
        "containers",
        "Read *the [docs](https://ex.com/a.b.)* and `x.y` first. "
        "Then **go *now* (or `never`)** and *a* b *c*. End.\n",
    ),
    Fixture("strikethrough", "It was ~~not done. Then~~ done. Then more.\n", ("gfm",)),
    Fixture(
        "atoms",
        'See `a b`. Next [x y](u). An ![image of it](i.png "a title") here. '
        "A badge [![b](i)](t) too. <https://x.y/a)b> is one atom. "
        'Then <em class="x">raw</em> HTML.\n',
    ),
    Fixture(
        "newlines in atoms",
        'Raw <span\nclass="x">HTML</span> here. Then a link [a\\\nb](u) with a break. '
        'Then [a](u "x\ny") with a title. End.\n',
    ),
    Fixture(
        "hard breaks",
        "Line one. Line one ends\\\nLine two. Then more  \nLine three. foo. \\\nbar.\n",
    ),
    Fixture("a run of wrap points", "w \\*\t\n  z. Then more.\n"),
    Fixture(
        "brackets",
        "It failed :(. Then came a) and b). One ( fine day. A b. C d. E 1) f. "
        "Label 1(a is open. (A whole sentence.) [Another one.] End.\n",
    ),
    Fixture(
        "containers of blocks",
        "> Quoted. Then more.\n>\n> - A list item. With two sentences.\n"
        ">   1. Nested. Numbered, too.\n\n"
        "- First. Item.\n\n  Second paragraph. Of the item.\n\n"
        "10. Ten. Wide marker.\n",
    ),
    Fixture(
        "references",
        "It cites \\[foo\\] early. Then [a link][foo] later.\n\n[foo]: https://x.y\n",
    ),
    # Section 6.4's hook-point fixtures that pinning alone can decide.
    *(
        Fixture(
            f"gfm url {url}",
            f"Read https://en.wikipedia.org/wiki/{url} first. Then go.\n",
            ("gfm",),
        )
        for url in ("Foo_(bar)", "Foo__bar__", "Foo*bar*")
    ),
    Fixture(
        "mkdocs attribute list",
        "A sentence here. Then [a link](u){: .cls } and more. End.\n",
        ("mkdocs",),
    ),
    Fixture(
        "gfm task item",
        "- [ ] Mr. Smith left early. Then he came back.\n",
        ("gfm",),
    ),
    Fixture(
        "mkdocs nested list item",
        "- item\n  - A nested list item that is longer than the width. "
        "It has two sentences in it.\n",
        ("mkdocs",),
    ),
    Fixture(
        "footnote reference",
        "The matter at hand.[^1] This is next.\n\n[^1]: A note. With two sentences.\n",
        ("footnote",),
    ),
    # Section 6.4's fixtures from Panache.
    Fixture(
        "inline list markers",
        "Hear from us in 60 days. 1. Tell us your name. 2. Describe the error.\n",
    ),
    Fixture(
        "one long sentence",
        "This one sentence runs on for eighty-eight columns without any interior terminator in it\n",
    ),
    Fixture("a trailing newline", "Only one sentence.\n"),
    # The corpus, and the dogfood as section 6.2 loads it.
    Fixture("sembr.md", _read("notes/corpus/sembr.md")),
    Fixture("sembr.md with gfm", _read("notes/corpus/sembr.md"), ("gfm",)),
    Fixture("DESIGN.md", _read("DESIGN.md"), ("gfm",)),
]


def orders(plugins: tuple[str, ...]) -> list[tuple[str, ...]]:
    """The co-plugins loaded before the plugin and after it (section 6.2)."""
    if not plugins:
        return [("sentence",)]
    return [(*plugins, "sentence"), ("sentence", *plugins)]


class Run(NamedTuple):
    out: str
    # (mdformat's rendering, the plugin's) for each paragraph's inline node
    pairs: list[tuple[str, str]]
    # (mdformat's rendering, `locate`'s pieces) for each paragraph located
    located: list[tuple[str, list[Piece]]]
    back_offs: int
    fallbacks: list[str]
    # How often anything listed the recording map's keys or length
    # (section 3.1), as a copy of it would
    listed: int


class _Messages(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.messages: list[str] = []

    def emit(self, record):
        self.messages.append(record.getMessage())


@lru_cache(maxsize=None)
def run(md: str, extensions: tuple[str, ...], wrap) -> Run:
    """Format `md` once, recording what the plugin was given and returned
    for each paragraph, and what it logged."""
    renderer = mdformat_sentence.RENDERERS["inline"]
    default = DEFAULT_RENDERERS["inline"]
    given: list[str] = []
    pairs: list[tuple[str, str]] = []
    located: list[tuple[str, list[Piece]]] = []
    listed = [0]
    locate = _plugin.locate
    recording = _segment.Recording

    def spy(node, context):
        text = default(node, context)
        given.append(text)
        return text

    def spy_locate(node, records, text):
        pieces = locate(node, records, text)
        if pieces is not None:
            located.append((text, pieces))
        return pieces

    class Listed(recording):
        def __iter__(self):
            listed[0] += 1
            return super().__iter__()

        def __len__(self):
            listed[0] += 1
            return super().__len__()

    def wrapper(node, context):
        given.clear()
        out = renderer(node, context)
        if node.parent is not None and node.parent.type == "paragraph":
            (text,) = given
            pairs.append((text, out))
        return out

    handler = _Messages()
    level = LOGGER.level
    # The plugin reads mdformat's renderers through its module global,
    # and mdformat's own map is read-only.
    _plugin.DEFAULT_RENDERERS = {**DEFAULT_RENDERERS, "inline": spy}
    mdformat_sentence.RENDERERS["inline"] = wrapper
    _plugin.locate = spy_locate
    _plugin.Recording = Listed
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.DEBUG)
    try:
        out = mdformat.text(md, options={"wrap": wrap}, extensions=list(extensions))
    finally:
        _plugin.DEFAULT_RENDERERS = DEFAULT_RENDERERS
        mdformat_sentence.RENDERERS["inline"] = renderer
        _plugin.locate = locate
        _plugin.Recording = recording
        LOGGER.removeHandler(handler)
        LOGGER.setLevel(level)
    prefix = f"{FALLBACK}: "
    return Run(
        out,
        pairs,
        located,
        handler.messages.count(BACK_OFF),
        [m[len(prefix) :] for m in handler.messages if m.startswith(prefix)],
        listed[0],
    )


@lru_cache(maxsize=None)
def baseline(md: str, plugins: tuple[str, ...], wrap) -> str:
    """Plain mdformat with the same co-plugins, named explicitly
    (section 6.2)."""
    return mdformat.text(md, options={"wrap": wrap}, extensions=set(plugins))


def preserves(given: str, out: str) -> bool:
    """Whether `out` is `given` with each run of wrap points replaced by
    one newline or one space (section 6.2's text-preservation row)."""
    # Independent of `_segment._RUN`, so the row can catch a fault in it.
    parts = re.split(f"{re.escape(WRAP_POINT)}+", given)
    return re.fullmatch("[\n ]".join(map(re.escape, parts)), out) is not None
