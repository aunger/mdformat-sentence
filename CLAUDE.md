# mdformat-sentence

An mdformat plugin that puts one sentence on each line, specified in `DESIGN.md` and not yet built.

## What is authoritative

`DESIGN.md` is normative, except where a passage says it reports a measurement or a verification (§3's preamble).
Code follows it.
When code cannot be built as `DESIGN.md` says, change `DESIGN.md` in the same pull request, and anchor a PR comment at each place the two would otherwise differ.
Never let them drift apart silently.

`notes/` is working material and is not normative; `notes/CLAUDE.md` gives its conventions.
Record each kind of finding where the notes say it goes:

- a deferral in `notes/FUTURE-WORK.md`, as an observation and an intention;
- a cost accepted on purpose in `notes/TRADE-OFFS.md`;
- behavior of a third-party project in `notes/quirks-<project>.md`;
- a measurement in prose that names the program in `notes/experiments/` that reproduces it.

## Building

Build in the order of §6.4, starting with the positive control.
The dependency range is §2's: mdformat `>=1.0.0,<1.1` on Python 3.10 or later, and the range moves only after §6's gate passes against the new version.
Check any claim about mdformat by running it against 1.0.0, and say whether a claim was run or only read.

## Writing

Prose in `DESIGN.md` and `notes/` is one sentence per line, because `DESIGN.md` is also a fixture (§6.2, the dogfood row).
So every line must end a sentence, with its terminator outside any code span, and the next line must open with a capital, a digit, a code span or `mdformat`.
Write "Section 6.2", not "§6.2", at the start of a sentence.
Run `mdformat --check DESIGN.md` with plain mdformat 1.0.0 before committing.

Never run mdformat over `notes/corpus/`: `sembr.md` there is verbatim third-party text pinned by a checksum, and `notes/corpus/README.md` explains why mdformat's own `exclude` cannot protect it.
