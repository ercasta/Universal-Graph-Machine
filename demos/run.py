#!/usr/bin/env python
"""Runner for the UGM demos — loads a `.cnl` demo file and answers the questions
embedded in it, so a demo is a single self-contained, runnable file.

    python demos/run.py                      # run every demo in this folder, in order
    python demos/run.py demos/01_basics.cnl  # run just one

A demo file is an ordinary CNL corpus (the same text you'd pass to `h.load_corpus`) — a
question is a BARE line, no special marker. What a line IS (fact / rule / question) is
decided the same way `ingest` decides it: by which recognition FORM fires, never a
runner-side sniff. `is alice gets mango` is recognized as a question because `is` leads;
`alice is a customer` is a fact because the subject leads — word order alone disambiguates
(`ugm.cnl.query.recognize`, the same function `ingest` calls). Each recognized question line
is pulled OUT of the corpus text before it reaches `load_corpus` (see `_directives`) — it is
answered, not loaded as content. This runner only adds:

    #-- some heading            -> printed as a section header (structure only, not CNL)
    [open: served] is ...       -> the question that follows, with `served` opted into
                                   OPEN-world (OWA). This bracket is NOT CNL: which predicates
                                   are open is a caller-side POLICY (`FirmwarePolicy`), not
                                   domain content, so it can't be "native" CNL any more than a
                                   command-line flag can (see `docs/architecture.md` §6).

Everything else is either plain CNL (facts + rules) or a plain `#` walkthrough comment.

Each recognized question is answered against a FRESHLY loaded copy of the corpus. That is
not required in general (`ingest`/`ask_goal` are happy to answer many questions against one
KB — see demo 6), but it keeps every `why …` derivation a clean, from-scratch demand trace —
otherwise a fact already materialised by an earlier question renders as `(given)` instead of
showing its rule. Demos are tiny, so the reload is instant.
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


def _directives(text):
    """Parse `text` into (content, directives). `content` is the CNL corpus text with every
    recognized-question line blanked out (a blank line changes nothing `load_corpus` sees, so
    line numbers still line up for any error message). `directives` is the ('head', str) /
    ('ask', (open_preds, q)) list in file order.

    A line is a QUESTION iff `h.recognize` fires on it — the same test `ingest` uses, not a
    runner-side keyword. It MUST be excluded from `content`: a generic fact form is declared
    over the SAME base relations a question asks about (`X in Y`, `X is Y`, ...), so a bare
    question line left in the corpus text can double as a spurious FACT (`who in north_america`
    would mint a node literally named `who`) — recognition alone can't arbitrate that inside
    `load_corpus`, which folds a whole text at once rather than routing one utterance at a time
    (`ingest` avoids exactly this by checking `recognize` BEFORE `load_facts`, per utterance).
    A leading `[open: ...]` is stripped before recognition (policy, not CNL, §module docstring)."""
    lines, directives = [], []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#--"):
            directives.append(("head", line[3:].strip()))
            lines.append(raw)
            continue
        if not line or line.startswith("#"):
            lines.append(raw)
            continue
        open_preds = frozenset()
        q = line
        if q.startswith("[open:"):
            spec, q = q[6:].split("]", 1)
            open_preds = frozenset(spec.replace(",", " ").split())
            q = q.strip()
        if h.recognize(q) is not None:
            directives.append(("ask", (open_preds, q)))
            lines.append("")                                  # excluded from the corpus content
        else:
            lines.append(raw)
    return "\n".join(lines), directives


def run_demo(path):
    text = path.read_text(encoding="utf-8")
    content, directives = _directives(text)
    print("\n" + "=" * 70)
    print(f"  {path.name}")
    print("=" * 70)
    for kind, payload in directives:
        if kind == "head":
            print(f"\n  -- {payload} --")
            continue
        open_preds, q = payload
        kb, rules = h.load_corpus(content)                    # fresh load per question (see module docstring)
        policy = h.FirmwarePolicy(open_preds=open_preds) if open_preds else None
        outcome = h.ingest(kb, rules, q, policy=policy)       # the native question-answering entry point
        tag = f"   [open: {' '.join(sorted(open_preds))}]" if open_preds else ""
        print(f"\n  ?  {q}{tag}")
        for i, line in enumerate(outcome.answer):
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
