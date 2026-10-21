"""The `--wrap keep` warning of §2.5."""

import logging

import mdformat
from mdformat._cli import run
import pytest

from mdformat_sentence._plugin import KEEP_WARNING

PARAGRAPHS = "It ended. Then it began.\n\nOne more.\n\nAnd another.\n"


def cli(tmp_path, capsys, *args, files=1, md=PARAGRAPHS):
    # An empty config stops mdformat's upward search, so no
    # `.mdformat.toml` above the temporary directory can reach the test.
    toml = tmp_path / ".mdformat.toml"
    if not toml.exists():
        toml.write_text("")
    paths = []
    for i in range(files):
        path = tmp_path / f"doc{i}.md"
        path.write_text(md)
        paths.append(str(path))
    assert run([*args, *paths]) == 0
    return capsys.readouterr().err.count(KEEP_WARNING)


@pytest.mark.parametrize("wrap", [[], ["--wrap", "keep"]])
def test_warns_once_per_file_when_named(tmp_path, capsys, wrap):
    assert cli(tmp_path, capsys, "--extensions", "sentence", *wrap) == 1
    assert cli(tmp_path, capsys, "--extensions", "sentence", *wrap, files=2) == 2


def test_warns_when_named_in_toml(tmp_path, capsys):
    (tmp_path / ".mdformat.toml").write_text('extensions = ["sentence"]\n')
    assert cli(tmp_path, capsys) == 1


@pytest.mark.parametrize("wrap", ["no", "40"])
def test_silent_when_the_plugin_can_act(tmp_path, capsys, wrap):
    assert cli(tmp_path, capsys, "--extensions", "sentence", "--wrap", wrap) == 0


def test_silent_when_no_paragraph_was_rendered(tmp_path, capsys):
    # Headings and table cells hold inline nodes too; the paragraph-parent
    # guard (§2.2) is what keeps them from reaching the warning.
    md = "# It ended. Then it began.\n\n| It ended. Then it began. |\n| -- |\n| a |\n"
    named = ["--extensions", "sentence", "--extensions", "gfm"]
    assert cli(tmp_path, capsys, *named, md=md) == 0


def test_silent_on_the_default_configuration(tmp_path, capsys):
    assert cli(tmp_path, capsys) == 0
    assert cli(tmp_path, capsys, "--wrap", "keep") == 0


def test_silent_through_the_api(caplog):
    with caplog.at_level(logging.WARNING, logger="mdformat"):
        mdformat.text(PARAGRAPHS, options={"wrap": "keep"}, extensions={"sentence"})
        mdformat.text(PARAGRAPHS, extensions={"sentence"})
    assert KEEP_WARNING not in caplog.text
