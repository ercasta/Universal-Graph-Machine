"""`ugm.repl`'s autocorrect: a typo in a relation name gets fixed against
the CORPUS's own vocabulary; a quote, a variable or a rule reference never
does; an ambiguous typo is left alone rather than guessed.

    python -m ugm.probes.autocorrect

Outside `ugm.selftest` on purpose -- `repl.py` is REPL interaction, not the
engine `selftest`'s own docstring scopes itself to.
"""

from ..repl import _autocorrect, _levenshtein, _vocabulary
from ..core.machine import Machine
from ..core.text import load

CORPUS = """
    rule <list> = implies( { +want(list($dir)) },
                           { +ls($dir), -want(list($dir)) } )
    rule <flag> = implies( { +file($dir, $name), +size($dir, $name, $s),
                             +created($dir, $name, $c) },
                           { +checked($dir, $name) } )
"""


def main() -> int:
    failed = 0

    def check(name: str, ok: bool) -> None:
        nonlocal failed
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        failed += not ok

    check("levenshtein of equal strings is 0", _levenshtein("want", "want") == 0)
    check("levenshtein counts one substitution", _levenshtein("wart", "want") == 1)
    check("levenshtein of a transposition is 2 (no swap operation)",
          _levenshtein("wnat", "want") == 2)

    m = Machine()
    load(m, CORPUS)
    vocab = _vocabulary(m)
    check("vocabulary reaches a NESTED relation head -- `list`, one level "
          "inside `want(list($dir))` -- not just the top of the pattern",
          {"want", "list", "ls"} <= vocab)
    check("machinery bookkeeping (`ant`/`con`/`rule`, deposited for every "
          "loaded rule) is excluded, so it cannot tie a real word and "
          "block a correction",
          not ({"ant", "con", "rule"} & vocab))

    fixed, corr = _autocorrect("+wnat(list($d))", vocab)
    check("an unambiguous typo is corrected...",
          fixed == "+want(list($d))" and corr == [("wnat", "want")])

    fixed, corr = _autocorrect('+file(d, "wnat.txt")', vocab)
    check("...and a quoted string of the SAME text never is -- a filename "
          "is not vocabulary",
          fixed == '+file(d, "wnat.txt")' and corr == [])

    fixed, corr = _autocorrect("+lsit($d)", vocab)
    check("`list` and `ls` tie at the same distance from `lsit` -- left "
          "alone rather than guessed, same as a genuinely new word",
          fixed == "+lsit($d)" and corr == [])

    fixed, corr = _autocorrect("+want(<list>, $x)", vocab)
    check("a rule reference is never a candidate, however close its "
          "spelling reads to a relation name",
          fixed == "+want(<list>, $x)" and corr == [])

    fixed, corr = _autocorrect('fact +wnat(list("x"))', vocab)
    check("the STATEMENT KEYWORD is never a candidate either -- found "
          "live: `wnat` reads closer to `want` than `fact` does to "
          "anything, and without this guard `fact` mangled into `want` "
          "and the line stopped parsing at all",
          fixed == 'fact +want(list("x"))'
          and corr == [("wnat", "want")])

    print(f"\n{failed} failing")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
