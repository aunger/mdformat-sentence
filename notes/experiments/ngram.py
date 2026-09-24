import json, re, time, urllib.parse, urllib.request, statistics
URL="https://books.google.com/ngrams/json"
def q(c,y0=1990,y1=2019):
    p=urllib.parse.urlencode({"content":c,"year_start":y0,"year_end":y1,"corpus":"en-2019","smoothing":3})
    with urllib.request.urlopen(f"{URL}?{p}",timeout=45) as r: return json.load(r)
def series(c):
    try: d=q(c)
    except Exception: return {}
    return {e["ngram"]: statistics.mean(e["timeseries"]) for e in d
            if e.get("type")!="NGRAM_COLLECTION" and e.get("timeseries")}
def digit_share(tok):
    """Of the TOP TEN continuations of '<tok>', what share are numerals?

    Google's wildcard returns only the ten commonest substitutions and omits
    punctuation from them, so this is a share of that top ten and not of all
    occurrences of the token.
    """
    s = series(f"{tok} *")
    if not s: return None, 0, 0, ""
    tot = sum(s.values()) or 1
    pat = re.escape(tok) + r" (\d+|[IVXLCDM]{1,4})"
    dig = sum(v for k,v in s.items() if re.fullmatch(pat, k))
    n   = sum(1 for k in s if re.fullmatch(pat, k))
    top = ", ".join(k[len(tok)+1:] for k,_ in sorted(s.items(), key=lambda x:-x[1])[:5])
    return 100*dig/tot, n, len(s), top
def noun_use(tok):
    """'a X' + 'the X' -- only a count noun takes these. Single tokens only."""
    if " " in tok: return float("nan")
    s = series(f"a {tok}"); s.update(series(f"the {tok}"))
    return sum(s.values())

# "et al", not bare "al": the abbreviation only separates from "al Qaeda" and
# "al dente" in the bigram, which is 100% numerals against the bare token's 44%.
print(f"{'token':6s} {'numerals, top ten':>20s}   {'used as a noun':>14s}   commonest continuations")
for tok in ["Fig","fig","No","no","Vol","Ch","Sec","sec","vs","St","Dr","et al"]:
    d, k, tot, top = digit_share(tok); time.sleep(1.2)
    n = noun_use(tok); time.sleep(1.2)
    ds = f"{d:.0f}% ({k}/{tot})" if d is not None else "n/a"
    print(f"{tok:6s} {ds:>20s}   {n:14.2e}   {top[:46]}")
