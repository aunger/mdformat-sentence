# Quirks: mdformat-space-control

A note, not a specification.
Behavior of mdformat-space-control that `DESIGN.md` does not work around.
Version 0.5.0 with mdformat 1.0.0 on Python 3.13; *verified* means run, *read* means read from source.
Nothing here has been filed.

______________________________________________________________________

## An authored line break reaches the plugin as a literal space

**Compatibility risk.** *Verified* 2026-10-18 (`experiments/spacecontrol.py`), space-control alone beside a stand-in `inline` renderer, in both load orders.
Its `softbreak` renderer, `_render_softbreak` in `mdformat_space_control/plugin.py`, returns a literal space (*read*), so an authored line break inside a paragraph never becomes a wrap point.
With it loaded, `One here.` and `Two here.` on two lines reach the `inline` renderer as `One\x00here. Two\x00here.` at `--wrap no` and `40`, where plain mdformat gives a wrap point in place of that space, so the sentence end there is not a gap and §3.4 cannot break it.
The hook point does not matter, because the `softbreak` child is rendered before any `inline` renderer or postprocessor sees the text.
A stand-in renderer that breaks after `.` before a capital shows what follows from the two passes of `mdformat.text()`: the first pass breaks `One here. Two here.`, the second reads each new break as a `softbreak` and joins it again, so a paragraph on one line comes back unbroken and one already broken at its sentence ends comes back as it was, in either load order.
A paragraph with an authored break at one sentence end and none at another keeps the first and gains no second, so every break in the output is one the author made.
At `--wrap keep` it joins the author's lines whether or not this plugin is loaded.
`DESIGN.md` §3.1's statement that `text()` turns an authored soft line break into a wrap point holds for plain mdformat, not with this plugin loaded.
The 2026-10-06 hook-point review reached the first point by reading its source and did not run it (`DESIGN-REVIEW-HOOK-POINT-2026-10-06.md` at `9264f70`, section *9. Known incompatibilities and out-of-scope notes*).
