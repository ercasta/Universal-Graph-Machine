#!/usr/bin/env python
"""Runner for the UGM demos — loads a `.cnl` demo file and answers the questions
embedded in it, so a demo is a single self-contained, runnable file.

    python demos/run.py                      # run every demo in this folder, in order
    python demos/run.py demos/01_basics.cnl  # run just one

A demo file is an ordinary CNL corpus (the same text you'd pass to `h.load_corpus`)
with three kinds of `#` line that this runner reads and the engine ignores as comments:

    #-- some heading            -> printed as a section header (structure only)
    #? who gets mango           -> asked with `ask_goal`, the answer printed under it
    #? [open: served] is ...    -> asked with those predicates opted into OPEN-world (OWA)

Everything else is plain CNL (facts + rules) or a plain `#` walkthrough comment.

Each question is answered against a FRESHLY loaded copy of the corpus. That is not
required in general (`ask_goal` is happy to answer many questions against one KB), but
it keeps every `why …` derivation a clean, from-scratch demand trace — otherwise a fact
already materialised by an earlier question renders as `(given)` instead of showing its
rule. Demos are tiny, so the reload is instant.
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")               # so CNL text prints on any console
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # run from a checkout, no install needed
import ugm as h

DEMOS = sorted(Path(__file__).resolve().parent.glob("[0-9]*.cnl"))


def _questions(text):
    """Yield (kind, payload) directives in file order: ('head', str) or ('ask', (open_preds, q))."""
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#--"):
            yield "head", line[3:].strip()
        elif line.startswith("#?"):
            rest = line[2:].strip()
            open_preds = frozenset()
            if rest.startswith("[open:"):
                spec, rest = rest[6:].split("]", 1)
                open_preds = frozenset(spec.replace(",", " ").split())
                rest = rest.strip()
            yield "ask", (open_preds, rest)


def run_demo(path):
    text = path.read_text(encoding="utf-8")
    print("\n" + "=" * 70)
    print(f"  {path.name}")
    print("=" * 70)
    for kind, payload in _questions(text):
        if kind == "head":
            print(f"\n  -- {payload} --")
            continue
        open_preds, q = payload
        kb, rules = h.load_corpus(text)                      # fresh load per question (see module docstring)
        answer = h.ask_goal(kb, q, rules, open_preds=open_preds)
        tag = f"   [open: {' '.join(sorted(open_preds))}]" if open_preds else ""
        print(f"\n  ?  {q}{tag}")
        for i, line in enumerate(answer):
            arrow = "  => " if i == 0 else "     "
            print(f"  {arrow}{line}")


def main(argv):
    targets = [Path(a) for a in argv] or DEMOS
    if not targets:
        print("no demo files found next to run.py")
        return 1
    for path in targets:
        if not path.exists():
            print(f"!! not found: {path}")
            continue
        run_demo(path)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
