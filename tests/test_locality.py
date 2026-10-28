"""Section 6.2's locality row: one inserted word changes exactly one line.

A neutral word, plain and lowercase with no terminator, goes between two
words of one line of a paragraph, where neither neighbor carries a
terminator or is a lone mark, so it is never beside a gap a sentence end
could stand at and never directly before a word carrying a terminator
(§1), and neither carries markup the word could change the meaning of.
"""

from __future__ import annotations

from markdown_it import MarkdownIt
import mdformat
import pytest

from _gate import FIXTURES, orders, run
from mdformat_sentence._detect import TERMINATORS, is_lone
from test_gate import _absent

NEUTRAL = "quietly"
MARKUP = frozenset("[]()<>`\\*_~|$&!#")

# Paragraphs tried per fixture, spread over it, so the two long documents
# stay quick; §6.2 leaves the sample size open.
SAMPLE = 10

_PARSER = MarkdownIt("commonmark").enable("table")


def insertions(md: str) -> list[tuple[int, str]]:
    """One edited line per sampled paragraph of `md`: its index and text."""
    lines = md.split("\n")
    edits = []
    for token in _PARSER.parse(md):
        if token.type != "paragraph_open":
            continue
        candidates = []
        for i in range(*token.map):
            words = lines[i].split(" ")
            for k in range(len(words) - 1):
                if _neutral(words[k]) and _neutral(words[k + 1]):
                    candidates.append((i, " ".join([*words[: k + 1], NEUTRAL, *words[k + 1 :]])))
        if candidates:
            edits.append(candidates[len(candidates) // 2])
    if len(edits) > SAMPLE:
        edits = [edits[i * len(edits) // SAMPLE] for i in range(SAMPLE)]
    return edits


def _neutral(word: str) -> bool:
    """Whether a word may stand beside the inserted one."""
    return (
        bool(word)
        and not is_lone(word)
        and not any(c in TERMINATORS or c in MARKUP for c in word)
    )


@pytest.mark.parametrize(
    "md, extensions",
    [
        pytest.param(f.md, extensions, id=f"{f.name}-{'+'.join(extensions)}", marks=_absent(f))
        for f in FIXTURES
        for extensions in orders(f.plugins)
    ],
)
def test_locality(md, extensions):
    def fmt(text):
        return mdformat.text(text, options={"wrap": "no"}, extensions=list(extensions))

    before = run(md, extensions, "no").out
    reference = fmt(before).split("\n")
    edits = insertions(before)
    if not edits:
        pytest.skip("no line has two neighboring words a neutral word may join")
    for i, edited in edits:
        lines = before.split("\n")
        lines[i] = edited
        after = fmt("\n".join(lines)).split("\n")
        changed = [j for j, (a, b) in enumerate(zip(reference, after)) if a != b]
        assert len(after) == len(reference) and changed == [i], edited
        assert after[i] == edited
