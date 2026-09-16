# Notes

Working material behind `DESIGN.md`. Nothing here is normative.

`DESIGN.md` is the specification and stands alone; these are the corpus and the
throwaway programs that produced the numbers quoted in it, kept so that anyone
can re-run them rather than take them on trust.

| | |
| --- | --- |
| `PRESERVE-MODE.md` | Why the plugin does not try to preserve an author's existing line breaks. The longest-running open question about this design, answered. |
| `corpus/` | The one corpus that gives honest answers about layout heuristics, and why. |
| `experiments/` | Eleven short programs. Five need mdformat, six are stdlib only. |

## Running them

```
python3 -m venv v && ./v/bin/pip install 'mdformat==1.0.0'
./v/bin/python notes/experiments/probe.py
```

Pin mdformat to 1.0.0. Every seam fact in `DESIGN.md` §2 was measured against
that version, and the wrap-point mechanics these programs depend on are internal
to it.

| program | needs mdformat | what it establishes |
| --- | --- | --- |
| `probe.py` | yes | What reaches the `POSTPROCESSORS["inline"]` seam under each `--wrap` mode. Zero wrap points under `keep`, 44 under `no` and under an integer width. |
| `handwritten.py` | yes | `--wrap no` collapses a hand-broken paragraph to one line before any plugin sees it. The basis of `DESIGN.md` §2.5's warning. |
| `addonly.py` | yes | The author's line breaks survive to the seam as `softbreak` children on pass 1 and are gone on pass 2. |
| `proto.py` | yes | A working add-only postprocessor. Idempotent, width-independent, and not a pure function of the text. |
| `proto2.py` | yes | The same harness with a pluggable decision function. The shape every later experiment varies. |
| `breaks.py` | no | **41% of real sembr line breaks carry no punctuation at all.** A break-word list recovers 11 of 31; 27% of all breaks stay undetectable. The reason rule 5 cannot be recovered from layout. |
| `triage2.py` | no | Sentence coverage separates hand sembr from geometric wrapping perfectly on this corpus: 1.00 against 0.00. |
| `cov.py` | no | What "coverage" means, on worked cases, including a width-wrapped paragraph that scores 1.00 by coincidence. |
| `thresh.py` | no | Any coverage *threshold* reintroduces paragraph-sized diffs: one edit, 18 changed lines. |
| `k0.py` | no | At a threshold of exactly zero, appending a sentence is safe (1 diff line) but removing a sentence break is not (8 lines, all clause breaks lost). |
| `edit.py` | no | Rewrapping a paragraph versus adding only the missing break: 9 diff lines against 1, 0 clause breaks surviving against 4. |
| `lic.py` | no | Every plugin in mdformat's curated list is MIT, and so is mdformat. |

The programs are throwaway quality on purpose. They exist to produce a number
once, not to become a test suite. `DESIGN.md` §6 specifies the real gate.
