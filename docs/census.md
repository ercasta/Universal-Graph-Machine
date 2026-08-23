# The machine.py census, 2026-08-22

`machine.py` is 4582 lines, 63% of `ugm/core`. Before subtracting anything from it, a
measurement of what is reachable from where. Run against the tree at `165e4d4`.

The question is not *what is unused* — the answer to that turned out to be nothing. It is
*what can a corpus reach*, because the engine's real size is the surface a corpus meets, and
everything else is substrate or scaffolding.

## Method, and the two ways the instrument lied first

Every function in `machine.py`, its line span, and a call graph over its own bodies. Then
three entry sets flooded through that graph:

    corpus       answerers, on_write hooks, vetoes -- the only ways a written fact runs Python
    loop         everything core/attention.py touches
    cli          everything __main__.py touches
    inspection   everything ONLY selftest / probes / gates touch

Both times the instrument was wrong it answered plausibly rather than failing.

**A regex caller-match excludes the calls.** The first version counted callers with
`(?<![\w.])name(?![\w])`. The guard excludes a preceding dot — which is exactly how a method
is called. It reported `_pick_expert`, `_push_frame` and `_obey` as referenced nowhere. They
are all live. Caller counting has to be AST: a method call is an `ast.Attribute`.

**The CLI is not scaffolding.** `__main__.py` was classified with the probes, which moved
`_rendered`, `save`, `replay` and their callees — 192 lines — into "reachable only from
inspection". `python -m ugm <corpus>` is a product surface. Splitting it out cut that
category from 337 lines to 145.

Sanity checks, once it was fixed: `_root`, `_count`, `_dispatch` and `_only_among_ids` come
out corpus-reachable; `_pick_expert` loop-reachable; `_rendered` cli-reachable. All correct.

## The numbers

    machine.py                            4582 lines, 4402 in 140 functions

    reachable from corpus                  885 lines   32 functions    20%
    reachable from loop                   1477 lines   62 functions
    reachable from other core / learning   1432 lines   56 functions
    reachable from cli                     418 lines   19 functions
    reachable from inspection             3903 lines  122 functions
    reachable from __init__               1890 lines   47 functions

    reachable from NOTHING                   0 lines    0 functions
    reachable ONLY from inspection         145 lines    5 functions

## What it found

**Nothing is unreachable.** No free deletions exist in `machine.py`. Whatever *shallower*
means here, it is not deleting dead code — that was the working assumption going in and it
is wrong.

**A corpus can reach a fifth of it.** 885 of 4402 lines. The rest is loop, substrate,
construction and the inspection surface.

**Five functions, 145 lines, are reachable only from the verification apparatus**:
`review` 43, `settle_structure` 40, `_recall` 40, `ask_read` 17, `reify_all` 5. Not dead,
and not obviously wrong — a verification apparatus is allowed its own handles — but nothing
on a product path calls them.

**`_recall` is reachable only from `gates/quiescence.py`.** The loop does not call it. That
is not an oversight: the table loop became the kernel and applies dormancy itself. Which
leads to the finding worth acting on.

> Since this census: that gate is gone, `_recall` had no callers left at all, and it was
> deleted (2026-08-23). The dormancy predicate below is now written twice, not three times.

**The dormant-and-not-due predicate is written three times, identically:**

    core/attention.py:209    _dormant(m, r)          the loop's copy, and the live one
    core/machine.py:1237     inside _answer_recall
    core/machine.py:2499     inside _recall          (deleted 2026-08-23)

    m._claims(m.g.rel(m.DORMANT, r.node)) and not m._claims(m.g.rel(m.DUE, r.node))

and a **fourth, different** one in `core/rules.py:507`, which tests `DORMANT` and does not
test `DUE`. That may be deliberate — it asks *did either input come from a dormant rule*
during composition, which is a different question — but it is written as though it were the
same predicate, and nothing says which it means. Worth settling before it is copied a fifth
time. This is the shape the repository has already deleted twice: a table that was debt, and
a precedence that is read rather than kept.

**The largest function in the engine is its vocabulary.** `Machine.__init__` is 650 lines —
297 code, 344 comment — containing 104 `g.atom(` calls. It is not logic; it is names and
hook wiring.

Which gives the metric that matters:

    corpus-nameable apparatus relations    120

That is the number to reduce. Lines are a proxy; **reserved names are the surface a corpus
actually meets**, and each one is a concept the engine knows about that a corpus cannot
redefine. `extends` was one of the 120 until today. `root` and `rooted` are two more that a
verified `_count` route could retire.

## Candidates, ordered by evidence

1. **The dormancy predicate, written twice** (three at census time). Deduplicate, and settle whether
   `rules.py`'s `DUE`-less variant is a fourth site or a different question wearing the same
   clothes. Small, and it removes a way to drift rather than lines.
2. **`root` / `rooted`.** `docs/wanting.md` 9.3 verified `_count` reproduces `_root`,
   denial control included. Cost is a check rewrite, not a deletion: `rooted` is in the
   vocabulary gate, `<ask-root>` is in `bundle.ugm`, and three selftest checks are written
   about the answerer rather than about rootedness. Removes two of the 120.
3. **The 145 inspection-only lines.** Not a deletion candidate on this evidence — a
   verification apparatus may legitimately have handles nothing else uses. Worth revisiting
   only if one of them turns out to duplicate something the loop does, which is how `_recall`
   surfaced -- and it has since gone from 5 functions to 4.

## What this census does not answer

It measures reachability, not necessity. A function every path reaches can still be
something a corpus should have been doing, which is the question `docs/models.md` asks and
this cannot. The two are complementary: this says where the code is, and that says what has
no business being code at all.
