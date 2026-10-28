"""The vendored Unicode data and the module generated from it
(sections 2 and 3.3)."""

from mdformat_sentence import _detect, _generate_ucd, _ucd


def test_the_generated_module_is_regenerated_exactly():
    """A Unicode upgrade is one replaced file and a reviewable diff
    (section 3.3)."""
    source = _generate_ucd.SOURCE.read_text(encoding="utf-8")
    assert _generate_ucd.TARGET.read_text(encoding="utf-8") == _generate_ucd.generate(source)


def test_the_data_is_ucd_18():
    assert _ucd.VERSION == "18.0.0"
    assert len(_detect.TERMINATORS) == 172
    assert _detect.ATERMS == frozenset(".․﹒．")
    assert len(_detect.STERMS) == 168


def test_each_class_matches_the_file_total():
    """Every value's ranges add up to the total the file states for it."""
    source = _generate_ucd.SOURCE.read_text(encoding="utf-8")
    for value in _generate_ucd.VALUES:
        ranges = getattr(_ucd, value.upper())
        count = sum(last - first + 1 for first, last in ranges)
        block = source[source.index(f"; {value} ") :]
        stated = int(block[block.index("# Total code points: ") :].split()[4])
        assert count == stated, value


def test_the_license_travels_beside_the_data():
    license = _generate_ucd.SOURCE.with_name("LICENSE.txt").read_text(encoding="utf-8")
    assert license.startswith("UNICODE LICENSE V3")
