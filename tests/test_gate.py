"""The rows of §6.2 that segmentation and pinning (§3.1 to §3.6) must
pass, over the fixtures and `notes/corpus/`."""

from __future__ import annotations

import pytest

from _gate import FIXTURES, WIDTHS, baseline, orders, preserves, run

CASES = [
    pytest.param(f.md, f.plugins, extensions, id=f"{f.name}-{'+'.join(extensions)}")
    for f in FIXTURES
    for extensions in orders(f.plugins)
]

# Atoms §3.1's fallback may make: mdformat-gfm's bare URL and
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
