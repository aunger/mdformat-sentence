import re
SENT = re.compile(r'[.!?](?:["\'’”])?$')

def coverage(lines):
    words, breaks = [], set()
    for i, l in enumerate(lines):
        words += l.split()
        if i < len(lines) - 1:
            breaks.add(len(words))            # gap index where the author put a newline
    ends = [j for j in range(1, len(words)) if SENT.search(words[j-1])]   # internal sentence ends
    if not ends:
        return 1.0, 0, 0                      # vacuous: all zero of them are covered
    hit = sum(1 for j in ends if j in breaks)
    return hit / len(ends), hit, len(ends)

CASES = {
 "hand sembr (clause breaks, sentence ends broken)": [
   "Because the cascade picks by width,",
   "an edit upstream can change which candidate wins,",
   "and cascade down the paragraph.",              # <- internal sentence end, IS a line break
   "The tool reports success."],
 "same text, wrapped at 62 columns": [
   "Because the cascade picks by width, an edit upstream can",
   "change which candidate wins, and cascade down the paragraph.",   # wrap lands ON the end: 1.00 by luck
   "The tool reports success."],
 "single sentence, clause-broken (no internal ends)": [
   "Because the cascade picks by width,",
   "an edit upstream can change which candidate wins."],
 "half and half": [
   "One. Two.",                                    # two ends here, only "One." is unbroken
   "Three.",
   "Four."],
}
for name, p in CASES.items():
    c, hit, tot = coverage(p)
    print(f"{c:.2f}  ({hit}/{tot})  {name}")
