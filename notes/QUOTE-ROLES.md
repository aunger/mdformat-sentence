# Quotation-mark roles: which marks can be read by their glyph?

A note, not a specification.
`DESIGN.md` §3.3 reads a lone CJK mark or a lone guillemet by its glyph, and every other lone mark by what precedes it.
This records the research behind that split.

The question was whether any curly or angle quotation mark always opens, or always closes, in every language.
Two agents answered it independently, one by computation from CLDR and one from typographic sources with a citation for every claim.
Their combined answer then went to three more agents, each told to refute one part of it: the single-role verdicts, the two-role verdicts, and the lone-guillemet rule already in the specification.
Only what survived is used.

Measured claims come from `experiments/cldrquotes.py` and `experiments/lonemark.py`.
Claims about printed books and style authorities were checked against the primary source where this note says so, and are marked where they were not.

______________________________________________________________________

## 0. The answer

| marks | verdict | basis |
| --- | --- | --- |
| `「` `『` `《` `〈` open, `」` `』` `》` `〉` close | one role each | CLDR for the corner brackets; no reversed use found for any of the eight |
| `„` | both, historically | Italian books of about 1860 to 1920 close with it; scans checked |
| `‚` `‟` `‛` | open in every convention found | a handful of closing uses in digitized text, none a convention |
| `“` `”` `‘` `’` `«` `»` `‹` `›` | both | current official sources in Latin-script languages |

The CJK verdict is an absence of evidence, and its search was the lightest of the four: no corpus was searched for reversed uses.

______________________________________________________________________

## 1. What CLDR says

`cldrquotes.py` reads the delimiters of all 766 locales in CLDR 48.2.

| mark | code | gc | opens in | closes in |
| --- | --- | --- | --- | --- |
| « | U+00AB | Pi | 146 | 4 |
| » | U+00BB | Pf | 4 | 146 |
| ‘ | U+2018 | Pi | 512 | 60 |
| ’ | U+2019 | Pf | 58 | 549 |
| ‚ | U+201A | Ps | 37 | 0 |
| “ | U+201C | Pi | 545 | 80 |
| ” | U+201D | Pf | 48 | 592 |
| „ | U+201E | Ps | 79 | 0 |
| ‹ | U+2039 | Pi | 18 | 2 |
| › | U+203A | Pf | 2 | 18 |
| 「 | U+300C | Ps | 10 | 0 |
| 」 | U+300D | Pe | 0 | 10 |
| 『 | U+300E | Ps | 10 | 0 |
| 』 | U+300F | Pe | 0 | 10 |

`《` `》` `〈` `〉` `‟` `‛` are not a quotation delimiter in any locale.
They appear only in punctuation exemplar sets, which list a locale's characters with no direction: `《` `》` `〈` `〉` for Chinese, Cantonese, Japanese, Korean and Yi, where they mark titles, `〈` `〉` also for Venetian, and `‟` for Slovenian; `‛` appears nowhere.

CLDR understates how often a mark takes its minority role, for three reasons.
It records one primary and one alternate pair per locale, so German books' `»…«` and Swiss `«…»` are not there.
It records nothing historical, which is where `„` closes.
And the JSON is resolved, so about 490 locales carry root's `“…”` and `‘…’` by inheritance, while only about 129 of the 766 set a value of their own.

Unicode's general category is no guarantee either.
In CLDR every `Ps` or `Pe` mark has one role and every `Pi` or `Pf` mark has both, which looks like a rule, but `„` and `‚` are `Ps` and both close in historical text (§3).
UAX #44 says only that `Pi` and `Pf` "may behave like opening punctuation (gc=Ps) or closing punctuation (gc=Pe), depending on usage and quotation conventions".

______________________________________________________________________

## 2. The eight two-role marks

Every minority role below was re-fetched from a current primary source and read by codepoint rather than by how it rendered.

| minority role | convention | source |
| --- | --- | --- |
| `“` closing | German `„…“` | Duden, rule D5: „Hier gefällt es mir.“ |
| `”` opening | Finnish `”…”`, the same mark at both ends | Kielitoimiston ohjepankki, *Lainausmerkit* |
| `‘` closing | German `‚…‘` | Duden, rule D12 |
| `’` opening | Finnish and Swedish `’…’` | Kielitoimisto, *Puolilainausmerkki*; Isof, question 24612 |
| `«` closing, `»` opening | Danish `»…«`; Finnish and Swedish `»…»` | Retskrivningsordbogen (2025) §58; Kielitoimisto |
| `‹` closing, `›` opening | Danish `›…‹` | Retskrivningsordbogen §58 |

Three minority roles in CLDR or Wikipedia did not survive checking, and none changes a verdict.
CLDR's Uyghur `»…«` looks like display order typed as logical order: Uyghur text on three sites stores `«` first every time.
English Wikipedia's Hebrew row, `”…„`, is display order too; the Hebrew Academy's rule is that `„` opens.
Hebrew `‘` as a closer rests on one Wikipedia example.

______________________________________________________________________

## 3. The low marks and the high-reversed marks

**`„` closes in historical Italian.**
The scans checked are De Amicis, *Il romanzo d'un maestro* (Treves, 1900, p. 189), `degli “ umiliati del villaggio. „ Quegli era un avvocato`; Belli, *Sonetti romaneschi* I (Lapi, 1886, p. 68), `“ Viènghi puro. „`; and Pascoli, *Traduzioni e riduzioni* (1923, p. 17).
A French edition, *Orgueil et Préjugé* (Geneva, 1813, p. 104), closes both `“` and `«` with `„`.
A regular-expression search of Italian Wikisource for a letter, optional punctuation and then `„` reported about 2,700 to 3,400 pages before it timed out, with some noise among them.

The print spaces the mark off; the transcriptions do not.
All three Italian pages above store it attached on Wikisource, `villaggio.„ Quegli`, `“Viènghi puro.„` and `torri!„`, checked for this note.
So the spaced form that the lone-mark rule reads correctly is the printed one, and the form a reader would actually import is the attached one.
§3.3 therefore puts `„` in the closer set as well as the opener set, which finds `villaggio.„` as a sentence end.
It costs nothing in modern text, where `„` touches the word it opens and follows a terminator in the same segment only by typo, `sagte.„ Hallo`, which then breaks with the mark at the end of the line where before it did not break at all.
`‚` stays an opener only, although it closed in one edition (below), because it is nearly indistinguishable from a comma and the closer set must not contain anything a comma could be mistaken for; how often it stands in for one was not measured.

The Unicode Standard does not say `„` always opens, probably by accident.
Versions 1.0 and 2.0 said U+201A and U+201E "may represent opening or closing quotation marks depending on which language they are used with".
Version 3.0 said instead that "U+201A and U+201B (low-9 quotation marks) are always opening", but U+201B is not a low-9 mark, and the same sentence carried a second wrong codepoint that 4.0 corrected, so U+201B looks like a slip for U+201E.
Version 7.0 spelled the codepoints out as names, which fixed the slip in place, and the current text leaves U+201E among the marks that "may represent opening or closing".
No erratum or discussion of this was found.

**`‚` closes in one scholarly edition.**
Straparola, *Le piacevoli notti* I (ed. Rua, Bologna, 1899) pairs `‘…‚`; six pages on all of Italian Wikisource match, all from that edition.

**`‟` and `‛` are rare everywhere.**
Neither is a delimiter in any CLDR locale.
`‟` opens traditional Greek nested quotations, `‟…”`.
`‛` opens a Polish alternative `‛…’`, a Bulgarian variant, and Russian lexicological quotation, `‛…’`.
Both occasionally close in German Wikisource transcriptions, `„Darf ich?‟ fragte sie` (*Die Gartenlaube*, 1888, p. 309), on 5 pages for `‟` and 22 for `‛`, which is a transcriber's habit and not a convention.
`‛` is not a backtick: it is U+201B, a quotation mark, where the backtick is U+0060, the grave accent that Markdown uses for code.
The Finnish language office names it as a look-alike to avoid: "puolilainausmerkki on ’, ei ‛ eikä '", the half quotation mark is `’`, not `‛` or `'`.
In Verdana and Tahoma, `“` and `‟` look swapped, so text typed by eye may hold either.
No frequency was measured: a Wikipedia regular-expression search for either mark times out, and its one hit on Greek Wikipedia used `‟` as an apostrophe.
`DESIGN.md` §3.3 puts both in the opener and the closer sets, as it does `“` and `‘`: the overlap costs nothing inside a segment, and it gains the break before a quotation that opens a sentence with either mark, and after the German closing `‟`.

**Unverified leads**, each uncited where it appears: Albanian `“…„`, whose own orthography rules use `„…“`; a closing low mark in old Hebrew books, where three Hebrew Wikisource hits checked all open with `„`; Portuguese `“…„`, whose Wikisource hits were OCR errors for commas; and `“…„` in 2012 NHK subtitles.

______________________________________________________________________

## 4. Guillemets

**French is the only convention that spaces them.**
Finnish writes the mark attached, "ilman välilyöntiä kiinni lainauksen aloittavaan tai lopettavaan sanaan", as does Swedish in Finland (Språkbruk), and German, "Spitze nach innen … ohne Leerraumzeichen" (Typolexikon).
Swiss French uses a narrow no-break space, or none where that is unavailable.
Danish, Hungarian, Polish and Czech were not checked at a primary source.
The languages on Wikipedia's list outside the `»…«` and `»…»` traditions all open with `«`, so a glyph reading stays correct even if one of them does space.

**A lone `»` can open in French.**
Canada's Bureau de la traduction, *Le guide du rédacteur* §7.2.5, describes "une tradition rivale" in which each continuation paragraph of a long quotation opens with `»`, and notes that many consider it "puriste et désuète"; the OQLF mentions it too.
The guide's own example types an ordinary space after that `»`, so it produces exactly a lone `»` that does not close.
In Markdown it opens a paragraph, where either reading gives the same lines.
A hard line break comes to the same thing, and the guide's own page separates its paragraphs that way, with `<br /><br />`: `DESIGN.md` §3.1 splits sections at hard breaks, so the `»` again has nothing before it.
A soft break is not a continuation at all.
A newline inside a Markdown paragraph renders as a space, so `Il a dit : « Il y a trois raisons.` then `» La première est la croissance. »` renders as one paragraph with a `»` in the middle of it, and reading that `»` as closing matches what the reader sees.

**Guillemets that are not quotation marks do little harm.**
Ditto marks and the accounting zero live in tables and lists, where a lone mark decides nothing.
Navigation arrows, `Suivant »` and `‹ Retour`, point the way the glyph reading reads them.
The one wrong case is an arrow leading a phrase after a sentence, `…disponible. » Lire la suite`, where the `»` is left at the end of the line before.

______________________________________________________________________

## 5. What a lone mark's role decides

`lonemark.py` runs §3.3's rules over plain strings.

§3.3 treats a run of lone marks between two words as one gap: the words on either side decide whether it breaks, and the marks' roles decide only where in the run the newline goes.
A wrong role can then strand a mark at the wrong end of a line, and can never add or remove a break.
Over twenty-two texts, with marks alone and side by side, every combination of readings, 120 in all, puts the same words on each line.

The run rule replaced an earlier design that decided each gap separately, with the terminator test looking back past closing marks and the capital test skipping forward past opening ones.
That design held for one mark between two words, but with marks side by side the readings moved breaks: `Il a dit. « “ Oui. ” » Puis il part.` had sixteen readings and four different layouts, and an opening mark followed by a closing one, `Il a dit. « » Puis il part.`, lost its break outright.

The roles themselves come from shape for the guillemets and for `”` and `’`, from the set for a mark in only one, and from what precedes it for the rest.
`”` and `’` joined the openers for Finnish and Swedish, which open with them, and a spaced one reads as closing because neither language spaces them; that also lands English nested quotes correctly, `He said: “ ‘ Yes. ’ ” Then he left.`
The one misplacement left is a spaced opening `“` after a sentence end, which the older rule reads as closing: `He said. “ ‘ Yes. ’ ” Then he left.` leaves the `“` at the end of the first line.

______________________________________________________________________

## Sources

- CLDR 48.2: [`cldr-misc-full` 48.2.0](https://www.npmjs.com/package/cldr-misc-full); [UAX #44 §5.7.1](https://www.unicode.org/reports/tr44/#General_Category_Values)
- The Unicode Standard: [16.0, chapter 6](https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-6/); [3.0, chapter 6](https://www.unicode.org/versions/Unicode3.0.0/ch06.pdf); [2.0, chapter 6](https://www.unicode.org/versions/Unicode2.0.0/ch06.pdf)
- German: [Duden, Anführungszeichen](https://www.duden.de/sprachwissen/rechtschreibregeln/anfuehrungszeichen); [Typolexikon](https://www.typolexikon.de/franzoesische-anfuehrungszeichen/)
- Finnish: [Kielitoimisto, Lainausmerkit](https://kielitoimistonohjepankki.fi/ohje/lainausmerkit/); [Puolilainausmerkki](https://kielitoimistonohjepankki.fi/ohje/puolilainausmerkki/)
- Swedish: [Isof, question 24612](https://frageladan.isof.se/faqs/24612); [Språkbruk, mellanrum](https://sprakbruk.fi/-/anvandningen-av-mellanrum-i-skriven-text/)
- Danish: [Retskrivningsordbogen §58](https://ro.dsn.dk/?paragraf=58&stykke=3&type=rulesearch)
- French: [Bureau de la traduction §7.2.5](https://www.btb.termiumplus.gc.ca/redac-chap?lang=fra&lettr=chapsect7&info0=7.2.5) and [§7.3](https://www.btb.termiumplus.gc.ca/redac-chap?lang=fra&lettr=chapsect7&info0=7.3); [OQLF, citation longue](https://vitrinelinguistique.oqlf.gouv.qc.ca/23206/la-redaction-et-la-communication/bibliographie-et-citations/citations/citation-longue); [OQLF, guillemets itératifs](https://vitrinelinguistique.oqlf.gouv.qc.ca/23362/la-ponctuation/guillemets/guillemets-iteratifs)
- Greek `‟`: [Nick Nicholas, Greek punctuation](https://www.opoudjis.net/unicode/punctuation.html)
- Italian scans: [De Amicis 1900](https://it.wikisource.org/wiki/Pagina:De_Amicis_-_Il_romanzo_d%27un_maestro,_Treves,_1900.djvu/197); [Belli 1886](https://it.wikisource.org/wiki/Pagina:Sonetti_romaneschi_I.djvu/380); [Pascoli 1923](https://it.wikisource.org/wiki/Pagina:Pascoli_-_Traduzioni_e_riduzioni,_1923.djvu/37); [Straparola 1899](https://it.wikisource.org/wiki/Pagina:Straparola_-_Le_piacevoli_notti_I.djvu/330)
- German transcription: [*Die Gartenlaube* 1888, p. 309](https://de.wikisource.org/wiki/Seite:Die_Gartenlaube_(1888)_309.jpg)

Read only through Wikipedia: the Imprimerie nationale's *Lexique*, Duden volume 9, *Svenska skrivregler*, the RAE's DPD, GB/T 15834, and Haralambous 2002.
The Hebrew Academy's page returned 403.
