"""The positive control of sections 6.2 and 6.4: it must fail when the
plugin is absent."""

import mdformat

SOURCE = "The first sentence ends here. The second one follows it.\n"
EXPECTED = "The first sentence ends here.\nThe second one follows it.\n"


def test_plain_mdformat_fails_the_control():
    assert mdformat.text(SOURCE, options={"wrap": "no"}, extensions=set()) != EXPECTED


def test_positive_control():
    out = mdformat.text(SOURCE, options={"wrap": "no"}, extensions={"sentence"})
    assert out == EXPECTED
