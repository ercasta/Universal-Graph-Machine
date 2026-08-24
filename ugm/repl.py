"""A REPL: load a corpus, run to quiescence, take a line, repeat.

`ugm/__main__.py` deliberately has none of this -- it runs one corpus once
and exits, because `--save`/`--resume` were never built (see its own
docstring). This is not that. There is still no session file: the state
that would need saving is the one `Machine` this process holds, for as long
as the process runs. What a REPL adds over one run is a human answering a
tool mid-session -- `ugm/repl_fs.py`'s `approve` calls `input()` -- and
typing a NEW rule once the facts it would read already exist, which is the
"compounding" this exists to show (see `docs/tools-approval.md`).

One Loader for the whole session, not one per line: a rule named `<hold>` on
line 1 has to still resolve when line 40 writes `<producing(<hold>, ...)>`
about it, and name resolution lives on the Loader instance, not the scope
string (see `Loader.rule_nodes`).

Everything a corpus can do, this REPL asks for the same way a corpus does --
`.ugm` text, one line at a time. There used to be `:ls`/`:cleanup` shortcuts
that built `+want(...)` facts directly in Python, because a real path or
filename (colons, spaces, backslashes) could not survive the tokenizer.
Gone: the tokenizer now reads a quoted string (`core/text.py`'s lexer), so
`+want(list("C:\\Users\\ercas\\Documents"))` is ordinary, typeable `.ugm`
text, and `<list>` (`ugm/rules/fs/fs_demo.ugm`) is the tool -- driven by the
engine, not by a REPL command that knew what a directory listing meant.

## Typing at this prompt is talking on a channel, not authoring

A `fact` is standing knowledge; what a PERSON types is an utterance, and
§13 says an arrival is not a belief until a rule trusts it -- the same
distinction the engine already draws for every other channel. So a bare
line (`+want(list("..."))`) is wrapped as `say user: <line>` before it
reaches the loader, and `TRUST_USER` below is the rule that turns it into
a belief -- unconditional, because the person at the keyboard IS the
authority a REPL exists to ask. It is an ORDINARY rule, loaded like any
other: replace it (or add a condition to it) in your own corpus and the
REPL's trust in `user` is whatever you wrote, not a hidden default.

`/godmode` and `/usermode` switch which one a line IS, for every line until
the other is typed -- an explicit, visible session state (the prompt shows
it), not sniffed per line from what the text happens to start with. In
user mode a line can only ever be a proposition (`say` reads nothing else);
authoring a rule live needs `/godmode` first.

## Autocorrect is against the CORPUS's own vocabulary, and only ever a
## name -- never a quote, a variable or a rule reference

A typo in a relation name does not fail loudly: it mints a fresh atom,
same as any other word, and `gates.vocabulary` exists to catch that AFTER
the fact by reading `nothing writes this`. At the keyboard the fix is
closer to hand -- every relation name the loaded rules and facts already
use, at any nesting depth (`_vocabulary`), is a known word, and a typed
word that is not one gets corrected to the nearest known word IF exactly
one is nearest and close enough (`_LEVENSHTEIN_MAX`). Ambiguous (two
words equally close) or too far: left alone, so the loader's own error is
what a genuinely new word gets, same as always. Printed either way -- an
autocorrect that changed what you typed without saying so would be a
worse trap than the typo. `"quoted text"`, `$variables` and `<rule refs>`
are never touched: a filename is not vocabulary.
"""

import re
import sys
from typing import Optional, TextIO

from .core.machine import Machine
from .core.text import Loader, ParseError, _LINE_FORM_STOPS

# A quoted string, a `<rule reference>`, a `$variable` -- consumed whole and
# never corrected -- or a bare name, which might be.
_SPAN = re.compile(r'"(?:[^"\\]|\\.)*"|<[^>]*>|\$[A-Za-z_][A-Za-z0-9_-]*'
                    r'|[A-Za-z_][A-Za-z0-9_-]*')
_LEVENSHTEIN_MAX = 2

# The surface's OWN vocabulary -- statement keywords (`_LINE_FORM_STOPS`,
# reused so this stays in sync with the parser rather than drifting), plus
# everything else `Parser` dispatches on by spelling: connectives,
# bindings, postcondition ops. None of it is domain vocabulary and none
# of it may ever be a correction target -- `fact +wnat(...)` mangling
# `fact` itself into `want` (found live: `wnat` IS closer to `want` than
# `fact` is to anything else) is exactly the failure this guards.
_GRAMMAR_WORDS = _LINE_FORM_STOPS | {
    "no", "as", "at", "implies", "causes", "extends", "alt",
    "stop", "attend", "unattend", "push", "pop",
    "merge", "unmerge", "destroy", "label", "unlabel", "forget",
}


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1,
                         prev[j - 1] + (ca != cb))
        prev = cur
    return prev[-1]


def _vocabulary(m: Machine) -> "set[str]":
    """Every relation name the loaded rules and facts use, at ANY nesting
    depth -- unlike `Machine.web`, which only looks at the top of each
    antecedent/consequent pattern and so misses `list` in `want(list($d))`.

    `m._bookkeeping` (the same filter `_visible` prints through) is
    excluded: every loaded rule deposits `rule(<name>)`/`ant(...)`/`con(...)`
    as ordinary believed facts (§ a rule is a node), so without this,
    `ant` -- never something a person means to type -- sits in the
    vocabulary and ties `want` at distance 2, refusing a correction that
    would otherwise be unambiguous. Measured, not guessed: this is exactly
    the failure `_wnat_ -> want` hit before the filter was added.
    """
    out: "set[str]" = set()

    def collect(node) -> None:
        rel = m.g.relation_of(node)
        if rel is not None and not m.g.is_var(rel) and rel not in m._bookkeeping:
            out.add(m.g.show(rel))
        for mm in m.g.members(node):
            collect(mm)

    for r in m.rules.rules:
        for x in r.antecedent:
            collect(x.pattern)
        for x in r.consequent:
            collect(x.pattern)
    for p in m.pad.believed():
        collect(p)
    return out


def _autocorrect(line: str, vocab: "set[str]"):
    """`(corrected_line, [(typed, fixed), ...])`. Only a bare name span is
    ever a candidate; see `_SPAN`."""
    corrections = []
    out = []
    last = 0
    for match in _SPAN.finditer(line):
        text = match.group()
        out.append(line[last:match.start()])
        last = match.end()
        if (text[0] in ('"', "<", "$") or text in vocab
                or text in _GRAMMAR_WORDS or len(text) <= 2):
            out.append(text)
            continue
        best, best_dist, ties = None, _LEVENSHTEIN_MAX + 1, 0
        for word in vocab:
            d = _levenshtein(text, word)
            if d < best_dist:
                best, best_dist, ties = word, d, 1
            elif d == best_dist:
                ties += 1
        if best is not None and best_dist <= _LEVENSHTEIN_MAX and ties == 1:
            out.append(best)
            corrections.append((text, best))
        else:
            out.append(text)
    out.append(line[last:])
    return "".join(out), corrections

# `no trusted($p)` is not optional. Without it this rule matches the same
# `says(user, $p)` -- which nothing ever retracts, an utterance stays said
# -- forever, winning arbitration every tick without producing anything
# new and starving every other rule out. Same discipline as
# `fs_demo.ugm`'s `<flag-stale>`: the guard is consumed in the SAME firing
# that acts on it, not a later stage.
TRUST_USER = ('rule <trust-user> = implies( { +says(user, $p), no trusted($p) }, '
              '{ +$p, +trusted($p) } )')

HELP = """\
/show      what is believed right now
/load PATH load another .ugm file into this session
/godmode   author directly -- a line is `.ugm` text (fact, rule, say, ...)
/usermode  back to the default -- a line is what you're SAYING
/quit      leave

Starts in user mode: a line is wrapped as `say user: <line>` and believed
only because <trust-user> (loaded at start) trusts this channel
unconditionally -- an ORDINARY rule, replaceable in your own corpus. A path
or filename needing a space or a backslash is a quoted string: "like this",
never autocorrected. A misspelled relation name IS -- against whatever the
loaded rules already use -- and it's echoed (`~ typed -> fixed`), never
silent. Extra spacing between tokens has always been ignored.
example:  +want(list("C:\\Users\\ercas\\Documents"))
"""


def _visible(m: Machine, p) -> bool:
    return m.g.relation_of(p) not in m._bookkeeping


def run(m: Machine, ldr: Loader, limit: int = 400,
        prompt: str = "ugm", stdin: Optional[TextIO] = None,
        echo_prompt: bool = True) -> int:
    stdin = stdin or sys.stdin
    ldr.load(TRUST_USER)
    print(HELP)
    seen = set(m.pad.believed())
    god = False

    def settle(label: str = "") -> None:
        nonlocal seen
        steps = m.run(limit=limit)
        now = set(m.pad.believed())
        for p in sorted(now - seen):
            if _visible(m, p):
                print(f"  + {m.g.show(p)}")
        for p in sorted(seen - now):
            if _visible(m, p):
                print(f"  - {m.g.show(p)}")
        seen = now
        ended = steps[-1].state if steps else "nothing to do"
        print(f"  ({len(steps)} ticks{label}, ended {ended})")

    while True:
        if echo_prompt:
            sys.stdout.write(f"{prompt}{'[god]' if god else ''}> ")
            sys.stdout.flush()
        line = stdin.readline()
        if line == "":
            break
        line = line.strip()
        if not line:
            continue
        if line in ("/q", "/quit", "/exit"):
            break
        if line == "/show":
            for p in sorted(seen):
                if _visible(m, p):
                    print(f"  {m.g.show(p)}")
            continue
        if line == "/godmode":
            god = True
            print("  authoring directly -- /usermode to go back")
            continue
        if line == "/usermode":
            god = False
            print("  back to talking on the `user` channel")
            continue
        if line.startswith("/load "):
            path = line[6:].strip()
            with open(path, "r", encoding="utf-8") as fh:
                ldr.load(fh.read())
            settle()
            continue
        line, corrections = _autocorrect(line, _vocabulary(m))
        for typed, fixed in corrections:
            print(f"  ~ {typed} -> {fixed}")
        if not god:
            line = f"say user: {line}"
        try:
            ldr.load(line)
        except ParseError as e:
            print(f"  ! {e}")
            continue
        settle()
    return 0
