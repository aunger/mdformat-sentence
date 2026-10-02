"""camelCase sentence openers in English documentation: DESIGN.md §3.3.

For every gap inside paragraph prose where the left segment ends in a
terminator (. ! ?) plus optional closers, record whether the next word is
camelCase (lowercase start, a capital later: iOS, gRPC) or another lowercase
word, and which of the shipped join rules would already suppress the break.

Needs markdown-it-py (installed with mdformat) and the corpora, cloned with
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 into one directory DIR as:

  mdn      https://github.com/mdn/content                 b60c5dad  (files/en-us)
  ghdocs   https://github.com/github/docs                 2eaab0b   (content)
  vscode   https://github.com/microsoft/vscode-docs       250ea55
  flutter  https://github.com/flutter/website             ab59c61   (sites/docs)
  rn       https://github.com/facebook/react-native-website  f5d7ce0  (docs, blog)
  xamarin  https://github.com/MicrosoftDocs/xamarin-docs   0506e3b   (docs)
  dotnet   https://github.com/dotnet/docs                 91cc9093  (docs)

Run: python3 camelcase.py DIR. It prints the totals and writes records.jsonl,
totals.json and cameltok.json into DIR. 113 camelCase positions in 13.0
million words; camelcase.tsv beside this file holds them with the verdict
each was given by reading it: 111 real sentence ends, and two `eg.` inside
parentheses, where bracket depth blocks the break anyway.
"""
import json, os, re, sys
from markdown_it import MarkdownIt

ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else sys.exit("usage: camelcase.py DIR")
CORPORA = {
    "mdn": os.path.join(ROOT, "mdn/files/en-us"),
    "ghdocs": os.path.join(ROOT, "ghdocs/content"),
    "vscode": os.path.join(ROOT, "vscode"),
    "flutter": os.path.join(ROOT, "flutter/sites/docs"),
    "rn": os.path.join(ROOT, "rn"),
    "xamarin": os.path.join(ROOT, "xamarin/docs"),
    "dotnet": os.path.join(ROOT, "dotnet/docs"),
}

md = MarkdownIt("commonmark").enable("table").enable("strikethrough")

OPAQUE = "▯"  # ▯ placeholder for code span / image / autolink / macro
CLOSERS = set("\"'’”»›«‹“‘‟‛„*_~")
OPENERS = set("\"'“‘‟‛«‹»›¿¡„‚*_~[(\\")
ABBRX = set("""etc inc ltd co corp llc plc eg ie cf approx incl esp al ca vs v ver
dept fig figs no nos vol vols ch sec secs pp p pg min max est ext misc ref resp avg eq
ex jan feb mar apr jun jul aug sep sept oct nov dec mon tue wed thu fri sat sun
attn govt univ assn bros dist div intl natl mt ft hr hrs yr yrs mo mos wk
op ed eds repr rev trans viz sq mr mrs ms dr prof sr jr st""".split())
UNCOND = {"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs"}
COND = {"fig", "no", "vol", "ch", "sec"}
DOTTED = re.compile(r"(?:[^\W\d_]+\.)+[^\W\d_]+")
CAMEL = re.compile(r"[a-z]+[A-Z][A-Za-z0-9]*")
LOWERWORD = re.compile(r"[a-z][a-z0-9]*")
FOOTREF = re.compile(r"(\[\^[^\]\s]+\])+$")
FRONT = re.compile(r"\A---\n.*?\n---[ \t]*(?:\n|\Z)", re.S)

GLOSSARY = re.compile(r"\{\{\s*[Gg]lossary\(\s*\"([^\"]*)\"(?:\s*,\s*\"([^\"]*)\")?[^}]*\}\}")
MACRO = re.compile(r"\{\{.*?\}\}", re.S)
LIQ_DATA = re.compile(r"\{%-?\s*(?:data|octicon)\b.*?-?%\}", re.S)
LIQ_OTHER = re.compile(r"\{%.*?%\}", re.S)
KB = re.compile(r"\bkb\([^)]*\)")
DOCFX = re.compile(r":::[^\n]*?:::")


def inline_to_text(tok):
    out = []
    skip_autolink = False
    for c in tok.children or []:
        t = c.type
        if skip_autolink:
            if t == "link_close":
                skip_autolink = False
            continue
        if t == "text":
            out.append(c.content)
        elif t in ("softbreak", "hardbreak"):
            out.append("\n")
        elif t in ("code_inline", "image"):
            out.append(OPAQUE)
        elif t == "link_open":
            if c.markup == "autolink" or c.info == "auto":
                out.append(OPAQUE)
                skip_autolink = True
            else:
                out.append("[")
        elif t == "link_close":
            out.append("]")
        elif t in ("em_open", "em_close", "strong_open", "strong_close", "s_open", "s_close"):
            out.append(c.markup)
        elif t == "html_inline":
            pass  # drop tags, keep surrounding/inner text
        else:
            out.append(c.content or "")
    s = "".join(out)
    s = GLOSSARY.sub(lambda m: m.group(2) or m.group(1), s)
    s = MACRO.sub(OPAQUE, s)
    s = LIQ_DATA.sub(OPAQUE, s)
    s = LIQ_OTHER.sub("", s)
    s = KB.sub(OPAQUE, s)
    s = DOCFX.sub(OPAQUE, s)
    return s


def delta(seg):
    d = 0
    for ch in seg:
        if ch in "[(":
            d += 1
        elif ch in "])":
            d -= 1
    return d


def lstrip_openers(s):
    i = 0
    while i < len(s) and (s[i] in OPENERS or s[i] == " "):
        i += 1
    return s[i:]


from collections import Counter as _C
CAMELTOK = _C()


def analyse_para(text, corpus, path, recs, tot):
    segs = [s for s in re.split(r"[ \t\n]+", text) if s]
    # character offsets for context
    offs = []
    pos = 0
    for s in segs:
        j = text.index(s, pos)
        offs.append(j)
        pos = j + len(s)
    tot["words"] += len(segs)
    for s_ in segs:
        w_ = lstrip_openers(s_)
        if w_ and w_[0].islower():
            tot["tok_lower"] += 1
            if CAMEL.match(w_):
                tot["tok_camel"] += 1
                CAMELTOK[CAMEL.match(w_).group(0)] += 1
    depth = 0
    for i in range(len(segs) - 1):
        depth = max(0, depth + delta(segs[i]))
        P = FOOTREF.sub("", segs[i])
        k = len(P)
        while k > 0 and P[k - 1] in CLOSERS:
            k -= 1
        core = P[:k]
        closers = P[k:]
        m = re.search(r"[.!?]+$", core)
        linkclose = False
        if not m:
            # terminator at the end of link text: `[The docs.](u) Next` -> `docs.]`
            c2 = core.rstrip("]")
            if c2 == core:
                continue
            k2 = len(c2)
            while k2 > 0 and c2[k2 - 1] in CLOSERS:
                k2 -= 1
            core = c2[:k2]
            m = re.search(r"[.!?]+$", core)
            if not m:
                continue
            linkclose = True
        term_run = m.group(0)
        term = term_run[-1]
        at = lstrip_openers(core[:-1])
        # follower: skip segments made only of openers
        j = i + 1
        N = lstrip_openers(segs[j])
        openers = segs[j][: len(segs[j]) - len(N)]
        while not N and j + 1 < len(segs):
            j += 1
            N = lstrip_openers(segs[j])
        if not N:
            continue
        ch = N[0]
        if ch == OPAQUE:
            cls = "opaque"
        elif ch.isdigit() or (ch.isalpha() and not ch.islower()):
            cls = "pass"
        elif CAMEL.match(N):
            cls = "camel"
        elif ch.islower():
            cls = "lower"
        else:
            cls = "other"
        pre = "lc_" if linkclose else ""
        tot[pre + "cand_" + cls] += 1
        tot[pre + "cand_" + cls + "_" + corpus] += 1
        if cls not in ("camel", "lower") and not (term == "." and re.sub(r"^[^\w]+|[^\w]+$", "", at).lower() in ABBRX):
            continue
        # which existing rules already join here?
        rules = []
        if linkclose:
            rules.append("linkclose")
        if depth > 0:
            rules.append("bracket")
        if term == ".":
            if term_run == "...":
                rules.append("ellipsis")
            al = at.lower()
            if al in UNCOND:
                rules.append("abbr:" + al)
            if DOTTED.fullmatch(at):
                rules.append("dotted")
            if len(at) == 1 and at.isalpha() and at.isupper():
                rules.append("initial")
            if al in COND:
                rules.append("cond:" + al)  # follower opens lowercase -> joined
        word = (CAMEL.match(N) or LOWERWORD.match(N))
        word = word.group(0) if word else N
        a = max(0, offs[i] - 70)
        b = min(len(text), offs[j] + len(segs[j]) + 50)
        ctx = text[a:b].replace("\n", " ")
        recs.append(dict(corpus=corpus, path=os.path.relpath(path, ROOT), cls=cls,
                         term=term_run, at=at, prev=segs[i], word=word, next=segs[j],
                         depth=depth, rules=rules, closers=closers, openers=openers, ctx=ctx))


def main():
    from collections import Counter
    tot = Counter()
    recs = []
    for corpus, base in CORPORA.items():
        for dp, dn, fn in os.walk(base):
            if "/.git" in dp or "/release/release-notes" in dp:
                continue  # flutter release notes are generated PR-title lists
            for f in fn:
                if not f.endswith(".md"):
                    continue
                p = os.path.join(dp, f)
                try:
                    src = open(p, encoding="utf-8").read()
                except Exception:
                    tot["unreadable"] += 1
                    continue
                src = FRONT.sub("", src.lstrip("\ufeff").replace("\r\n", "\n"))
                tot["files_" + corpus] += 1
                toks = md.parse(src)
                for k, t in enumerate(toks):
                    if t.type == "inline" and k > 0 and toks[k - 1].type == "paragraph_open":
                        tot["paras_" + corpus] += 1
                        before = tot["words"]
                        analyse_para(inline_to_text(t), corpus, p, recs, tot)
                        tot["words_" + corpus] += tot["words"] - before
    with open(os.path.join(ROOT, "records.jsonl"), "w") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(dict(tot), open(os.path.join(ROOT, "totals.json"), "w"), indent=1, sort_keys=True)
    json.dump(CAMELTOK.most_common(), open(os.path.join(ROOT, "cameltok.json"), "w"))
    print(json.dumps(dict(sorted(tot.items())), indent=1))


if __name__ == "__main__":
    main()
