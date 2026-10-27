"""Segmentation (§3.1), inline atoms (§3.2), emission (§3.4) and the
failure policy (§3.6).

Section numbers refer to `DESIGN.md`.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections.abc import Callable, Iterator, Mapping
from itertools import accumulate
import re
from typing import TYPE_CHECKING, NamedTuple

from mdformat.renderer import LOGGER, WRAP_POINT

if TYPE_CHECKING:
    from mdformat.renderer import RenderTreeNode
    from mdformat.renderer.typing import Postprocess

BACK_OFF = "mdformat-sentence backed off a paragraph"
FALLBACK = "mdformat-sentence made an atom by fallback"

# Recorded whole, children and all (§3.2). Autolinks are links.
ATOMS = frozenset({"link", "image"})
# Leaves that are neither prose nor atoms: a soft break is a gap, and a
# hard break's newline ends a paragraph part.
BREAKS = frozenset({"softbreak", "hardbreak"})

_RUN = re.compile(f"({re.escape(WRAP_POINT)}+)")
_OPENERS = {")": "(", "]": "["}


class Recording(Mapping):
    """A postprocessor map that appends one recorder, last, to the chain
    of every node type (§3.1)."""

    def __init__(self, inner: Mapping[str, tuple[Postprocess, ...]], record):
        self._inner = inner
        self._record = record
        self._chains: dict[str, tuple[Postprocess, ...]] = {}

    def __getitem__(self, key: str) -> tuple[Postprocess, ...]:
        chain = self._chains.get(key)
        if chain is None:
            chain = self._chains[key] = (*self._inner.get(key, ()), self._record)
        return chain

    def __iter__(self) -> Iterator[str]:
        return iter(self._inner)

    def __len__(self) -> int:
        return len(self._inner)


class Piece(NamedTuple):
    """A located rendering: prose (a `text` leaf) or an atom."""

    start: int
    end: int
    type: str
    atom: bool


class ParagraphPart(NamedTuple):
    """The inline text between hard breaks (§3.1), split at its wrap points.

    `starts[i]` is the offset of `segments[i]` in the paragraph's text,
    so the gap after segment `i` begins at `starts[i] + len(segments[i])`.
    """

    segments: list[str]
    starts: list[int]


class State(NamedTuple):
    """Section 3.3's cross-segment facts about one paragraph part."""

    atoms: list[Piece]
    depth: list[int]


def locate(
    node: RenderTreeNode, records: dict[int, str], text: str
) -> list[Piece] | None:
    """The pieces under `node`, or `None` when its top-level records do
    not concatenate to `text` (§3.6)."""
    if _joined(node, records) != text:
        return None
    pieces: list[Piece] = []
    _locate(node, records, 0, pieces)
    return pieces


def _locate(node, records, start, pieces) -> None:
    for child in node.children:
        rendered = records[id(child)]
        end = start + len(rendered)
        if child.type == "text":
            pieces.append(Piece(start, end, child.type, False))
        elif child.type in BREAKS:
            pass
        elif not child.children or child.type in ATOMS:
            pieces.append(Piece(start, end, child.type, True))
        else:
            at = _find_children(child, records, rendered)
            if at is None:
                LOGGER.debug("%s: %s", FALLBACK, child.type)
                pieces.append(Piece(start, end, child.type, True))
            else:
                _locate(child, records, start + at, pieces)
        start = end


def _find_children(node, records, rendered: str) -> int | None:
    """Where the children's joined records lie in `rendered`, if they
    were all rendered and lie there exactly once."""
    joined = _joined(node, records)
    if joined is None:
        return None
    at = rendered.find(joined)
    if at < 0 or rendered.find(joined, at + 1) >= 0:
        return None
    return at


def _joined(node, records) -> str | None:
    """The children's records joined, or `None` if one was not rendered."""
    if any(id(c) not in records for c in node.children):
        return None
    return "".join(records[id(c)] for c in node.children)


def paragraph_parts(text: str, pieces: list[Piece]) -> Iterator[ParagraphPart]:
    """Split at every newline outside an atom (§3.1), then at wrap points,
    keeping each run's length in the offsets (§2.3)."""
    inside = _atom_test(pieces)
    begin = 0
    for end in [*(m.start() for m in re.finditer("\n", text)), len(text)]:
        if end < len(text) and inside(end):
            continue
        split = _RUN.split(text[begin:end])
        starts = list(accumulate(map(len, split), initial=begin))
        yield ParagraphPart(split[0::2], starts[0::2])
        begin = end + 1


def _atom_test(pieces: list[Piece]) -> Callable[[int], bool]:
    atoms = [p for p in pieces if p.atom]
    starts = [p.start for p in atoms]

    def inside(at: int) -> bool:
        i = bisect_right(starts, at) - 1
        return i >= 0 and at < atoms[i].end

    return inside


def scan(text: str, part: ParagraphPart, pieces: list[Piece]) -> State:
    """Section 3.3's facts, computed once per paragraph part: the atoms in it,
    and the bracket depth at each gap (§3.2)."""
    first = part.starts[0]
    last = part.starts[-1] + len(part.segments[-1])
    inside = [p for p in pieces if p.start < last and p.end > first]
    gaps = [s + len(seg) for s, seg in zip(part.starts, part.segments)][:-1]
    depth = [0] * len(gaps)
    for opened, closed in _pairs(text, [p for p in inside if not p.atom], first, last):
        for i in range(bisect_right(gaps, opened), bisect_left(gaps, closed)):
            depth[i] += 1
    return State([p for p in inside if p.atom], depth)


def _pairs(text: str, prose: list[Piece], first: int, last: int):
    """Pair prose brackets, each closer with the nearest earlier unpaired
    opener of its kind; a bracket left unpaired counts nothing (§3.2)."""
    stacks: dict[str, list[int]] = {"(": [], "[": []}
    for piece in prose:
        for at in range(max(piece.start, first), min(piece.end, last)):
            char = text[at]
            if char in stacks:
                stacks[char].append(at)
            elif char in _OPENERS and stacks[_OPENERS[char]]:
                yield stacks[_OPENERS[char]].pop(), at


def is_sentence_break(segments: list[str], i: int, state: State) -> bool:
    """Whether the gap after `segments[i]` breaks (§3.3, §3.5).

    Until sentence detection lands, no gap breaks.
    """
    return False


def decide(text: str, pieces: list[Piece]) -> str:
    """Resolve every gap to a newline or a literal space (§3.4)."""
    out = []
    for part in paragraph_parts(text, pieces):
        segments = part.segments
        state = scan(text, part, pieces)
        emit = [segments[0]]
        for i in range(len(segments) - 1):
            emit.append("\n" if is_sentence_break(segments, i, state) else " ")
            emit.append(segments[i + 1])
        out.append("".join(emit))
    return "\n".join(out)


def back_off(text: str) -> str:
    """Emit no break at all: every run of wrap points becomes one space
    (§3.6)."""
    LOGGER.debug(BACK_OFF)
    return _RUN.sub(" ", text)
