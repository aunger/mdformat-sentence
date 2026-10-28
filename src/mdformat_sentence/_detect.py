"""Sentence detection (§3.3) and the safety checks (§3.5).

Section numbers refer to `DESIGN.md`.
"""

from __future__ import annotations

from bisect import bisect_right
from itertools import chain
import re
from typing import TYPE_CHECKING

from markdown_it.rules_block.html_block import HTML_SEQUENCES

from mdformat_sentence import _ucd

if TYPE_CHECKING:
    from mdformat_sentence._segment import Piece, State


def _chars(ranges) -> frozenset[str]:
    return frozenset(chr(c) for first, last in ranges for c in range(first, last + 1))


ATERMS = _chars(_ucd.ATERM)
STERMS = _chars(_ucd.STERM)
TERMINATORS = ATERMS | STERMS

# Each set's quotation marks, `¿` and `¡`, then its markup characters.
CLOSERS = frozenset("\"'’”»›«‹“‘‟‛„」』》〉" "*_~])")
OPENERS = frozenset("\"'’”“‘‟‛«‹»›¿¡„‚「『《〈" "*_~[(\\")
# The no-break spaces: `Zs` in UCD 18.0.0, less U+0020.
NBSP = frozenset("         "
                 "      　")
# What a lone mark is made of.
LONE = OPENERS | CLOSERS | NBSP

# A lone mark's role by shape: guillemets read the French way, and the
# right-hand curly quotes.
_SHAPE_OPENS = frozenset("«‹")
_SHAPE_CLOSES = frozenset("»›”’")

_FOOTNOTES = re.compile(r"(?:\[\^[^\]\s]+\])+\Z")

# The decision list's verdict that vetoes a gap.
NO = "no"

# Sentence_Break values, looked up in the vendored data and never through
# `str.isupper`, `str.islower` or `str.isalpha`.
UPPER, LOWER, OLETTER, NUMERIC, EXTEND = "Upper", "Lower", "OLetter", "Numeric", "Extend"
_TABLE = sorted(
    chain.from_iterable(
        ((first, last, value) for first, last in ranges)
        for value, ranges in (
            (UPPER, _ucd.UPPER),
            (LOWER, _ucd.LOWER),
            (OLETTER, _ucd.OLETTER),
            (NUMERIC, _ucd.NUMERIC),
            (EXTEND, _ucd.EXTEND),
        )
    )
)
_FIRSTS = [first for first, _, _ in _TABLE]

# What opens a sentence, and what may follow a camelCase word's first letter.
_OPENS = frozenset({UPPER, OLETTER, NUMERIC})
_WORD = frozenset({UPPER, LOWER, OLETTER, NUMERIC, EXTEND})

# The atoms that open a sentence whatever they hold, besides an autolink
# and raw inline HTML tags (§3.3).
_OPAQUE = frozenset({"code_inline", "image"})

# Lines mdformat 1.0.0's `paragraph()` escapes or indents by their start,
# and the three that do damage unescaped: a tilde fence, and a task box and
# a definition-list marker, which co-plugins escape (§3.5).
_LINE_START = re.compile(
    r"#{1,6}(?:[ \t]|\Z)|>|[-*+](?:[ \t]|\Z)|[0-9]+[.)](?:[ \t]|\Z)"
    r"|~~~|\[[ xX]\]|[:~] "
)
# What mdformat's `text()` escapes by its neighbors, unescaped only between
# whitespace when it stands alone (§3.5).
_NEIGHBORED = frozenset("*_")
_HTML_OPENERS = [opener for opener, _, interrupts in HTML_SEQUENCES if interrupts]


def sentence_break_value(char: str) -> str | None:
    """`char`'s Sentence_Break value, among those the capital test reads."""
    code = ord(char)
    i = bisect_right(_FIRSTS, code) - 1
    if i >= 0 and code <= _TABLE[i][1]:
        return _TABLE[i][2]
    return None


def is_lone(segment: str) -> bool:
    """Whether `segment` is a lone mark (§3.3)."""
    return bool(segment) and all(char in LONE for char in segment)


def is_sentence_break(segments: list[str], i: int, state: State) -> bool:
    """Whether the gap after `segments[i]` breaks (§3.3, §3.5).

    A run of lone marks is one gap, decided once for its two words, and
    the newline lands at one of its gaps or none.
    """
    words = state.words
    w = bisect_right(words, i) - 1
    if w < 0 or w + 1 == len(words):
        # No word before the gap, or none after it: a run that ends its
        # paragraph part never breaks.
        return False
    if w not in state.landings:
        state.landings[w] = _landing(segments, w, state)
    return state.landings[w] == i + 1


def _landing(segments: list[str], w: int, state: State) -> int | None:
    """The segment a newline between word `w` and the next word would
    precede, or `None` where no break is made."""
    starts = state.part.starts
    left, right = state.words[w], state.words[w + 1]
    terminator = sentence_end(segments[left], starts[left], state)
    if terminator is None:
        return None
    if terminator in ATERMS:
        before = segments[state.words[w - 1]] if w else ""
        if state.rules.verdict(segments[left], before, segments[right]) == NO:
            return None
    if not opens_sentence(segments[right], starts[right], state):
        return None
    at = next((k for k in range(left + 1, right) if _opens(segments, k, state)), right)
    if state.depth[at - 1] or not is_safe(segments, at, state):
        return None
    return at


def sentence_end(segment: str, start: int, state: State) -> str | None:
    """The terminator `segment` ends a sentence with, if it does: after the
    footnote strip, a terminator followed by closers and no-break spaces,
    standing outside every atom (§3.2, §3.3).

    `start` is the segment's offset in the paragraph's text.
    """
    end = len(segment)
    footnotes = _FOOTNOTES.search(segment)
    if footnotes is not None:
        end = footnotes.start()
    while end and (segment[end - 1] in CLOSERS or segment[end - 1] in NBSP):
        end -= 1
    if not end or segment[end - 1] not in TERMINATORS:
        return None
    if atom_at(state, start + end - 1) is not None:
        return None
    return segment[end - 1]


def opens_sentence(segment: str, start: int, state: State) -> bool:
    """The capital test, its two exemptions, and the opaque atoms that open
    a sentence whatever they hold (§3.3)."""
    j = 0
    tags = False
    while j < len(segment):
        atom = atom_at(state, start + j)
        if atom is not None and atom.type != "link":
            if atom.type in _OPAQUE:
                return True
            if atom.type == "html_inline":
                # Read raw HTML by what it holds.
                j = atom.end - start
                tags = True
                continue
            # A node of a type this plugin does not know opens nothing.
            return False
        if atom is not None and atom.start == start + j and segment[j] == "<":
            # An autolink; link text is words, read like any other.
            return True
        if segment[j] not in OPENERS and segment[j] not in NBSP:
            break
        j += 1
    else:
        # Nothing but raw inline HTML tags and opening markup.
        return tags
    value = sentence_break_value(segment[j])
    if value in _OPENS:
        return True
    if value == LOWER and _camel(segment, j):
        return True
    return state.rules.lowercase_name(segment)


def _camel(segment: str, j: int) -> bool:
    """Whether the lowercase letter at `j` begins a run of letters and
    digits with an `Upper` later in it: `iOS`, `gRPC`."""
    for char in segment[j + 1 :]:
        value = sentence_break_value(char)
        if value == UPPER:
            return True
        if value not in _WORD:
            return False
    return False


def _opens(segments: list[str], k: int, state: State) -> bool:
    """A lone mark's role, read from its first character (§3.3)."""
    char = segments[k][0]
    if char in _SHAPE_OPENS:
        return True
    if char in _SHAPE_CLOSES:
        return False
    opener, closer = char in OPENERS, char in CLOSERS
    if opener != closer:
        return opener
    start = state.part.starts[k - 1]
    return sentence_end(segments[k - 1], start, state) is None


def is_safe(segments: list[str], at: int, state: State) -> bool:
    """Edge safety and line-start safety (§3.5), for a newline before
    `segments[at]`."""
    before, after = segments[at - 1], segments[at]
    if not before[-1:].strip() or not after[:1].strip():
        return False
    starts = state.part.starts
    for char, offset in (
        (before[-1], starts[at - 1] + len(before) - 1),
        (after[0], starts[at]),
    ):
        if char in _NEIGHBORED:
            # A literal mark, which a text leaf holds; emphasis markup is
            # rendered by its container whatever stands beside it.
            piece = piece_at(state, offset)
            if piece is not None and not piece.atom:
                return False
    return not _escaped_at_line_start(segments, at)


def _escaped_at_line_start(segments: list[str], at: int) -> bool:
    """Whether some line a newline before `segments[at]` could open is one
    `paragraph()` escapes or indents, or one that opens a block unescaped.

    The line ends at a later break or at the paragraph part's end, which
    is not decided yet, so every place it could end is tested. Every
    pattern but the thematic break reads across one gap at most.
    """
    first = segments[at].split("\n", 1)[0]
    longer = " ".join(segments[at : at + 2]).split("\n", 1)[0]
    for line in (first, longer):
        if _LINE_START.match(line):
            return True
        if any(opener.search(line) for opener in _HTML_OPENERS):
            return True
    mark = first[:1]
    if not mark or first != mark * len(first):
        return False
    if mark in "-=":
        # A setext underline.
        return True
    if mark not in "*_":
        return False
    # A thematic break: three or more of one mark, spaced or not.
    count = 0
    for segment in segments[at:]:
        if segment != mark * len(segment) or not segment:
            break
        count += len(segment)
        if count >= 3:
            return True
    return False


def piece_at(state: State, at: int) -> Piece | None:
    """The piece holding offset `at` of the paragraph's text, if one does."""
    pieces = state.part.pieces
    i = bisect_right(state.piece_starts, at) - 1
    if i >= 0 and at < pieces[i].end:
        return pieces[i]
    return None


def atom_at(state: State, at: int) -> Piece | None:
    """The atom holding offset `at` of the paragraph's text, if one does."""
    piece = piece_at(state, at)
    return piece if piece is not None and piece.atom else None
