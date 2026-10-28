"""Section 6.4's sentence-detection fixtures, each with its expected output
at `--wrap no`.

The fixtures that need a shipped rule, abbreviations, initials, an index
abbreviation before a punctuated number and the ellipsis, wait for the
rules files (section 4).
"""

from __future__ import annotations

from typing import NamedTuple


class Case(NamedTuple):
    name: str
    md: str
    expected: str
    plugins: tuple[str, ...] = ()


def _case(name, md, expected, plugins=()):
    return Case(name, md + "\n", expected + "\n", plugins)


NBSP = " "

DETECTION = [
    # Detection.
    _case(
        "camelCase openers",
        "The phone shipped in 2007. iOS came later. It ended. gRPC came next.",
        "The phone shipped in 2007.\niOS came later.\nIt ended.\ngRPC came next.",
    ),
    _case(
        "lowercase_names openers",
        "It is a formatter. mdformat runs it. Then mdformat's rules apply. "
        "And mdformat-gfm too.",
        "It is a formatter.\nmdformat runs it.\nThen mdformat's rules apply.\n"
        "And mdformat-gfm too.",
    ),
    _case(
        "a hyphenated word ending in a capital",
        "He met Jay-Z. He left.",
        "He met Jay-Z.\nHe left.",
    ),
    _case(
        "the capital test",
        "It ended. then it went on. 1976 was hot. Hot? Yes! $HOME is set. "
        "@octocat replied. — Oui, je viens.",
        "It ended. then it went on.\n1976 was hot.\nHot?\n"
        "Yes! $HOME is set. @octocat replied. — Oui, je viens.",
    ),
    _case(
        "the capital test reads Sentence_Break",
        "Il est parti. ხვალ დავბრუნდები. Next. ω is small. Done. انتهى الأمر. Ok.",
        "Il est parti.\nხვალ დავბრუნდები.\nNext. ω is small.\nDone.\nانتهى الأمر.\nOk.",
    ),
    _case(
        "STerm takes the capital test",
        'Panic! at the Disco played. Yahoo! bought it. A "Is this a test?" guide follows.',
        'Panic! at the Disco played.\nYahoo! bought it.\nA "Is this a test?" guide follows.',
    ),
    _case(
        "clause punctuation is not a closer",
        "Use e.g., this one. And i.e.; that one.",
        "Use e.g., this one.\nAnd i.e.; that one.",
    ),
    _case(
        "an ellipsis character is not a terminator",
        "A moment… Nobody moved. A moment…. Nobody moved.",
        "A moment… Nobody moved.\nA moment….\nNobody moved.",
    ),
    _case(
        "the Greek question mark is out of reach",
        "Τι είναι; Δεν ξέρω.",
        "Τι είναι; Δεν ξέρω.",
    ),
    _case(
        "footnote references",
        "The matter at hand.[^1] This is next. Held.[1] Then more. "
        "Held.<sup>1</sup> Then more.",
        "The matter at hand.[^1]\nThis is next.\nHeld.[1] Then more.\n"
        "Held.<sup>1</sup> Then more.",
    ),
    _case("CJK", "彼は言った。 次の文です。", "彼は言った。\n次の文です。"),
    _case(
        "a period inside a code span or a link destination",
        "Install the `foo.` Then run it. See the [docs](https://ex.com/a.b.) The next one.",
        "Install the `foo.` Then run it.\nSee the [docs](https://ex.com/a.b.) The next one.",
    ),
    _case(
        "opaque atoms open a sentence",
        "It ended. ![An image](i.png) follows. It ended. <https://x.y> is next. "
        "It ended. <em>then</em> no. It ended. <br> Then. It ended. `x` runs.",
        "It ended.\n![An image](i.png) follows.\nIt ended.\n<https://x.y> is next.\n"
        "It ended. <em>then</em> no.\nIt ended.\n<br> Then.\nIt ended.\n`x` runs.",
    ),
    _case(
        "formatted text is words",
        "It ended. [the docs](u) explain it. It ended. [The docs](u) explain it. "
        "It ended. *Then* it went. It ended. **so** it went.",
        "It ended. [the docs](u) explain it.\nIt ended.\n[The docs](u) explain it.\n"
        "It ended.\n*Then* it went.\nIt ended. **so** it went.",
    ),
    # Quotation marks.
    _case(
        "CJK marks spaced off their words",
        "彼は言った。 「こんにちは。」 次の文です。 She said 「Yes.」 Then he left.",
        "彼は言った。\n「こんにちは。」\n次の文です。\nShe said 「Yes.」\nThen he left.",
    ),
    _case(
        "French spaced closers",
        "Il a dit. « Ceci est important. » Puis il part. « Vraiment ? » dit-il en partant.",
        "Il a dit.\n« Ceci est important. »\nPuis il part.\n"
        "« Vraiment ? » dit-il en partant.",
    ),
    _case(
        "French typeset with no-break spaces",
        f"Il a dit.{NBSP}«{NBSP}Ceci est important.{NBSP}» Puis il part.",
        f"Il a dit.{NBSP}«{NBSP}Ceci est important.{NBSP}»\nPuis il part.",
    ),
    _case(
        "guillemets around a word or a fragment",
        "Le mot « chat » désigne un animal. Puis il part. "
        "Il l'appelle « le patron ». Puis il part. Il a crié « Stop ! » et il est parti.",
        "Le mot « chat » désigne un animal.\nPuis il part.\n"
        "Il l'appelle « le patron ».\nPuis il part.\nIl a crié « Stop ! » et il est parti.",
    ),
    _case(
        "French dialogue that closes in a later paragraph",
        "« Viens-tu ce soir ? Je t'attends.\n\n— Oui, bien sûr. » Puis il partit.",
        "« Viens-tu ce soir ?\nJe t'attends.\n\n— Oui, bien sûr. »\nPuis il partit.",
    ),
    _case(
        "a continuation paragraph opening with »",
        "» La première est la vigueur de la croissance. La deuxième est la prudence.",
        "» La première est la vigueur de la croissance.\nLa deuxième est la prudence.",
    ),
    _case(
        "Finnish and Swedish quotations opening with ” and ’",
        "Se oli selvää. ”Tule mukaan!” hän pyysi. Han sa. ’Kom hit!’ Sedan gick han.",
        "Se oli selvää.\n”Tule mukaan!” hän pyysi.\nHan sa.\n’Kom hit!’\nSedan gick han.",
    ),
    _case(
        "nested quotations spaced French-style",
        "Il a dit. « “ Oui. ” » Puis il part.",
        "Il a dit.\n« “ Oui. ” »\nPuis il part.",
    ),
    _case(
        "nested quotations spaced English-style",
        "He said: “ ‘ Yes. ’ ” Then he left. He said. “ ‘ Yes. ’ ” Then he left.",
        # After a sentence end the leading “ reads as closing (section 3.3).
        "He said: “ ‘ Yes. ’ ”\nThen he left.\nHe said. “\n‘ Yes. ’ ”\nThen he left.",
    ),
    _case(
        "spaced straight quotes",
        'He said. " Hello. " Then he left.',
        'He said. "\nHello. "\nThen he left.',
    ),
    _case(
        "a spaced ¿",
        "Dijo algo. ¿ Por qué ? Nadie sabe.",
        "Dijo algo.\n¿ Por qué ?\nNadie sabe.",
    ),
    _case(
        "the historical Italian closing „",
        "degli “ umiliati del villaggio. „ Quegli era un avvocato. "
        "degli “umiliati del villaggio.„ Quegli era un avvocato.",
        "degli “ umiliati del villaggio. „\nQuegli era un avvocato. "
        "degli “umiliati del villaggio.„\nQuegli era un avvocato.",
    ),
    _case(
        "Greek and Polish quotations opening with ‟ and ‛",
        "«Του είπα. ‟Όχι.” Και έφυγε.» Zapytał. ‛Dlaczego?’ Nikt nie wiedział.",
        "«Του είπα.\n‟Όχι.”\nΚαι έφυγε.»\nZapytał.\n‛Dlaczego?’\nNikt nie wiedział.",
    ),
    _case(
        "German quotes",
        "Er sagte. „Hallo.“ Dann ging er. »Ist das ein Test?« Dann ging er. "
        "„Darf ich?‟ Sie lachte.",
        "Er sagte.\n„Hallo.“\nDann ging er.\n»Ist das ein Test?«\nDann ging er.\n"
        "„Darf ich?‟\nSie lachte.",
    ),
    _case(
        'the ?" case',
        'He asked "Why?" Then he left. A "Why?" guide.',
        'He asked "Why?"\nThen he left.\nA "Why?" guide.',
    ),
    _case(
        "an opening mark before a closing one",
        "Il a dit. « » Puis il part.",
        "Il a dit.\n« » Puis il part.",
    ),
    # Brackets.
    _case(
        "sentences ending inside parentheses and brackets",
        "He left. (He came back.) Then he left again. The editor wrote it. "
        "[This was later retracted.] Readers noticed. "
        "We tested browsers (Chrome, Firefox, etc.) Most passed.",
        "He left.\n(He came back.)\nThen he left again.\nThe editor wrote it.\n"
        "[This was later retracted.]\nReaders noticed.\n"
        "We tested browsers (Chrome, Firefox, etc.)\nMost passed.",
    ),
    _case(
        "spaced parentheses",
        "He left. ( He came back. ) Then more.",
        "He left.\n( He came back. )\nThen more.",
    ),
    _case(
        "bracket depth",
        "As shown (Smith et al. 1990. Later work) it held. "
        "See [@Smith2020, p. 12-14] for it.",
        "As shown (Smith et al. 1990. Later work) it held.\n"
        "See [@Smith2020, p. 12-14] for it.",
    ),
    _case(
        "unclosed openers followed by later sentence ends",
        "It failed :( again. Then it worked. Label 1(a is open. Then more. End.",
        "It failed :( again.\nThen it worked.\nLabel 1(a is open.\nThen more.\nEnd.",
    ),
    _case(
        "an unclosed opener adopted across a sentence end",
        "It failed :(. Then came a) and b). Done.",
        "It failed :(. Then came a) and b).\nDone.",
    ),
    # Safety checks.
    _case(
        "a word opening with ~~~ after a sentence end",
        "It ended. ~~~Then more.",
        "It ended. ~~~Then more.",
    ),
    _case(
        "a paragraph part that mentions ~~~",
        "Use `~~~` for fences. Then indent the block.",
        "Use `~~~` for fences.\nThen indent the block.",
    ),
    _case(
        "a run whose newline would open a line with ~~~",
        'It ended. " ~~~ Then more.',
        'It ended. " ~~~ Then more.',
    ),
    _case(
        "a run whose newline would end a line in a no-break space",
        f"Il a dit. {NBSP} Puis il part.",
        f"Il a dit. {NBSP} Puis il part.",
    ),
    _case(
        "no-break spaces at a gap's edge",
        f"Il a dit.{NBSP} Puis il part. Il a dit. {NBSP}Puis il part.",
        f"Il a dit.{NBSP} Puis il part.\nIl a dit. {NBSP}Puis il part.",
    ),
    _case(
        "an HTML block opener",
        "Do not use it. <div> is a block element. Ok. <span>Inline</span> is fine.",
        "Do not use it. <div> is a block element.\nOk.\n<span>Inline</span> is fine.",
    ),
    _case(
        "task boxes",
        "It is done. [X] marks a finished task. It is open. [ ] Then it is not.",
        "It is done. [X] marks a finished task.\nIt is open. [ ] Then it is not.",
    ),
    # Section 6.4's hook-point fixtures that M3 decides.
    _case(
        "footnote reference with footnote",
        "The matter at hand.[^1] This is next.\n\n[^1]: A note. With two sentences.",
        "The matter at hand.[^1]\nThis is next.\n\n[^1]: A note.\n    With two sentences.",
        ("footnote",),
    ),
    *(
        _case(
            f"gfm url {url} breaks",
            f"Read https://en.wikipedia.org/wiki/{url} first. Then go.",
            # As mdformat-gfm renders the URL, with or without this plugin.
            f"Read https://en.wikipedia.org/wiki/{rendered} first.\nThen go.",
            ("gfm",),
        )
        for url, rendered in (
            ("Foo_(bar)", "Foo_(bar)"),
            ("Foo__bar__", "Foo__bar\\_\\_"),
            ("Foo*bar*", "Foo*bar\\*"),
        )
    ),
    # Section 6.4's fixtures from Panache.
    _case(
        "inline list markers end lines",
        "Hear from us in 60 days. 1. Tell us your name. 2. Describe the error.",
        "Hear from us in 60 days. 1.\nTell us your name. 2.\nDescribe the error.",
    ),
    _case(
        "a trailing newline emits no empty line",
        "Only one sentence.",
        "Only one sentence.",
    ),
]
