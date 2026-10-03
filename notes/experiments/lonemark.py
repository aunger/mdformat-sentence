"""Lone quotation marks: DESIGN.md §3.3, simulated.

A lone mark is a segment made only of quotation or markup characters, and
a run is one or more of them between two words. This runs §3.3's
sentence-end test, capital test and the lone-mark rules over plain strings
split at ordinary spaces, which is what the seam delivers for these texts.
Stdlib only.

Terminators are cut down to the ones these texts use; the real set is
UAX #29 STerm and ATerm. No rules table, bracket depth or capital-test
exemption is consulted: none of these texts needs one.

It establishes four things:
  1. the fixtures of §6.4 for quotation marks break where §3.3 says;
  2. a run of lone marks is one gap: the words on either side decide
     whether it breaks, and the marks' roles only decide where in the
     run the newline goes, so no reading of any mark, alone or side by
     side, changes which words share a line;
  3. what §3.3's own readings do with marks side by side, including the
     known misplacement of a spaced opening “ after a sentence end;
  4. reading the low mark „ by its glyph would misplace the historical
     Italian closing „, spaced as it was printed, which the older rule
     places correctly. De Amicis, Il romanzo d'un maestro, 1900, p. 189;
     Wikisource transcribes it attached, which the fixtures also cover.
"""
import itertools
import re
import sys
import unicodedata

TERMINATORS = set(".!?。！？")
CLOSERS = set("\"'’”»›«‹“‘‟‛„」』》〉)]*_~")
OPENERS = set("\"'’”“‘‟‛«‹»›¿¡„‚「『《〈[(*_~\\")
NBSP = {chr(c) for c in range(sys.maxunicode + 1) if unicodedata.category(chr(c)) == "Zs"} - {" "}
SHAPE_OPEN = set("«‹")          # guillemets, read the French way
SHAPE_CLOSE = set("»›”’")       # and the right-hand curly quotes, never spaced to open
TAIL = "".join(CLOSERS | NBSP)  # skipped by the sentence-end test
HEAD = "".join(OPENERS | NBSP)  # skipped by the capital test
LONE = TAIL + HEAD


def is_lone(seg):
    return bool(seg) and not seg.strip(LONE)


def ends_sentence(seg):
    return seg.rstrip(TAIL)[-1:] in TERMINATORS


def opens_sentence(seg):
    ch = seg.lstrip(HEAD)[:1]
    return ch.isdigit() or (ch.isalpha() and not ch.islower())


def spec_role(segs, i, shape_open=SHAPE_OPEN):
    """§3.3: by shape for guillemets and ” ’, by set for a mark in one set only,
    and otherwise by what precedes it."""
    ch = segs[i][0]
    if ch in shape_open:
        return "open"
    if ch in SHAPE_CLOSE:
        return "close"
    if ch in OPENERS and ch not in CLOSERS:
        return "open"
    if ch in CLOSERS and ch not in OPENERS:
        return "close"
    return "close" if i > 0 and ends_sentence(segs[i - 1]) else "open"


def spec_roles(segs, shape_open=SHAPE_OPEN):
    return {i: spec_role(segs, i, shape_open) for i, s in enumerate(segs) if is_lone(s)}


def emit(segs, roles):
    """Words decide whether a run breaks; roles decide where in it."""
    words = [i for i, s in enumerate(segs) if not is_lone(s)]
    breaks = set()
    for left, right in zip(words, words[1:]):
        if ends_sentence(segs[left]) and opens_sentence(segs[right]):
            run = range(left + 1, right)
            opening = [i for i in run if roles.get(i) == "open"]
            breaks.add(opening[0] if opening else right)  # newline goes before this segment
    return segs[0] + "".join(("\n" if i in breaks else " ") + segs[i] for i in range(1, len(segs)))


def split(text):
    return re.split(r" +", text)


def run(text, shape_open=SHAPE_OPEN):
    segs = split(text)
    return emit(segs, spec_roles(segs, shape_open))


def show(label, got, want):
    ok = "ok  " if got == want else "FAIL"
    print(f"{ok} {label}")
    for line in got.split("\n"):
        print(f"       {line}")
    return got == want


print("1. Fixtures\n")
FIXTURES = [
    ("spaced French", "Il a dit. « Ceci est important. » Puis il part.",
     "Il a dit.\n« Ceci est important. »\nPuis il part."),
    ("spaced Japanese", "彼は言った。 「こんにちは。」 次の文です。",
     "彼は言った。\n「こんにちは。」\n次の文です。"),
    ("CJK quote in English", "She said 「Yes.」 Then he left.",
     "She said 「Yes.」\nThen he left."),
    ("continuation paragraph opening with »",
     "» La première est la vigueur de la croissance. La deuxième est la prudence.",
     "» La première est la vigueur de la croissance.\nLa deuxième est la prudence."),
    ("historical Italian closing „, spaced as printed",
     "degli “ umiliati del villaggio. „ Quegli era un avvocato",
     "degli “ umiliati del villaggio. „\nQuegli era un avvocato"),
    ("the same, attached as transcribed: „ is a closer",
     "degli “umiliati del villaggio.„ Quegli era un avvocato",
     "degli “umiliati del villaggio.„\nQuegli era un avvocato"),
    ("German „ still opens", "Er sagte. „Hallo.“ Dann ging er.",
     "Er sagte.\n„Hallo.“\nDann ging er."),
    ("Greek nested quotation opening with ‟", "«Του είπα. ‟Όχι.” Και έφυγε.»",
     "«Του είπα.\n‟Όχι.”\nΚαι έφυγε.»"),
    ("Polish quotation opening with ‛", "Zapytał. ‛Dlaczego?’ Nikt nie wiedział.",
     "Zapytał.\n‛Dlaczego?’\nNikt nie wiedział."),
    ("‟ closing, as some German transcriptions have it", "„Darf ich?‟ Sie lachte.",
     "„Darf ich?‟\nSie lachte."),
    ("Finnish quotation opening with ”", "Se oli selvää. ”Tule mukaan!” hän pyysi.",
     "Se oli selvää.\n”Tule mukaan!” hän pyysi."),
    ("Swedish quotation opening with ’", "Han sa. ’Kom hit!’ Sedan gick han.",
     "Han sa.\n’Kom hit!’\nSedan gick han."),
    ("nested quotes, spaced French-style", "Il a dit. « “ Oui. ” » Puis il part.",
     "Il a dit.\n« “ Oui. ” »\nPuis il part."),
    ("nested quotes, spaced English-style", "He said: “ ‘ Yes. ’ ” Then he left.",
     "He said: “ ‘ Yes. ’ ”\nThen he left."),
    ("spaced Spanish ¿ opens by its set", "Dijo algo. ¿ Por qué ? Nadie sabe.",
     "Dijo algo.\n¿ Por qué ?\nNadie sabe."),
    ("a sentence in spaced parentheses", "He left. ( He came back. ) Then more.",
     "He left.\n( He came back. )\nThen more."),
    ("an opening mark before a closing one still breaks", "Il a dit. « » Puis il part.",
     "Il a dit.\n« » Puis il part."),
]
passed = sum(show(label, run(t), want) for label, t, want in FIXTURES)
print(f"\n{passed} of {len(FIXTURES)} fixtures hold\n")


def layouts(text):
    """The distinct word layouts over every open/close reading of the lone marks."""
    segs = split(text)
    idx = [i for i, s in enumerate(segs) if is_lone(s)]
    seen = set()
    for reading in itertools.product(("open", "close"), repeat=len(idx)):
        out = emit(segs, dict(zip(idx, reading)))
        seen.add(tuple(" ".join(w for w in ln.split() if not is_lone(w)) for ln in out.split("\n")))
    return seen, 2 ** len(idx)


print("2. A mark's role moves only the mark, alone or side by side\n")
TEXTS = [
    "Il a dit. « Ceci est important. » Puis il part.",
    "« Vraiment ? » dit-il. Puis il part.",
    "Il a dit : « Oui. » Puis il part.",
    "Er sagte. » Das ist wichtig. « Dann ging er.",
    "Hän sanoi. » Tämä on tärkeää. » Sitten hän lähti.",
    "Il a dit. « Ceci continue. Et encore.",
    "— Oui, bien sûr. » Puis il partit.",
    "Il a dit : « Il y a trois raisons. » La première est la croissance. »",
    "C'est disponible. » Lire la suite. Fin.",
    "He said. \" Hello. \" Then he left.",
    "Le mot « chat » désigne un animal. Puis il part.",
    "Il a crié « Stop ! » et il est parti.",
    "He read 『 Kokoro. 』 Then he slept.",
    "» La première est la vigueur de la croissance. La deuxième est la prudence.",
    "» Finalement, la troisième raison est prudente. » Le ministre a ensuite parlé.",
    "degli “ umiliati del villaggio. „ Quegli era un avvocato",
    "他说： 《 你好。 》 然后走了。",
    "Il a dit. « “ Oui. ” » Puis il part.",
    "He said. “ ‘ Yes. ’ ” Then he left.",
    "He said. \" ' Yes. ' \" Then he left.",
    "Il a dit. « » Puis il part.",
    "He left. ( He came back. ) Then more.",
]
total, invariant = 0, True
for t in TEXTS:
    seen, n = layouts(t)
    total += n
    invariant &= len(seen) == 1
print(f"{len(TEXTS)} texts, {total} readings; the same words on every line in all of them: {invariant}\n")

print("3. §3.3's readings of marks side by side\n")
for t in ("Il a dit. « “ Oui. ” » Puis il part.", "He said. “ ‘ Yes. ’ ” Then he left."):
    print(t)
    for line in run(t).split("\n"):
        print(f"       {line}")
print("   The leading “ after `said.` reads as closing, the older rule's known cost.\n")

print("4. The rejected option: reading „ and ‚ by glyph\n")
t = "degli “ umiliati del villaggio. „ Quegli era un avvocato"
for label, got in (("older rule (§3.3)", run(t)),
                   ("by glyph", run(t, shape_open=SHAPE_OPEN | set("„‚")))):
    print(f"   {label:18} {got!r}")
