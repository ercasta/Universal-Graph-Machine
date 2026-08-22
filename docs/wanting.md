# Wanting — the design conversation, 2026-08-22

No engine changes. Everything recorded as *measured* below was run in scratch probes
against the tree at `ca792e1`; everything else is a position taken in conversation and is
marked as such.

The subject is one finding from the previous session, kept in `selftest.py` §18:

> A spent want cannot be noticed as unmet — nothing deposits `open`, so the retry rule is
> never applied and the alternative is not handed back.

That check ends by naming its own repair: *the argument for computing wanting from the
state instead of asserting it.* This document is what happened when that argument was
followed, and it does not end where it expected to.

---

## 1. What a want was, at the start

Three different things carry the name.

    goal(w)     the apparatus's own relation, and the only one the engine reads. Drives
                backward reading, `achieved`, `_outstanding`, `_notice_open`. In
                `_bookkeeping`, so it is excluded from state spans.

    want(...)   an ordinary corpus relation with no engine support. The dungeon and
                `probes/attention` use it precisely BECAUSE `goal` is reserved: a
                completion rule written over `goal(?w)` is applied to the backward
                reader's own subgoals and reports the thing finished before it is built.

    the gap     `delta(<have>, <want>, <gap>)`, a tool, answering `missing(<gap>, p)` and
                `extra(<gap>, p)`, with `matched(<gap>)` for the empty gap.

Spending is a corpus law, not a mechanism. `_forgo`, `_passed_up` and `forgone(...)` were
deleted; a rule that serves a want denies it in its own consequent, so the rival route has
nothing left to match.

`open(w)` has exactly one writer, `_notice_open`, which iterates `instances_of(GOAL)`
resolving `+`. A spent goal resolves `-` and is skipped. Two things sharpen the finding
beyond what the check says:

- `_notice_open` is called only from `_enough`, the satisfied stop. `_wake` — quiescence —
  calls only `_notice_attempts`. So `open` is a stop-time notice on one of the two endings,
  and even an unspent want is invisible until something claims `enough`.
- The veto is per-seat and once, so it is an interrupt rather than a standing condition.

---

## 2. Four representations, tried and dropped

The first proposal was to make the delta the only goal machinery. That question — *what is
the bootstrap want when something arrives from a channel?* — produced four answers in
sequence, each failing for the same underlying reason.

### 2.1 A standard containing a description. Measured: it does not work

The idea was a standing want-span compared against the world at each settling. The span
must be a description, because you do not know in advance what will arrive.

    standard              held                     result
    want(served(?r))      request(r7)              extra(gap, request(r7))
    want(served(?r))      nothing                  matched(gap)
    want(served(?r))      request(r7), served(r7)  extra x2
    want(served(r7))      request(r7)              missing(gap, served(r7))   [control]
    want(served(r7))      request(r7), served(r7)  no missing                 [control]

Three silent failures, and the middle one is the dangerous one: **a standard containing a
demand that nothing satisfies reports itself met**, because `_delta` skips members with
variables and then finds no difference. The third row is the same blindness inverted — the
proposition that satisfies the standard is reported as junk to get rid of. Set subtraction
cannot see instantiation in either direction.

### 2.2 A span that grows. Measured: it works, and it is the wrong shape

A rule can conclude a ground demand — `implies({ +request(?r) }, { +wants(served(?r)) })`
binds `?r` from the world — but the conclusion lands in the state, not in a compound whose
members are fixed at construction. Extending `_contents` with a third kind of span, the
extension of a relation, makes it work:

    one request outstanding      missing(gap, served(r7))
    ...served                    matched(gap)
    ...a second request ARRIVES  missing(gap, served(r9))
    ...and is served             matched(gap)

Four cycles, no goal asserted anywhere, and an arrival re-opens the gap by itself. Two
things had to be got right. The have-span must exclude the wanting vocabulary, or
`extra(gap, wants(served(r7)))` appears — the standard's own deposits compared against the
world as though they were part of it. And `extra` must be scoped, or `differed` is
permanently true and `matched` is never deposited at all.

### 2.3 The measurement that killed it

    derived:                 +
    after a rule denies it:  -
    after running again:     -     refraction; the ground does not restore it
    ground denied instead:   +     the demand outlives its support

**A derived demand is spendable.** Refraction stops the rule being applied again on the
same bindings, so denying it is final — being derived rather than asserted buys nothing.
And denying its ground leaves it standing, because conclusions are not retracted when their
support goes.

So the demand set is not a function of the world in either direction. It accumulates. The
four clean cycles above were carried entirely by `_delta`'s own stale-denial of `missing`,
not by anything live above it.

### 2.4 Standards as rules consulted. Withdrawn

If demands must be a function of the world at comparison time, and deposits are not, then
demands must not be deposited: the standard becomes rules run against the have-span when
the gap is computed, with signed conclusions giving demand, prohibition and silence.

Withdrawn on the author's argument in §3.

---

## 3. The reframing: wanting is the moving force

The author's position, and the turn this document exists for:

> The agent acts because it wants something. Via competence — a mix of style, instinct and
> education — it acts depending on the want and on its internal state. Under this view the
> delta is, correctly, just a tool: the agent uses it because at a given moment it WANTS to
> know what is missing. The goal is external. What moves the agent is wanting to satisfy
> the request.

This kills 2.1 through 2.4 at the root, and it agrees with a line the engine already holds:
a tool proposes, never concludes, and `delta` is registered NOT standing on the argument
that a corpus retiring it should lose only what it chose to ask. Making it the sole goal
machinery contradicted both.

What it corrects is deeper than the delta. Four representations had been tried when the
question was never representation: it is what gives a want its **force** and what ends it.

**A want has two parts, and `goal(w)` fused them.**

    the force   why the agent would move at all
    the test    what would count as done

Every failure above is the test standing in for the force. A goal spent is a want that lost
its force and kept nothing. A demand deposited is a test that outlives its force. A gap
recomputed is a test with no force at all, which is why the gap-keyed corpus in
`probes/alternation` works only for as long as the harness keeps asking.

### Three tiers, which are read rather than declared

They are a way of talking about wants, not a classification in the graph. Nothing is
tagged: a want with no parent is a root, one with a parent is a sub-want, and whether a
root is constitutive is just whether its condition is something the agent always has. All
three are what the `because` query returns, and everything below is a consequence of that
reading rather than a property anything asserts.

    constitutive  *serve what is asked*. A disposition, not a state, so it is never
                  satisfied and never spent, and not derived from anything. This is the
                  bootstrap the delta was being asked to supply, and it is not a goal.

    occasioned    *serve r7*. Created by an arrival, and its terminus is the answer going
                  OUT, not the world reaching a configuration. The blocks being stacked
                  does not discharge it; `emitted` does.

    sub-want      a reduction. Freely spendable, and it should be: it is how a want cashes
                  out given this world and this competence, not a want in the moving sense.

This is also why `want` and `goal` kept colliding in the fixtures. They are not two names
for one thing — one tier is the agent's, the other is the machinery's reduction of it.

### The carrot, and where it bottoms out

The author's formulation: competence always puts the next carrot in front of the agent, and
the bottoming out is when it does not put another one but eats it. That settles termination
without a marker — competence given a live want yields either another want or `doing(...)`,
and the outbound boundary already distinguishes them.

It also means the chain is left behind rather than built ahead. Nothing plans the sequence;
each cycle puts down one link. That is the shape `probes/alternation` already measures —
one move, the world settles, ask again — which is why laziness costs nothing.

---

## 4. Force is inherited, so wants form a chain

If a want moves the agent and an action spawns a sub-want, the sub-want must inherit its
force, or it floats free and outlives its reason — which is what 2.3 measured.

The author's proposal: materialise the chain. *I want to go to the restaurant because I want
to eat because I am hungry.* Then inheritance is a query rather than a mechanism.

**It bottoms out in something that is not a want.** *Hungry* is a state; *want to eat* is
that state read through a constitutive disposition. So the root of every chain is a
constitutive want plus a condition, and the condition lapsing kills the chain in one walk
with nothing retracted anywhere. That is the death of a want, finally expressible.

**The links may not need asserting.** `_rivals` already reads which want an application
served off `app.consumed`, so the trail records one step of it. What materialising buys is
depth, and §5 says why that costs no machinery.

**A want has several parents.** The restaurant because I am hungry and because I want to
meet Anna. Cutting one link must not kill it, so the chain is a DAG. A parent-pointer
version looks correct on every single-parent fixture and is wrong the first time two
reasons coincide.

### Push life down, do not pull liveness up

The obvious reading of inheritance is a question asked upward — *is there a live root above
me* — and it is the wrong direction. Propagating life **down** from the roots is one rule:

    implies( { +because(?c, ?p), +live(?p) }, { +live(?c) } )

Three things fall out that the upward reading had to be given:

- **the DAG needs no special handling.** Any live parent gives life, so *does any uncut path
  reach a live root* stops being a question anything has to ask.
- **`dead` is `no live(?w)`**, one step, answered by the machinery §5 is about. There is no
  negative existential over paths anywhere.
- **the cut is one member on the propagation rule** — `no no_more(because(?c, ?p))` — so it
  bites per link, which is where a cut means anything.

The root case is the same rule with nothing above it: `live(<root>)` while its condition
holds. So *the condition lapsing kills the chain* is not a walk at all; it is the same rule
failing to be applied, and §5 says what removes what is already there.

### What is not a want

An agent with no live want must still perceive, still take arrivals, still notice staleness,
or rest is indistinguishable from being switched off. The constitutive tier covers it, and
it puts staleness in the right place: the agent refreshes its view because it WANTS to,
which dissolves the register-owned "occasion" proposed two turns earlier. `quiet(<moment>)`
and `arrived(...)` stop being triggers the register pulls and become ordinary facts
competence reads.

Three consequences, and the third is the argument for the whole shape:

- the refresh is scoped by what a live want rests on, rather than by a global cache rule;
- rest becomes a fixed point rather than the loop running out;
- the liveness answer is itself subject to staleness and needs no special case, because it
  is the same want doing the same thing one level down.

---

## 5. `no` dissolves the maintenance problem

Four sections had been spent on how to keep a satisfaction mark fresh. The author's
correction: rules can ask for absence. `ABSENT = "no"`, and the note above it in `rules.py`
says an absence is asked, never deposited — the gate has no entry sign for it, deliberately.

So satisfaction is a **match condition**:

    alias active_want(?p) = { +want(?p), no ?p }

Measured:

    want unsatisfied            emitted ['fill(kettle)']   want still + : True
      <chase> expanded to       ['+want(?p)', 'no?p', '+route(?p, ?a)']
    want already satisfied      emitted []                 want still + : True
    control -- guard removed    emitted ['fill(kettle)']   want still + : True

Aliases expand at load and in place, so `?p` is bound by `+want(?p)` before `no ?p` is asked
— binding order is safe by construction rather than by care. The want stays `+` in every
row, nothing is denied anywhere, and the control fails correctly.

Nothing needs maintaining, because nothing is materialised.

### What this deletes

`_root` gives its own reason for being Python: *a root goal is a `goal(?w)` with no
`subgoal(?p, ?w)`, and a `-` member says an entry denies this, never for no ?p.* That is
exactly the limitation `no` removes. `implies({ +want(?w), no because(?w, ?p) },
{ +root(?w) })` looks like the whole of it — worth checking rather than assuming.

### Depth costs nothing, because the loop is the closure

This section originally asked how a rule could express reachability, weighed two homes for
the walk, and reached for walkers. All of it was a mistake of the same kind as reaching for
a Python walker: machinery for something the substrate already does.

**A one-step rule applied to quiescence is the transitive closure.** The `live` rule in §4
is not recursive in any special sense — its conclusion happens to feed its own antecedent,
and forward chaining supplies the depth. Nothing has to say *transitively*.

Two consequences for the two things that looked like requirements:

- **Arbitrary depth in one query is not available and is not needed.** A rule's antecedent
  is a fixed set of members, so `because(?a,?b), because(?b,?c)` reaches depth two and depth
  *n* needs *n* members. A bounded query is a fallback for when a bounded answer is what you
  want, never the mechanism.
- **A walk that has to find something out is split over the agent's own cycles**, which is
  the carrot model doing what it already does: advance one link, let the world settle, ask
  again. Liveness happens not to need it, because the chain is already held and the loop
  closes it without acting. So the loop answers walks that do not touch the world, the
  carrot answers walks that do, and neither is a walker.

Two things from the discarded version are worth keeping.

**The structure trap is real.** Minting a closure relation as structure while the matcher
still resolves it through the chain would make `no reaches(...)` silently true for
everything — a wrong answer rather than a crash.

    if want.sign in (MINUS, ABSENT):
        # `no` over the skeleton IS this negation: structure has no
        # denying entry, so absent and denied collapse into one
        # question the walker already answers.

**Node-keyed, not path-keyed.** `3n + 1` against `2^(n+2) − 3`. That measurement was taken
of walkers but it is about the closure, so it survives whatever computes it: conclude about
the node, never materialise the paths.

### And no walkers either

The walker apparatus — `at(<w>, <node>)`, a fresh identity term per walk, spawn rather than
move, termination by denial — exists to give a traversal an answer that cannot be confused
with the last traversal's answer. Every part of it is a workaround for a chain that can only
be added to. Under the scratchpad there is nothing to work around: one graph, one current
answer, and a stale mark deleted rather than superseded.

Two things do not go away with the walkers.

**Erase-then-create is the same hazard that made a walker spawn rather than move.** That was
measured: moving denies the position both rules needed, and the branch is lost *silently*,
in fewer ticks and less work than the run that succeeds. Erasure has exactly that shape and
generalises the finding — an erasure is not local, anything that still needed the erased
node is affected, and it fails quietly. It wants a probe of its own under anchors.

**Absence of a witness is still not a finished search** — §9's own line. One asymmetry
rescues it: **chasing needs only a positive witness**, so a closure still being computed
means the agent does not act yet, which is correct. Only **abandoning** needs the search
known finished, and that is the cell that spawns cleanup rather than the common path.

### The residue: who removes a mark the world has invalidated

The loop supplies the depth, but it does not un-supply it. `live` marks derived from a world
that then changes are wrong marks, and something has to remove them. Two ways, and the
second is the one this engine has reached for every other time:

- **clear the relation's whole extension before each deliberation.** Not rule-shaped — a
  rule cannot speak about the set of its matches — so it would be a tool, and a scan.
- **license each erasure by whatever invalidated it.** The root condition lapsing erases
  `live(<root>)`, which erases `live` on its children, one link per application: the same
  one-step rule running in the other direction. It stays rule-shaped, and it costs only what
  changed rather than the whole extension.

The second is delta-shaped, which is how every other version of this problem has been fixed
here. It needs erasure to be licensed and recorded first, so it waits on §9 item 2.

---

## 6. Endings, and why denial loses them

A want denied is four fates under one sign: satisfied, abandoned, overtaken, never mind. And
refraction means it does not come back. That is the original finding in its general form,
and it is what rewriting `want` to `wanted` was proposed to fix.

Rewriting is not needed and not available. The graph is monotone in nodes — a sign is an
entry in the chain, not a property of the node — so after `-want(p)` the node still exists
and every link pointing at it is intact. Nothing was lost. There is no node rewriting in the
engine either: `rewrote(<trigger>, old, new)` records a norm intercepting a conclusion
before it is written, and the identity layer merges nodes that denote the same thing, which
is coreference rather than a state change.

What denial actually loses is the ending. The author's alternative — keep the want and put
the status on a separate proposition — names the ending instead of erasing it.

### The 2x2

                    live                                  dead
    unsatisfied     chase: a sub-want or an act           abandon
    satisfied       done; for a maintenance want, watch   nothing; the record stands

The bottom-left is the cell worth designing for. Abandoning is not a silent drop: you went
to the restaurant and stopped being hungry, and you are now at the restaurant. So the death
of a want is an occasion for competence and can spawn a fresh want — get home, retract the
request, tell whoever asked.

### Denying a link

A `-because(...)` entry would be invisible if `because` is structural, for the mechanical
reason quoted in §5: for a skeleton relation the walker is asked *does anything satisfy
this*, never *is there a denying entry*. The entry would sit in the chain looking meaningful
and change nothing.

`no_more(because(hungry, eat))` is the correct form and is better than sign-denial would
have been, because it is an ordinary claim — dated, attributable, deniable in turn,
defeasible, learnable. Everything structure deliberately is not. Whether it survives at all
is settled in §7.

---

## 7. The scratchpad, which makes most of the above moot

Belief becomes presence of an anchor; retraction becomes deletion; the chain becomes a log
of what changed that the agent reads.

Every problem in §2 through §5 is one symptom: **a deposit that cannot be taken back.** That
is an artefact of an append-only chain, not of wanting. Under anchors the demand whose
ground went away is erased, there is nothing to maintain and nothing to deny, and the split
this document was groping toward falls out:

    current status   in the graph — the anchor is present or it is not
    which ending     in the log — the erasure is recorded

Which is exactly what the original finding needed. A spent want could not be noticed because
append-only had nowhere to put the difference between *never wanted* and *wanted and done*.

### What survives, measured

    before               p = 3  want(restaurant)  | anchor = 4  believed(want(restaurant))
    anchor erased
      show(anchor)       #4(erased)
      relation_of        None
      members            ()
      show(p) still      want(restaurant)      intact
      p findable         True

A NodeId is a plain int, so anything holding one — a chain entry, an index — still holds a
valid reference. The node's content does not survive: reads answer rather than raise, but
they answer with nothing. It does not matter, because the proposition is never deleted.
`delete`'s own docstring: *structure only — what makes a proposition believed is an anchor
node, so retracting a belief is deleting the anchor and never the proposition, which rules
mention and must keep.*

### Two gaps in the erase substrate

**Deleting an ENTITY hides nothing.** Measured:

    before delete    chasing(restaurant)     the rule was applied
    entity deleted   chasing(restaurant)     applied anyway
    is(...) indexed  ['is(?d, want)', 'is(x, want)', 'is(#1292(erased), want)']

`delete` only touches indexes inside `if rel is not None`, and an entity has no relation, so
for an entity it pops six dicts and de-indexes nothing. Nothing anywhere removes a node from
the buckets of other nodes that mention it.

So `probes/erase.py` verified *no rule matches an incomplete subgraph* for one shape — the
matched proposition is gone, so the premise fails to bind — and not for the shape the anchor
design needs, where a surviving proposition mentions a gone thing. **The only safe deletion
target is the anchor.** Delete anchors; never propositions, never entities.

That gap is now closed as a measurement: check 4 runs the two erasures side by side, the
probe is 6/0, and the consequence is stated in the module's own docstring. The behaviour is
unchanged — what changed is that it is no longer unmeasured.

**Erasure records nothing and bypasses the gate.** `Graph.delete` writes no chain entry, no
licence, no trail, and its only callers are inside the probe. Writes go through `gate.write`
with licence, consumed and source, and run the `on_write` hooks; erasure sits below all of
it. An erasure has no entry by construction, so recording it needs its own deposit on the
log, made through a gate-level erase. Until that exists, `no_more(...)` is not redundant —
the licence on the erasure is what would name the ending.

### The desire is an entity

The author's position: the want in `want(restaurant)` is a desire, and it has its own id.
Two wantings of the same content are two entities, exactly as two mentions are never one
mention. That turns erase-and-recreate from a hazard into the design — the old wanting keeps
its id and its history in the log, and the new one is a new thing that happens to be about
the same restaurant.

It also decides what the log should name: the **entity**, because a term is a rigid
designator and a premise is a description. The description of the want may be revised; the
wanting itself cannot be.

### `context: believed`

If belief is presence of an anchor, a rule matching a bare proposition reads structure as
though it were belief — and the entity measurement above is what that failure looks like: a
rule applied to a want nobody holds, with nothing anywhere to say so.

A per-member wrapper can be forgotten on one member out of five. A document-level context
applied to every component cannot, which is why it is preferred over `B(?p) = believed(?p)`
and why it makes the load-time gate unnecessary rather than merely cheap.

Because the wrapping happens at load, exactly as aliases do, what is stored in a rule is
already `believed(want(?p))` and the matcher never learns what an anchor is. That may take
**matching** off the todo's list of what `believed(p)` touches, leaving the loader and
`Graph`.

Four constraints, three of them already precedented:

- **Skip what is never believed.** Skeleton relations and computators. Wrapping a structural
  member is a category error and would break the stratum-0 test, since a wholly structural
  rule wrapped in `believed` stops classifying as structural and starts depositing entries.
  Both are determinable at load.
- **Do not descend into mentions.** Aliases already refuse this — expanding inside a mention
  puts words in the mention's mouth.
- **The reflective case needs an explicit escape.** A rule about belief would be
  double-wrapped, and `believed(believed(p))` is meaningful. "Do not wrap what is already an
  anchor" is the tempting rule, and it is wrong for the case this engine cares most about.
- **The consequent is where the sign disappears.** `+p` creates the anchor, `-p` deletes it.
  That is the migration path for every existing corpus — a header line rather than a rewrite
  — but it collides with a question the todo already has open: `-` and `?` collapse into *no
  anchor matches*, with `bundle.ugm`'s three deviation rules named as the fixture for
  whether that collapse is lossy.

---

## 8. What is settled

- A want is force plus test. `goal(w)` fused them, which is why every failure looked like a
  representation problem.
- The three tiers are a way of READING the chain, not a classification in it. There is no
  tier vocabulary, no marker and no field: a want with no parent is a root, one with a parent
  is a sub-want, and whether a root is constitutive is just whether its condition is
  something the agent always has. All three are what the queries return, and the terminus of
  an occasioned want — the answer going out rather than a world configuration — is a
  consequence of that reading, not a property declared anywhere.
- Competence puts the next carrot in front until it eats one. `doing(...)` is the bottoming
  out, so termination needs no marker.
- The want chain is materialised and is a DAG. Life is **pushed down** from the roots by one
  one-step rule, and the loop supplies the depth — so nothing expresses transitivity, the DAG
  needs no special handling, and `dead` is `no live(?w)`. No walkers, no `at`, no walk
  identity: all of that was a workaround for an append-only chain.
- Node-keyed, never path-keyed. That measurement is about the closure, not about walkers, so
  it survives them.
- Removing a mark the world invalidated is licensed per link, not swept. It waits on the
  gate-level erase.
- Satisfaction is `no ?p`, asked at match time. Nothing is maintained.
- Only the anchor is ever deleted. The log names the entity.
- Belief-wrapping is `context: believed`, applied to every component at load.

## 9. What is open

1. ~~`probes/erase.py` checks one shape of two.~~ **Done.** Check 4 added, and the probe is
   6/0: the two erasures are run side by side, and only the erased premise hides anything.
   The behaviour is unchanged — what changed is that the tree now measures it, and says in
   its own docstring that the only safe deletion target is the anchor.
2. A licensed erase through the gate, depositing `erased(<entity>, <licence>)` on the log. A
   precondition for deciding whether `no_more` survives.
3. `_root` looks deletable now that `no` exists.
3b. **Erasure is not local, and nothing measures that yet.** The walkers finding — moving
   denies the position both rules needed, and the branch is lost silently in fewer ticks
   than the run that succeeds — is the same shape as erase-then-create. Under anchors it
   stops being a walker's problem and becomes everyone's.
4. The `-` / `?` collapse under anchors, with the three deviation rules as the fixture.
5. Per-term weights on competence rules, scoring the application rather than the rule and
   combined with the attention multiplier. Parked deliberately. `_attended_first` already
   sums weights over the nodes an application binds; what is added is position, so the same
   node can weigh differently depending on which member it satisfied — which is the
   limitation node-keyed advice was recorded as having. It must stay ordering rather than
   confidence, and whatever lands must be read by the chooser with a check that can fail
   without it: `weaker` was carried, composed, printed and never obeyed.
6. Belief over a stretch. The todo flags it as decide-it-before-a-corpus-needs-it, and
   wanting is that corpus: *I wanted this until I got it* is a claim about a stretch, and a
   stretch has no presence. §12.5 narrows it usefully — an observation record can say *I
   looked at these times and it held then*, which is honest and is not a stretch claim.
7. The observation record of §12 costs log weight and saves interrogation cost. Interning
   collapses repeated instantiations, so growth is probably far below worst case — and
   *probably* is what this repo has been wrong about before. One measurement of both, with
   and without, before it is believed.
8. §12.7's failed-member record is only unambiguous after `believed(p)` lands. Today a
   required-present member fails both when the proposition is absent and when it is denied,
   so the finding would blur two cases that anchors collapse into one.

## 10. Instrument traps met on the way

- **`g.atom("x")` does not intern.** Each call mints a new node; the loader's name table
  decides identity when a name is read. A probe that builds terms in Python compares
  disconnected nodes and reports a plausible wrong answer. Build through `load` and
  `kb.term`.
- **`asked` is a structural relation.** A fixture rule using it was classified stratum 0,
  applied, and wrote nothing. The only symptom was `wrote=()` on an applied step.
- **A borrowed word collides.** `answered` is the apparatus's own relation for tool answers
  and is filtered out of a state span as a mention record, so a fixture using it as a corpus
  word measured the wrong thing.

## 11. Where to pick up

The substrate items — 1, 2 and 3 — are small, verifiable against the existing suite, and
commit nothing about the want design. They also unblock item 2's question about `no_more`.

The want chain itself can be probed today, but it would be written in signs, which is the
notation anchors replace. It is better treated as the thing that motivates the anchor work
than as a probe run twice.

§12 is the memory design, worked out after the sections above and depending on §7.

---

## 12. Memory: what a scratchpad has to keep

If the graph is the current state, the question is where the past lives. Nothing below is
built; `holds_at(<proposition>, <moment>, <sign>)` is proposed in the handoff and does not
exist, and the observation record described here does not exist either. What does exist is
the structural vocabulary the log is made of: `in_delta`, `delta_next`, `pred`, `anc`,
`rests_on`, `licensed_by`, `entry_of`, `time`.

### 12.1 Three records, three questions

    the graph      what do I believe now              anchors, present or absent
    the log        what did I believe then            deltas, reconstructed
    the memory     what did I look at, and find       observations, dated

They are not redundant storage; they hold different content, and each is cheap only at the
thing it is for. Two snapshots cannot say which rule changed something — *which ending a
want had* lives in the transition, which is §6's whole subject. A log cannot cheaply say
what held — reconstruction means replay. And neither says what the agent examined and
found, which is what justification and learning read.

### 12.2 The log, and the measured warning about it

Reconstructing the past by delta is the undo half of undo/redo, and it is the chain's
natural role once it stops being what the view is computed from.

**Reading the past is not returning to it.** Undo-as-memory is this; undo-as-restore is
hypothesis, and the engine has already moved away from that shape once — `suppose` and
`discharge` were replaced entirely by three bridge rules, with containment becoming an
ordinary premise. The read should be built and the restore should not, or the old semantics
return under a new name.

**Replay must be bounded by a snapshot, never by the beginning.** This is the same finding
arriving a third time: the state stopped being rebuilt (1,600 facts, 4.79s to 0.48s, the
loop made linear), and `resolve` was 86% of a run before it was cut 67×. *Reconstruct by
delta* is right as a model and dangerous as an implementation.

### 12.3 Snapshots, which are spans

`_contents` already reads two kinds of span — a moment, and a compound's members — and
`delta(<have>, <want>, <gap>)` already compares two of them. **Comparing now against a
remembered span is the same operation as comparing now against a wanted one**, in the other
direction, so a snapshot needs no new comparison machinery.

What it needs is a way to mint one, and that is an aggregate: only something that has seen
the whole believed set can name it. So it is a tool, for exactly the reason `matched(<gap>)`
is a tool.

**A snapshot must not live under `believed`, and the reason is mechanical: membership in a
span is not an anchor.** Propositions inside a snapshot are members of a node; nothing
anchors them, so no rule can mistake a remembered belief for a current one — with no filter,
no reserved vocabulary and no special case. It also states the semantics correctly: the
agent does not believe what it believed then, it believes that it believed it.

**And snapshots are what make the log prunable.** An append-only log with no horizon is
unbounded. With checkpoints, deltas older than one can be dropped. That is the third reason
for having both, and the one that makes both necessary rather than convenient.

### 12.4 Retention is keyed on occasions, not on content

A rule cannot speak about the set of its matches, so no rule can say *remember all this*.
It does not have to. It has to recognise an **occasion** worth remembering, which is a much
easier judgement and one the corpus already makes with vocabulary that exists — `deviates`,
`arrived`, `quiet`, `declined`, `unsupported`:

    implies( { +deviates(?p, ?r) }, { +snapshot(<here>) } )

The rule names *when*. It never names the set.

### 12.5 Record at evaluation, not at match and not at the door

An earlier draft of this section asked whether to record an application's premises at match
time or at the door, since an absence re-asked at the door may have closed since the match.
Recording **what was re-evaluated at that moment** dissolves the question: each observation
is stamped when it was actually made, and a member carried over from an earlier match is not
re-recorded now because it was already recorded then, correctly.

The hook is where it should be. Delta matching walks pivot-first against the delta, which is
*a Situation like any other, so this adds no representation*, and `match` already records
what it matched with the argument attached: *that is not overhead — it is what makes a
misbehaving rule distinguishable from a misresolving chain.* This extends the same argument
one step, to what was evaluated and not matched.

**A consequence worth stating: an application's premises were never simultaneous.** Member
one observed forty ticks before member three is the normal case, and assembling them into
one dated set would manufacture an instant that never existed. It also lands on the open
stretch question: the agent can honestly say *I looked at these times and it held then*, and
cannot say *throughout* — which is correct, because it does not know.

### 12.6 Record the finding, not the LHS

The obvious proposal is to record the instantiated antecedent, on the argument that it is
the truth at that moment including its absences, where `consumed` cannot report an absence
at all. The argument is right and the object is wrong.

**A sign in an antecedent is a requirement, not a finding.** For a satisfied member the two
coincide, which is why recording the LHS looks correct. For a **failed** member they are
opposite — and failed members are exactly where the new information is. Recording
`+locked(door)` off a failed match writes down *locked was required* when the finding is
*locked was absent*.

So the unit is, per member evaluated:

    the term, ground          what was looked at
    found present / absent    what was seen

independent of what the rule required. And under anchors the antecedent carries no signs to
confuse this with: bare means *require the anchor present*, `no` means *require it absent*,
and `?` goes with the rest, since absence is unknown once the log distinguishes never-said
from said-and-erased. The three deviation rules in `bundle.ugm` are the named fixture for
whether that collapse is lossy.

The polarity that survives is in the consequent, and it is a different kind of thing:
**an antecedent's polarity is a question, a consequent's is an action** — present-or-absent
against create-or-delete. They shared notation because a chain wrote both as entries.

### 12.7 Partial matches, and why memory is three-valued in itself

Record the evaluated members of candidates that did not complete, filtered by a compound
salience score. Then:

- a member that was **required present and found** records a truth;
- a member that was **required present and missing** records an absence — the agent looked
  for it and it was not there;
- everything else is **not remembered**.

Absence in the record never means falsity, because falsity has its own representation. So no
threshold has to be written down, no partiality marker is needed, and — the property that
makes the whole scheme work — **soundness is independent of the filter.** Raise the
threshold and the memory gets sparser; it never gets wrong.

One thing not to record: **computators**. `minus(?x, ?c) as ?new` is a condition on the
binding that claims nothing, so writing it into a record of what was true is a category
error. That is the same skip list `context: believed` needs, which is an argument for
building the list once.

And one thing the shape gives away free: a member required **absent** and found so is a
universal negative about that moment — *nothing satisfied this pattern at t*. A rule cannot
otherwise make a claim about a whole set. Here the matcher has already evaluated it, and
recording it costs nothing.

### 12.8 What this memory does not answer

A fact that never changes is never re-evaluated, so it is recorded once and never again.
Memory then under-reports what the agent knew — correctly, because **this is a memory of
looking, not of knowing.** Knowing now is the graph; knowing then is the log. Keeping the
three apart is what lets each stay cheap.

### 12.9 Pruning

Retention as a function of salience and age: strong observations are kept longer. This makes
the score do a third job — it already orders what to do and filters what to record — so
there is one notion of mattering rather than three that can drift apart.

It is safe by construction. A curve that rises with age is still only a threshold at each
moment, and by 12.7 any threshold leaves the memory sound.

Four things to get right.

**It runs periodically or on a threshold, never per tick.** Pruning is a scan, and it is the
only part of this design that is one. Garbage-collection shaped: triggered by size, or on
the same occasion that mints a snapshot.

**Recency is moment distance, not a clock.** The ordinal is already in the chain, and there
is a measured warning about the alternative — a foreign corpus *spent 24% of itself
re-implementing a moment ordinal as a round counter*.

**This decay is not attention's decay.** Attention decays by **displacement, deliberately
not by a timer**: *ten quiet ticks should not forget what you were doing.* Memory decays by
age. Both will be called decay, and the difference is that attention is a working set —
where a quiet hour must not clear the desk — while memory is an archive, where time really
did pass. Written down here so the two are not unified later by name.

**Salience alone cannot keep what it failed to notice.** If score decides recording,
retention and ordering, and memory feeds learning, and learning tunes the score, the loop
tightens three times. The counterweight is already in the vocabulary: surprise is by
definition what salience did not predict, `deviates` is an occasion, and the trail carries it
with the `expects` licence. Two criteria — **salience keeps what mattered, surprise keeps
what you got wrong** — and the second is what stops the first becoming self-confirming.

The retention unit is the **observation**, not the application. An old justification thins
unevenly and degrades to partial, which keeps pruning a local decision and is what
remembering is actually like: you remember that you did it and one of the reasons, not all
five.

### 12.10 No forgetting marker

An earlier draft proposed that pruning leave a horizon marker, so *I did not look* stays
distinguishable from *I looked and forgot*. Dropped, and the reason generalises a principle
rather than making an exception to one.

The distinction changes nothing the agent does: both readings mean look now. A distinction
that alters no action should not be represented, which is the same standard as a check that
cannot fail and a mark the matcher cannot see. So the principle is not *anything that
forgets must record that it forgot* — it is:

> Record a forgetting when the distinction changes an action, not because it is tidy.

Which is why belief still records its erasure — *never said* and *said and erased* lead to
different conclusions — and observations do not.

One hazard survives and is independent of pruning: a learner treating absence-of-observation
as evidence. That is *a search that stopped is not a search that found nothing*, and it is a
property of how memory is read rather than of how it is trimmed.
