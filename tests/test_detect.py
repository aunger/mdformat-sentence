"""Sentence detection (section 3.3) and the safety checks (section 3.5):
section 6.4's fixtures, the interface the rules files implement, and the
hand-written fixture pairs that section 6.2's minimality row asks of the
checks in code."""

from __future__ import annotations

import re

import mdformat
from mdformat._util import is_md_equal
import pytest

from _detection import DETECTION
from _gate import orders, run
from mdformat_sentence import _detect, _plugin, _segment
from mdformat_sentence._rules import ALLOW, NO, STUB


def plugin(md, extensions=()):
    return mdformat.text(md, options={"wrap": "no"}, extensions=[*extensions, "sentence"])


def plain(md, extensions=()):
    return mdformat.text(md, options={"wrap": "no"}, extensions=set(extensions))


@pytest.mark.parametrize(
    "case, extensions",
    [
        pytest.param(case, extensions, id=f"{case.name}-{'+'.join(extensions)}")
        for case in DETECTION
        for extensions in orders(case.plugins)
    ],
)
def test_detection(case, extensions):
    assert run(case.md, extensions, "no").out == case.expected


class Recorded:
    """Rules that record what they are asked and answer from a table."""

    def __init__(self, no=(), names=False):
        self.no = set(no)
        self.names = names
        self.verdicts = []
        self.lowercase = []

    def verdict(self, at, before, after):
        self.verdicts.append((at, before, after))
        return NO if at in self.no else ALLOW

    def lowercase_name(self, word):
        self.lowercase.append(word)
        return self.names


@pytest.fixture
def rules(monkeypatch):
    """Format with the rules given rather than the stub."""

    def format_with(rules, md, extensions=()):
        monkeypatch.setattr(_plugin, "STUB", rules)
        return plugin(md, extensions)

    return format_with


# `mdformat.text` renders twice (section 2.3), so every question is asked
# twice.


def test_the_verdict_is_asked_at_every_candidate_gap_after_aterm(rules):
    recorded = Recorded()
    rules(recorded, "Dr. Who came! Then it ended. then more. Yes? No.\n")
    assert recorded.verdicts == 2 * [
        ("Dr.", "", "Who"),
        ("ended.", "it", "then"),
        ("more.", "then", "Yes?"),
    ]


def test_the_verdict_reads_words_past_runs_of_lone_marks(rules):
    recorded = Recorded()
    rules(recorded, "« Dr. » Smith said. « Then » he left.\n")
    assert recorded.verdicts == 2 * [("Dr.", "", "Smith"), ("said.", "Smith", "Then")]


def test_before_is_empty_at_the_start_of_a_paragraph_part(rules):
    recorded = Recorded()
    rules(recorded, "One a.\\\nB. Then more.\n")
    assert recorded.verdicts == 2 * [("B.", "", "Then")]


def test_a_verdict_of_no_vetoes_and_allow_defers(rules):
    md = "Ask Dr. Smith. Then go.\n"
    assert rules(Recorded(no={"Dr."}), md) == "Ask Dr. Smith.\nThen go.\n"
    assert rules(Recorded(), md) == "Ask Dr.\nSmith.\nThen go.\n"
    # `allow` is not a break.
    assert rules(Recorded(), "It ended. then more.\n") == "It ended. then more.\n"


def test_lowercase_names_receives_the_raw_word_after_the_gap(rules):
    md = "It ended. (npm) runs it.\n"
    recorded = Recorded()
    assert rules(recorded, md) == md
    assert recorded.lowercase == 2 * ["(npm)"]
    assert rules(Recorded(names=True), md) == "It ended.\n(npm) runs it.\n"


def test_the_stub():
    assert STUB.verdict("Dr.", "Ask", "Smith") == ALLOW
    for word in ("mdformat", "mdformat's", "(mdformat-gfm", "“mdformat.”"):
        assert STUB.lowercase_name(word), word
    for word in ("npm", "Mdformat", "xmdformat"):
        assert not STUB.lowercase_name(word), word


# Openings that only a broad `lowercase_names` pattern lets through the
# capital test, and those that section 3.5's line-start check alone refuses.
LINE_STARTS = [
    "It ended. # Then more.",
    "It ended. ###### Then more.",
    "It ended. >Then more.",
    "It ended. - Then more.",
    "It ended. + Then more.",
    "It ended. 1. Then more.",
    "It ended. 12) Then more.",
    "It ended. ===",
    "It ended. ---",
    "It ended. <div> more.",
    "It ended. <!-- x --> more.",
    "It ended. <pre> more.",
    "It ended. ~~~Then more.",
    'It ended. " ~ Then more.',
    "It ended. : Then more.",
]


@pytest.mark.parametrize("md", LINE_STARTS)
def test_line_start_safety(rules, monkeypatch, md):
    """Each break the check refuses would change the source: undoing the
    plugin's breaks gives plain mdformat's output only with the check."""
    everything = Recorded(names=True)
    md += "\n"
    out = rules(everything, md)
    assert out.replace("\n", " ")[:-1] + "\n" == plain(md)
    monkeypatch.setattr(_detect, "_escaped_at_line_start", lambda *_: False)
    assert rules(everything, md) != out


def _rendered_alike(md, out, extensions):
    return is_md_equal(md, out, options={"wrap": "no"}, extensions=list(extensions))


@pytest.mark.parametrize(
    "md",
    [
        "Sentence one. *[HTML]: Hyper Text Markup Language is the term.",
        "Sentence one. *[Hyper Text]: is a phrase defined here.",
    ],
)
def test_the_definition_veto_keeps_mkdocs_from_reading_a_definition(md, monkeypatch):
    """Without the veto, mkdocs reads an abbreviation definition where the
    source had text, and the render changes (section 3.5)."""
    md += "\n"
    assert plugin(md, ["mkdocs"]) == plain(md, ["mkdocs"])
    monkeypatch.setattr(_detect, "_DEFINITION", re.compile("(?!)"))
    assert not _rendered_alike(md, plugin(md, ["mkdocs"]), ["mkdocs"])


@pytest.mark.parametrize(
    "md",
    ["Sentence one. [Foo]: Not a definition either.", "It ended. (Label)= Then more."],
)
def test_the_definition_veto_applies_without_the_co_plugin(md, monkeypatch):
    """With no co-plugin loaded these breaks would render the same; the veto
    refuses them anyway, and nothing else does."""
    md += "\n"
    assert plugin(md) == plain(md)
    monkeypatch.setattr(_detect, "_DEFINITION", re.compile("(?!)"))
    assert "\n" in plugin(md)[:-1]


@pytest.mark.parametrize(
    "md",
    [
        "[ a. Then [Foo]: bar",
        "\\[Foo Dr. Yes! [ ] [Foo]: \\ Yes! 1. Then more.",
    ],
)
def test_a_paragraph_opening_with_an_escaped_bracket_keeps_its_lines(md, monkeypatch):
    """mdformat-mkdocs reads a paragraph opening with `\\[` as display math,
    whole or in part, by where its `\\]` falls among its lines, and drops
    text doing so (section 3.5)."""
    md += "\n"
    assert plugin(md, ["mkdocs"]) == plain(md, ["mkdocs"])
    monkeypatch.setattr(_segment, "is_math", lambda text: False)
    assert not _rendered_alike(plain(md, ["mkdocs"]), plugin(md, ["mkdocs"]), ["mkdocs"])


@pytest.mark.parametrize("md", ["It ended. :-:", "It ended. |-|", "It ended. | --- | :-: |"])
def test_a_table_delimiter_row_is_refused_at_a_line_start(rules, md, monkeypatch):
    """mdformat-gfm escapes the first `-` of a line made only of `|`, `-`, `:`
    and spaces, which a broad `lowercase_names` pattern could open."""
    md += "\n"
    everything = Recorded(names=True)
    assert rules(everything, md, ["gfm"]) == plain(md, ["gfm"])
    monkeypatch.setattr(_detect, "_escaped_at_line_start", lambda *_: False)
    assert rules(everything, md, ["gfm"]) != plain(md, ["gfm"])


@pytest.mark.parametrize("extensions", [(), ("gfm",)])
def test_the_task_box_is_refused_with_or_without_gfm(extensions):
    md = "It is done. [X] marks a finished task.\n"
    assert plugin(md, extensions) == plain(md, extensions)


@pytest.mark.parametrize(
    "md",
    [
        "It ended. * Then more.",
        "It ended. _ Then more.",
        'It ended. " _ Then more.',
        "It ended. \u00a0* Then more.",
    ],
)
def test_a_lone_star_or_underscore_stays_off_a_line_edge(md, monkeypatch):
    """mdformat's `text()` escapes a literal `*` or `_` at a line edge on the
    second pass, which renders the same (section 3.5)."""
    md += "\n"
    assert plugin(md) == plain(md)
    monkeypatch.setattr(_detect, "_NEIGHBORED", frozenset())
    assert "\\" in plugin(md)


def test_emphasis_markup_is_not_a_literal_mark():
    md = "It *ended.* Then *it* went. It ended. *Then* it went.\n"
    assert plugin(md) == "It *ended.*\nThen *it* went.\nIt ended.\n*Then* it went.\n"


def test_edge_safety(rules, monkeypatch):
    md = "Il a dit.  Puis il part. Il a dit.  Puis il part.\n"
    assert plugin(md) == "Il a dit.  Puis il part.\nIl a dit.  Puis il part.\n"
    # mdformat strips each line, so a break at either gap deletes a space.
    monkeypatch.setattr(_detect, "is_safe", lambda *_: True)
    assert plugin(md).count(" ") < md.count(" ")


# Section 6.2's minimality row: the checks in code cannot be removed and
# tested, so each has a pair of fixtures, one it decides and its
# counterpart differing only in what the check reads.
PAIRS = {
    "opaque atom": [
        ("It ended. `x` runs.", "It ended.\n`x` runs."),
        ("It ended. x runs.", "It ended. x runs."),
    ],
    "line-start check": [
        ("Hear us. 1. Tell us.", "Hear us. 1.\nTell us."),
        ("Hear us. 1 Tell us.", "Hear us.\n1 Tell us."),
    ],
    "bracket pairing, a pair": [
        ("A (b. C) d. E f.", "A (b. C) d.\nE f."),
        ("A b. C d. E f.", "A b.\nC d.\nE f."),
    ],
    "bracket pairing, an unpaired closer": [
        ("A b. C) d. E f.", "A b.\nC) d.\nE f."),
        ("A (b. C) d. E f.", "A (b. C) d.\nE f."),
    ],
    "bracket pairing, an unpaired opener": [
        ("A (b. C d. E f.", "A (b.\nC d.\nE f."),
        ("A (b. C d.) E f.", "A (b. C d.)\nE f."),
    ],
    "inline atoms": [
        ("Install the `foo.` Then run it.", "Install the `foo.` Then run it."),
        ("Install the foo. Then run it.", "Install the foo.\nThen run it."),
    ],
    "footnote strip": [
        ("At hand.[^1] This is next.", "At hand.[^1]\nThis is next."),
        ("At hand.[1] This is next.", "At hand.[1] This is next."),
    ],
}


@pytest.mark.parametrize("check", PAIRS)
def test_checks_in_code_have_fixture_pairs(check):
    (md, expected), (counterpart, counterpart_expected) = PAIRS[check]
    assert plugin(md + "\n") == expected + "\n"
    assert plugin(counterpart + "\n") == counterpart_expected + "\n"


def test_sentence_break_values_come_from_the_vendored_data():
    """Python files Mkhedruli as lowercase; UAX #29 as `OLetter`
    (section 3.3)."""
    assert "ა".islower()
    assert _detect.sentence_break_value("ა") == _detect.OLETTER
    assert _detect.sentence_break_value("ǅ") == _detect.UPPER
    assert _detect.sentence_break_value("$") is None
