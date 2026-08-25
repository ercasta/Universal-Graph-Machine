# UGM — Universal Graph Machine

**An agent that plans, acts and explains itself — where almost nothing about reality is built into
the engine.**

> **New here? Start with the [illustrated tutorial](https://ercasta.github.io/Universal-Graph-Machine/)**
> — a plain-language, mobile-friendly book that teaches the machine from scratch, with live pages
> that run the real engine in your browser. The rest of this README is the technical overview; the
> full argument (some of it now aspirational — see below) is
> [`docs/rules-design.md`](docs/rules-design.md).

UGM is a self-contained Python library with no dependencies.

```bash
python -m ugm.selftest                              # 203 checks, 0 failing
python -m ugm ugm/rules/delay.ugm --ask "owed(ana,money)"
```

## Try it: HarneSkills is the door onto this engine

This repo is the engine only. The REPL — talk to it, one `.ugm` line at a time, typo-correction
against the loaded corpus's own vocabulary, a plain-English fallback for a line that isn't `.ugm`
syntax — has moved to **[HarneSkills](https://github.com/ercasta/harneskills)**, a small separate
repo that depends on this one rather than duplicating it:

```bash
pip install -e .              # this repo, editable
pip install -e ../harneskills # or wherever your checkout lives
harneskills-fs
```

```
harneskills> cleanup "C:\Users\you\Documents" 7
approve rename(notes.txt -> stale-notes.txt)? [y/N]
```

`harneskills-fs` is HarneSkills' own worked example — three file tools, a rename held for approval,
a circuit breaker watching it — none of it built into the engine, all of it ordinary `.ugm` rules
(`harneskills/examples/fs/fs_demo.ugm`). Nothing about "showing" a directory or "cleaning up" old
files is built into the REPL or the tools — a plain-English line means whatever an ordinary rule in
the loaded corpus says it means, and a rename is held for approval by the same write-time trigger
any corpus could use, not a special case in the engine.

## How it works: a loop, some lanes, and rules

**One graph is the whole state.** Nodes with ordered members and nothing else — `on(a, b)` is a
node, `a` and `b` are nodes, an atom and a compound are the same kind of thing. Belief is
presence: `believed(p)` holds or it doesn't, and that is the entirety of what "believing something"
means here. A member of a rule is signed `+` (assert), `-` (erase) or `no` (absence — *nothing
claims this*, told apart from a denial). There is no fourth sign and no provenance trail attached to
a belief; that machinery existed once and was cut for being more than the measured wins justified.

**One connective.** `rule <name> = implies( { antecedent }, { consequent } )` — `causes` is refused
at load, on purpose, with a message saying why: it only ever meant *lands in a later moment*, and
there are no moments to land in.

**The loop has no phases.** Each tick: score every rule, take the first whose antecedent matches
against current belief, apply it (write what it asserts, erase what it retracts), repeat. A run ends
*quiescent* (nothing matches any more) or hits a tick limit. Nothing in the loop is privileged —
*stop* is a rule spending a postcondition, not an engine decision.

**Lanes** let a corpus run more than one such pass per round. `fact +lane(<R>, watchdog)` puts a
rule in its own lane, which gets a turn every round independent of what the default (`main`) lane
selects that tick — the reason a rule that always wins `main`'s arbitration cannot starve out a
watchdog meant to rein it in (see `ugm/rules/circuit_breaker.ugm`).

**Triggers** (`intercepts`/`producing`/`instead`/`drop`) let a rule see what another rule is about
to conclude, before it lands, and add beside it, replace it, or drop it. This is the whole of how
approval-gating and starvation-breaking are built — ordinary rules, no engine hook per feature.

**Tools and channels are the seam to the world.** `kb.answerer(name, request, fn)` binds a Python
function to a relation; writing that relation calls it, and its answer lands as `answered(<tool>,
req, result)` — a record the corpus may believe or not, never a conclusion the tool makes for it.
`say user: +p` delivers an arrival (`arrived`/`says`), and an ordinary trust rule — the REPL loads
one for `user`, unconditional — is what turns an arrival into a belief. Nothing is trusted by
default.

**A rule is a node.** `overrides(<a>, <b>)` is defeat (the loser never applies), `standing(<r>)`
lifts a rule's priority, `dormant`/`due` suspend and resume it — all ordinary facts a corpus writes
and a rule can ask about.

## What it looks like

```
rule <cancel>     = implies( { +cancelled($f) }, { +disrupted($f) } )
rule <crewing>    = implies( { +cause($f, crew) }, { -extraordinary($f) } )
rule <compensate> = implies(
    { +disrupted($f), +booked($p, $f), -extraordinary($f) },
    { +owed($p, money) } )

fact +cancelled(bl204)
fact +cause(bl204, crew)
fact +booked(ana, bl204)
```

```
$ python -m ugm ugm/rules/delay.ugm --ask "owed(ana,money)"
ugm/rules/delay.ugm: 25 ticks, ended quiescent

what it believes, newest first:
  rerouted(ana, zr9)
  amount(ana, 600)
  owed(ana, money)
  ...

owed(ana,money): believed
```

## Layout

```
ugm/
  core/          9 modules   graph, chain, gate, machine (the loop, lanes, triggers), rules
                              (match/arbitrate), text (the .ugm surface), attention, channels,
                              scratchpad -- nothing outside `core` is needed to run an agent
  gates/         vocabulary  every reserved name classified, checked against corpora that ship
  probes/        5 modules   worked examples and measured comparisons -- dungeon fights, the
                              approval pattern, REPL autocorrect
  rules/                     shipped corpora (`worked.ugm`, `delay.ugm`, the dungeon fixtures,
                              `tools_approval.ugm`, `circuit_breaker.ugm` -- a generic, temporary
                              rule-suspension pattern any corpus can watch a rule with -- and
                              `todo.ugm`, a standing task stack any corpus can load alongside its
                              own)
  corpora.py                 one accessor for a shipped corpus's path, used throughout
  repl.py, repl_fs.py, fs_repl.py    superseded by HarneSkills (still here, still tested; not
                              the door a new user should walk through -- see Try It, above)
  selftest.py                the one test runner
```

## Verification

Not pytest. One runner that prints every check's named observations and counts any `False` as a
failure:

```bash
python -m ugm.selftest              # 179 checks, 0 failing
./tools_sweep.sh                    # every module with a main(), found on disk (not a fixed list)
python -m ugm.gates.vocabulary      # every reserved name classified exactly once
python -m ugm.probes.tools          # the approval pattern, run both approved and denied
```

## Documentation

- **[The book](https://ercasta.github.io/Universal-Graph-Machine/)** — the tutorial, from scratch.
- **[`docs/guide.md`](docs/guide.md)** — the surface syntax, the loop, lanes and triggers, in one page.
- **[`docs/authoring.md`](docs/authoring.md)** — what actually bites when you sit down and write a
  corpus.
- **[`docs/tools-approval.md`](docs/tools-approval.md)** — the approval-as-a-corpus pattern the REPL
  demo is built on.
- **[`docs/feature-requests.md`](docs/feature-requests.md)** — ideas raised along the way that never
  got built; not a roadmap.

## House rules

> **A claim with no measurement behind it is an opinion, and it is marked as one.**

> **No feature is novel until something falsifies the claim.**

## Licence

MIT. See [`LICENSE`](LICENSE).
