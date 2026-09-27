"""Lone quotation marks: DESIGN.md §3.3, simulated.

A lone mark is a segment made only of quotation or markup characters.
This runs §3.3's sentence-end test, capital test and the two lone-mark
rules over plain strings split at ordinary spaces, which is what the
seam delivers for these texts. Stdlib only.

Terminators are cut down to the ones these texts use; the real set is
UAX #29 STerm and ATerm. No rules table is consulted: none of these
texts has an abbreviation in it.

It establishes four things:
  1. the fixtures of §6.4 for quotation marks break where §3.3 says;
  2. one lone mark's role moves only the mark, never a break
     (seventeen texts, 64 readings);
  3. two lone marks side by side are different: their readings do
     change the breaks. §3.3's readings break both examples correctly,
     but the English marks land on the wrong lines, because a spaced
     opening “ or " after a sentence end reads as closing;
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
CLOSERS = set("\"'’”»›«‹“‘‟‛„」』》〉*_~")
OPENERS = set("\"'“‘‟‛«‹»›¿¡„‚「『《〈*_~[(\\")
NBSP = {chr(c) for c in range(sys.maxunicode + 1) if unicodedata.category(chr(c)) == "Zs"} - {" "}
GLYPH_OPEN = set("«‹「『《〈")
GLYPH_CLOSE = set("»›」』》〉")
TAIL = "".join(CLOSERS | NBSP)  # skipped by the sentence-end test
HEAD = "".join(OPENERS | NBSP)  # skipped by the capital test
LONE = TAIL + HEAD


def is_lone(seg):
    return bool(seg) and not seg.strip(LONE)


def ends_sentence(seg):
    return seg.rstrip(TAIL)[-1:] in TERMINATORS


def opens_sentence(seg):
    """True or False for the first testable character; None if there is none."""
    ch = seg.lstrip(HEAD)[:1]
    if not ch:
        return None
    return ch.isdigit() or (ch.isalpha() and not ch.islower())


def spec_roles(segs, glyph_open=GLYPH_OPEN):
    """§3.3: CJK marks and guillemets by glyph, every other lone mark by what precedes it."""
    roles = {}
    for i, s in enumerate(segs):
        if not is_lone(s):
            continue
        if s[0] in glyph_open:
            roles[i] = "open"
        elif s[0] in GLYPH_CLOSE:
            roles[i] = "close"
        else:
            roles[i] = "close" if i > 0 and ends_sentence(segs[i - 1]) else "open"
    return roles


def emit(segs, roles):
    out = [segs[0]]
    for i in range(len(segs) - 1):
        right = segs[i + 1]
        if roles.get(i + 1) == "close":  # a closing mark is never a break candidate
            out.append(" " + right)
            continue
        k = i  # the terminator test looks back past every closing mark
        while k > 0 and roles.get(k) == "close":
            k -= 1
        breaks = ends_sentence(segs[k]) and next(  # an opening mark defers the capital test
            (opens_sentence(s) for j, s in enumerate(segs[i + 1:], i + 1) if roles.get(j) != "open"), None)
        out.append(("\n" if breaks else " ") + right)
    return "".join(out)


def split(text):
    return re.split(r" +", text)


def run(text, glyph_open=GLYPH_OPEN):
    segs = split(text)
    return emit(segs, spec_roles(segs, glyph_open))


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
    ("nested quotes, spaced", "Il a dit. « “ Oui. ” » Puis il part.",
     "Il a dit.\n« “ Oui. ” »\nPuis il part."),
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


print("2. One lone mark between two words: its role moves only the mark\n")
SINGLE = [
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
]
total, invariant = 0, True
for t in SINGLE:
    seen, n = layouts(t)
    total += n
    invariant &= len(seen) == 1
print(f"{len(SINGLE)} texts, {total} readings; the same words on every line in all of them: {invariant}\n")

print("3. Two lone marks side by side: the readings matter\n")
for t in ("Il a dit. « “ Oui. ” » Puis il part.", "He said. “ ‘ Yes. ’ ” Then he left."):
    seen, n = layouts(t)
    print(f"{t}\n   {n} readings give {len(seen)} different word layouts; §3.3's reading gives")
    for line in run(t).split("\n"):
        print(f"       {line}")
print()

print("4. The rejected option: reading „ and ‚ by glyph\n")
t = "degli “ umiliati del villaggio. „ Quegli era un avvocato"
for label, got in (("older rule (§3.3)", run(t)),
                   ("by glyph", run(t, glyph_open=GLYPH_OPEN | set("„‚")))):
    print(f"   {label:18} {got!r}")
