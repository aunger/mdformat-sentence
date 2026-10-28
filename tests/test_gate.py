"""The rows of section 6.2 that segmentation and pinning
(sections 3.1 to 3.6) must pass, over the fixtures and `notes/corpus/`."""

from __future__ import annotations

from itertools import pairwise

import pytest

from _gate import FIXTURES, WIDTHS, baseline, orders, preserves, run
from mdformat_sentence._segment import paragraph_parts


def _absent(fixture):
    """A fixture read from a file this checkout lacks is skipped, visibly:
    the sdist ships `tests/` without `DESIGN.md` and `notes/`."""
    if fixture.md is not None:
        return ()
    return pytest.mark.skip(reason=f"{fixture.name}: its file is not in this checkout")


def _cases(orders_of):
    return [
        pytest.param(
            f.md,
            f.plugins,
            extensions,
            id=f"{f.name}-{'+'.join(extensions)}",
            marks=_absent(f),
        )
        for f in FIXTURES
        for extensions in orders_of(f.plugins)
    ]


CASES = _cases(orders)

# Every fixture with the three co-plugins that section 6.2 loads under every row,
# before the plugin and after it.
ALONGSIDE = ("gfm", "mkdocs", "footnote")
CASES_ALONGSIDE = _cases(lambda _: [(*ALONGSIDE, "sentence"), ("sentence", *ALONGSIDE)])

# Atoms that section 3.1's fallback may make: mdformat-gfm's bare URL and
# mdformat-mkdocs's attribute list.
NAMED_FALLBACKS = {"gfm_autolink", "python_markdown_attr_list"}


@pytest.mark.parametrize("md, plugins, extensions", CASES)
def test_width_independence(md, plugins, extensions):
    expected = run(md, extensions, "no").out
    for wrap in WIDTHS[1:]:
        assert run(md, extensions, wrap).out == expected, wrap


@pytest.mark.parametrize("wrap", ["no", 40])
@pytest.mark.parametrize("md, plugins, extensions", CASES)
def test_idempotency_vs_baseline(md, plugins, extensions, wrap):
    plain = baseline(md, plugins, wrap)
    if baseline(plain, plugins, wrap) != plain:
        pytest.skip("plain mdformat is not idempotent here either")
    once = run(md, extensions, wrap).out
    assert run(once, extensions, wrap).out == once


@pytest.mark.parametrize("wrap", ["keep", "no", 40])
@pytest.mark.parametrize("md, plugins, extensions", CASES)
def test_text_preservation(md, plugins, extensions, wrap):
    pairs = run(md, extensions, wrap).pairs
    assert pairs
    for given, out in pairs:
        assert preserves(given, out), (given, out)


@pytest.mark.parametrize("wrap", ["no", 40])
@pytest.mark.parametrize("md, plugins, extensions", CASES)
def test_no_back_offs(md, plugins, extensions, wrap):
    assert run(md, extensions, wrap).back_offs == 0


@pytest.mark.parametrize("wrap", ["no", 40])
@pytest.mark.parametrize("md, plugins, extensions", CASES)
def test_container_fallbacks_are_named(md, plugins, extensions, wrap):
    assert set(run(md, extensions, wrap).fallbacks) <= NAMED_FALLBACKS


@pytest.mark.parametrize("wrap", ["no", 40])
@pytest.mark.parametrize("md, plugins, extensions", CASES)
def test_each_paragraph_part_gets_its_own_pieces(md, plugins, extensions, wrap):
    """`paragraph_parts` walks the pieces once, which holds only while
    `locate` returns them in text order with no overlap."""
    located = run(md, extensions, wrap).located
    assert located
    for text, pieces in located:
        assert all(a.start <= a.end <= b.start for a, b in pairwise(pieces))
        for part in paragraph_parts(text, pieces):
            first, last = part.span
            assert part.pieces == [
                p for p in pieces if p.start < last and p.end > first
            ]


@pytest.mark.parametrize("wrap", ["no", 40])
@pytest.mark.parametrize("md, plugins, extensions", CASES_ALONGSIDE)
def test_the_recording_map_is_never_listed(md, plugins, extensions, wrap):
    """Copying the recording map would drop the recorder for node types
    the wrapped map lacks (`notes/TRADE-OFFS.md`); a copy lists it."""
    assert run(md, extensions, wrap).listed == 0
