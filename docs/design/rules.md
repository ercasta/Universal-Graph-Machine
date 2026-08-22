# `core/rules.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.


## `_Stop`

The postcondition that ends the run, as a sentinel rather than a node.

    ⭐ `attend` deposits a claim, `unattend` denies one, and this stops. All
    three are what an applied rule SPENDS, so all three are rows in one
    vocabulary rather than branches -- which is the test this design applies to
    connectives and applies here for the same reason.

     There were three more -- `boost`, `damp` and `reset` -- and they moved a
    SCORE. They named a rule, so they are retired with `prefer`. The vocabulary
    got shorter and no branch appeared, which is the property that mattered.

     Deliberately not `g.atom("stop")`. A corpus may name a rule `<stop>`, and
    a reserved atom would make the verb and the rule one node with two meanings
    -- the twin trap, which this repository has now recorded seven times. A
    sentinel cannot collide with anything a corpus can write.

     And it is not a *score*. The design's line about norms applies exactly:
    a thing that must not be outweighed is a premise, never a number. Stopping
    is decided by the rule's own antecedent -- the query that had to hold for
    the postcondition to run at all -- and never by outranking anybody.

## `Attend`

The postcondition that deposits attention on what the move just bound.

    ⭐⭐⭐ **A different KIND of row from the ones it outlived.** `boost`,
    `damp` and `reset` moved a score and `stop` ends the run -- all of them the
    loop's own bookkeeping. This one deposits an ordinary CLAIM, which nothing
    else a postcondition could spend has ever done, and it is why it is the one
    that survived the retirement.

     That is the point rather than a wrinkle. Attention is a fact about a node
    -- readable by rules, deniable, attributable, dated -- and a postcondition is
    the only place a lesson about it can live. `docs/HANDOFF.md` 2026-08-15
    measured why: a learned recogniser written as a RULE has to win a move to be
    heard and fired twice out of sixteen, because *in a one-move-per-tick loop,
    spending a move on recognition competes with doing the work*. A
    postcondition is evaluated for free after whatever applied.

     So the deposit is NOT the table's business, and this file's sentinel is
    where it stops: `Table.spend` stays a pure account of scores and the loop
    hands attends to the machine. A table that could write claims would be an
    interpreter with a memory, which is the thing the four primitives exist
    instead of.

     A class rather than a sentinel because it carries the term to attend to,
    which `stop` and `reset` do not. `term` is a node once the loader has built
    it, and the parser's own term before that.
    
    ⭐⭐⭐ **And it carries a WEIGHT, which is what a learned buff used to be.**
    `attend($x, 3)` says *of the things this move touched, THAT one matters* --
    a multiplier on a node's place in the attention queue rather than a number
    added to some other rule's score.

    That is the whole of the retirement, now complete: a
    calibration that names a NODE goes stale for nothing, where one naming
    `<R>` goes stale the moment a rule is adopted, composed or renamed. And it
    is the differentiation the queue's position alone cannot supply, because
    everything one move wrote arrives at the same instant.

## WHERE the entry must sit, as a pattern to bind

⭐ WHERE the entry must sit, as a pattern to bind (§8, §12). Defaulted, so
every construction site that does not care is untouched -- which is the
whole reason a NamedTuple was the right shape for a member.

§12 says a member IS an entry and the short form is an abbreviation whose
locus the frame supplies. That was true of the document and false of the
engine: there was nowhere to put a locus, so *the goblin acts after the
hero* was unwritable and a foreign corpus spent 24% of itself
re-implementing a moment ordinal as a round counter.

 The matcher had the locus all along -- every `Entry` carries one. What
was missing was a pattern for it, which is the third time this session a
wall turned out to be information nothing looked at.

## ...and a name for WHAT matched. at $m says w

⭐ ...and a name for WHAT matched. `at $m` says where the entry sits; `as
$t` says what its proposition is, so a rule can refer to the very thing it
matched rather than describing it again.

Without it a corpus reaches the same place by reconstruction -- match
`+$r($x, $y)` and rebuild `$r($x, $y)`, which interning makes the SAME
node, so it is genuine reference rather than a copy. That works and costs
§3's index, because a variable relation has no bucket. This keeps the
index and says the thing directly.

## STOP (below) may appear as a trigger's target.

`STOP` (below) may appear as a trigger's target. It is a sentinel and
not a node on purpose: a rule named `stop` must go on meaning that
rule, and encoding the verb as a reserved atom is the twin trap in its
cheapest form -- one name, two meanings.
Precedence is gone. It was two Python lists, then a graph read
(`precedence()`), and finally nothing: every corpus using it was saying
something it could say better as a premise about the state or as
`dormant(<R>)` -- a claim about one rule, read where the ordering is
built, revoked by `due`. What removes a rule from the running is that
claim, and nothing else does.

Measured on the way out: `overrides` cost 11 checks across six fixtures
and every one of them was rewritten smaller. The rules that read a
precedence relation -- `defeat`, `_defeated`, `_defeaters`,
`_superseded`, `precedence` -- are all deleted, and a RuleSet no longer
has a precedence node to be unset.

## ...and relations that are READ OFF THE CHAIN rat

...and relations that are READ OFF THE CHAIN rather than matched --
`pred`, `sanc`. §12 calls these the skeleton: *no sign, no locus, no
licence; nobody asserted them*. They are structure, so they are not
entries, so the state does not hold them -- which is why an ordinary
rule could never see one and stratum 0 needed a second matcher.

⭐ Given an ANCHORED moment they generate upward, and upward on a tree
is single-valued (§11), so a structural member cannot reach a sibling
branch. **Containment stays structural rather than becoming enforced**:
nothing is refused, a downward pattern simply finds nothing, exactly as
a rule matching an entry nobody wrote finds nothing.

## ...and defeat about a CASE, which was the last argument for precedence

`overrides` was per tick: a rule overridden by another that matched anywhere
this step did not apply at all, which is right when the two are rival answers to
one situation and wrong when they are rival answers to each of several. Pointing
it at a real pair showed it: making the outcome of an action replace the
assumption that the action happened also suppressed the assumption for every
OTHER action in the step. `supersedes` was added for exactly that case, and
compared consumed entries to find the applications about the same case.

Both are gone. *About the same case* belongs in the antecedent -- the bundle's
`<assert-act>` reads `no substituted($what)`, so the corpus qualifies it per ACT
-- and *this rule is out* belongs in `dormant`, which is per rule and says so.
Neither is precedence, and neither needs a second thing in the loop.

## Rules by the relation they CONCLUDE. §3 gives th

Rules by the relation they CONCLUDE. §3 gives the substrate one index,
over instances by relation, and argues for it in one line: *a rule
whose antecedent names a relation has to start somewhere, and scanning
every node is the alternative.* Read backwards the same argument holds
of the rule set -- a reader asking *what could produce this goal* has
to start somewhere, and asking every rule is the alternative.

It is an index over what was ASSERTED (the authored consequent), never
over what was derived, which is §12's condition on any index here.

A consequent that is a bare variable is deliberately absent: it claims
it can conclude anything, which §12 calls vacuous backwards, and `fit`
already declines it.

## A caller may supply the node, and adopt

 **A caller may supply the node, and `adopt` must.** A rule the
graph describes is already a node -- a corpus concluded `ant(<R>,
...)` about it, and `<R>` is what any `dormant`, any `exercised`
record and any later claim will name. Minting a fresh node here made
the live rule a TWIN of the described one: everything a corpus had
said about it went to a node that was not a rule, and everything the
machinery said about it named a node no corpus could reach. Found by
a standing policy that ordered a learned rule and quietly did
nothing. The twin trap, eighth time.

## `skeleton`

Every relation an ordinary rule reads as STRUCTURE rather than as a
        claim: the chain's own (`self.structural`) plus whatever a stratum-0
        rule concludes.

        ⭐⭐⭐ **The strata are derived, not assigned.** §6 defines stratum 0 as
        *a property of a rule* -- every antecedent member is structural --
        decided *by inspecting an antecedent rather than by a designer assigning
        layers*. That is computable, so it is computed: start from what the
        chain deposits, and add the conclusions of every rule that reads only
        those. Monotone, so it converges; and because it is a fixpoint from
        BELOW, a relation is structural only if something grounded in the chain
        makes it so. A cycle of rules concluding about each other adds nothing.

         Recomputed when a rule is added, because `adopt` means the rule set
        moves at run time and a stratum a rule was classified into before it
        existed is a stale answer. Cached because `match` asks per member.

## `strata`

The stratum-0 rules, grouped into layers that must run in order.

         **Negation makes the ORDER load-bearing, and structure cannot be
        taken back.** `best` is *a candidate nothing beats*. Applied before
        `beaten` has finished deriving, it mints a fact that is wrong and that
        nothing can deny -- a skeleton fact has no sign, which is the whole
        point of it. An entry would merely be superseded; this is permanent. So
        the layers are not a convenience, they are what makes the negation mean
        what it says.

        Standard stratification, and it is DERIVED like everything else here:
        a relation's layer is at least that of every relation a rule reads to
        conclude it, and strictly greater than that of any relation it reads
        NEGATED. Chain relations are layer 0. Iterated to a fixpoint, with a
        ceiling: if the layers keep rising, the rules negate each other in a
        cycle and there is no stratification to find.

         Refused loudly rather than run in some order that happens to work.
        An unstratifiable set gives a different answer depending on the order
        the rules are tried, and this is the one component whose whole purpose
        is to agree with the walk on every look.

## `compose`

Collapse `first` then `second` into one rule (§4).

        This is the design's largest available speedup, because it removes steps
        rather than making them cheaper, and the artifact is an ordinary node --
        askable, attributable, defeasible.

        Three things §21 requires, and each is a line here rather than a promise:

        **Standardise apart.** Both rules may say `$w` and mean different things.

        **Unify pattern against pattern.** Not match: `boiling($w)` against
        `boiling($x)` binds a variable to a variable, which matching never does.

        **Inherit the dormancy.** Anything that takes either constituent out must
        take the composition out too, or the shortcut fires where the reasoning
        it replaces would not have run -- §21's *a shortcut that has outlived
        its guards*, arriving immediately rather than after a context change.

        ⭐⭐⭐ **And guard inheritance is COMPLETE, which this docstring spent
        several commits apologising for.** It said `unless` is not implemented
        anywhere in this engine, so the half of guard inheritance §12 describes
        cannot be carried. That was false, and the mistake was a NAME: `unless`
        is *if not*, and *if not* is an ordinary negated antecedent member.
        Composition takes the **union of the antecedents**, so a guard is
        inherited by construction rather than by a mechanism -- verified from
        either constituent, and verified as behaviour and not only as structure,
        since a member carried and not obeyed is `adopt`'s own defect.

         What is genuinely absent is **amendment at a distance** -- adding a
        guard to a rule you did not write -- and calling that `unless` is what
        made a one-member rule look like a missing language feature. It is now
        refused by decision rather than open by omission: an ordinary rule may
        not reach into another rule's application (§5's wall), and amending a
        rule belongs to harmonization, where the agent authors a better rule
        through `adopt` and the amendment is itself an arguable claim.

        ⭐ **The grade used to block this.** §21 argued that composing one would
        be a minimum computed once from constituents that are themselves
        defeasible -- a cache of a derived value, §16's objection one level up --
        so composition refused anything but `certain`. With grades gone the
        objection goes with them: an uncertain conclusion is `+likely(p)`, an
        ordinary consequent pattern, and composing it is composing a pattern.
        The restriction was deleted rather than solved.

## Composing across a causes FLATTENS TWO M

 **Composing across a `causes` FLATTENS TWO MOMENTS INTO ONE
ANTECEDENT, and it loses conclusions.** §14: a `causes` consequent
lands in a SUCCESSOR, so the second rule's other premises are read
where the first rule's effect holds -- one moment later than the
first rule's own premises. The composite asks for all of them
together, which is a different and stricter question.

Measured, on `causes({+p}, {+q})` then `implies({+q, +r}, {+s})`:

  | r holds from the start        | derivation `s` | composite `s` |
  | r appears only AFTER p        | **True**       | **False**     |

The composite under-derives -- the safer direction, and still a
violation of §4's claim that *n* steps become one **with the same
conclusion**. An over-derivation was looked for and not found, which
is not the same as it being impossible.

⭐ This is why the mixed-connective question was the wrong one. What
looked like *which connective should a mixed composition get* is
really *some compositions must not happen at all*; and once the
unsound ones are refused, the connective is FORCED rather than chosen
-- a chain that crosses a causal step has advanced a moment, so the
result is `causes`, by §14's own persistence test.

The condition is exact rather than cautious: only members BEYOND the
seam are relocated, so a second rule whose antecedent is just the
seam composes soundly across a `causes` and is allowed. Refusing is
`None`, which this door already means as *I have nothing to say*.

## Identity, at BIND TIME -- and without th

⭐⭐⭐ **Identity, at BIND TIME** -- and without this the rest of the
identity layer is half a feature. `merge` repoints the indices, so after
merging `debt` into `owes` a rule reading `+owes($x, $y)` is OFFERED
`debt(zeta, 900)` by the argument index and then rejects it here, because
a node's own `_rel` field still says `debt`. Candidates found and thrown
away: the rule matches nothing, reports nothing, and looks like a corpus
bug. Measured exactly that way before this line existed.

 Guarded on `_merges`, so a corpus that never corefers compares two ints
as it always did. `identity_of` is called on the hottest path in the
engine and it has to cost nothing until something has merged.

## A variable in the RELATION slot. The subst

⭐ **A variable in the RELATION slot.** The substrate has always been
able to build `$p($x)` -- it is a node whose relation happens to be a
variable -- and this is the line that decided it could never match.
Binding it is what makes *apply the effect named by this ability* a
rule rather than one fact per (ability, target) pair.

 It costs §3's only index: a pattern whose relation is unknown has no
bucket, so `Situation.candidates` falls back to the ANY bucket and
scans. That is the same trade the design already takes for a
bare-variable pattern, and it is why this is allowed rather than
encouraged -- §12 says the same of a bare-variable consequent.

## `generalise`

The least general structure both `a` and `b` are instances of (Plotkin).

    The **dual of `unify`**, and the operation *learn from examples* is made of:
    matching asks what two structures have to agree about, and this asks what
    they already agree about. `unify_patterns` is the two-sided version of the
    first; nothing was the second, so an agent could recognise an instance of a
    rule it had and never propose the rule from the instances.

    ⭐⭐⭐ **`mapping` is the whole of it, and it is why this takes one.** The
    same disagreement must produce the same variable *everywhere it appears*,
    including across the two structures a caller generalises in turn. Without
    that, `f(a, a)` and `f(b, b)` generalise to `f($1, $2)` -- true, useless,
    and strictly more general than the answer -- and a premise and a conclusion
    generalised separately share no variable at all, so the rule built from them
    concludes about something nothing binds. That is the crux of building a rule
    out of two examples, and it is one dictionary.

     What agrees is KEPT. `f(a, b)` and `f(a, c)` give `f(a, $1)`, never
    `f($1, $2)`: an implementation that variabilises everything returns a
    generalisation, just not the least one, and the rule it yields fires on
    everything.

## `unify_patterns`

Unify two structures that may **both** be generic.

    §21 asked whether pattern-against-pattern is the same operation as match. It
    is not, and the differences are not incidental:

    | | match (§7) | this |
    |---|---|---|
    | sides | generic against **anchored** | generic against generic |
    | a variable binds to | a thing | a thing **or another variable** |
    | needs `walk` | no | yes -- bindings chain |
    | needs `occurs` | no | yes -- `$x = f($x)` is constructible |
    | needs standardising apart | no | yes -- two rules may reuse `$w` |

    So the floor's item 2 does not cover it. What follows is that composition
    (§4) cannot be built out of `fit`, and needs its own service -- which is the
    same conclusion `fit` reached for a different reason, and for the same
    underlying one: the caller cannot hold the answer, so the machinery must
    finish the job.

## `substitute`

Ground a consequent pattern. Anything still generic afterwards is a rule
    whose consequent names something its antecedent never bound, and the gate
    refuses it rather than minting a node nobody can read.

    **A subterm nothing changed is returned unchanged**, and that is correctness
    rather than a shortcut. Rebuilding goes through `g.rel`, which interns, so a
    subterm minted by `instance` comes back as a *different node*. A rule node is
    exactly that -- §5 needs a rule to be a node other facts can be about, so
    rule nodes do not intern.

    The test cannot be *is it ground*, because a rule node is not: it contains
    the variables of its own patterns. `+resume($h, <cb>)` binds `$h` and touches
    nothing inside `<cb>`, whose variables belong to `<cb>` and are bound by
    nobody. Rebuild it anyway and the conclusion is about an interned **twin** of
    the rule, so every later question about the real one answers nothing --
    silently, and only when rules started being pointed at.

## `already_there`

The node `substitute` WOULD produce, if it already exists. Never mints.

     **`substitute` interns, so asking with it changes the answer.** For an
    ordinary conclusion that is harmless -- a proposition nobody has claimed
    anything about is inert, and quiescence goes on to ask the CHAIN about it.
    For a stratum-0 conclusion the node's existence *is* the fact, so
    quiescence asking *would this change anything* by building the thing made
    the answer no, permanently, for whoever asked next.

    That surfaced as `ugm.arbitration` reporting the fast path choosing a move
    the slow path then found nothing to do -- **two paths over one state, where
    the first one's question consumed the second one's answer.** A predicate
    with a side effect, and this is the predicate without one.

    Three answers, and they have to be three: `GENERIC` when the consequent is
    still open (it mints nothing and changes nothing), `None` when it is ground
    and not yet derived (it would change something), and the node when it is
    already there. Collapsing the first two sends the caller back to
    `substitute` to tell them apart, which is the mint this exists to avoid.

## `Situation`

The current state, plus the one index matching actually asks for.

    §3 gives the substrate exactly one index, over instances by relation, and
    says why: *a rule whose antecedent names a relation has to start somewhere,
    and scanning every node is the alternative*. That argument is about the
    graph; it is just as true of the state, and it was not being made there --
    every antecedent member was unified against every entry.

    Signed, because a member's sign is fixed and half the entries are the wrong
    one. A member that is a **bare variable** has no relation to key on and still
    scans everything, which is correct: `+$p` is a rule that says *believe what
    this channel reported*, and it genuinely is about anything.

    ⭐⭐⭐ **And it is MAINTAINED, not rebuilt.** The index was built from the
    whole state once per tick, which is the same disease `state` cured one layer
    down: the state itself stopped being rebuilt and the index over it did not,
    so a tick stayed O(everything known) whatever matching cost. Measured:
    `Situation.__init__` was the single largest cost in the loop.

    A state changes by one claim at a time -- §4 says so -- so the index changes
    by one claim at a time too. `add` and `drop` are what a caller holding a kept
    state calls instead of constructing a new one; the constructor is still there
    for the callers that genuinely have a fresh list (a delta, the instrument).

     **Order is part of the answer.** Entries arrive here **newest-first** and
    §18's *a description with two candidates resolves to the most recent* rests
    on it. So a bucket is a dict in ARRIVAL order -- oldest first, which is the
    order a maintained state can append to -- and read back reversed. The
    reversal is cached per bucket and dropped when that bucket changes, so a
    rule reading a bucket nothing touched this tick pays nothing.

     And the honest limit of that, measured rather than assumed: reversing
    the STATE breaks 6 checks, and reversing the BUCKETS breaks none. Since
    `heap` the within-rule order is a stamp off the consumed entries' nodes, not
    the order they were discovered in, so nothing downstream reads a bucket's
    order any more. It is kept because it is what the walk says and this is a
    replacement for the walk -- not because a check would notice. `ugm.state`
    is what notices.

    ⭐⭐⭐ **And by ARGUMENT POSITION, which is the second index and a different
    quadratic.** Keyed on the relation alone, a member that has already bound
    one of its arguments still draws every instance of that relation and unifies
    each: `{ +child($p, $x), +child($x, $y) }` over N facts is N candidates for
    each of N bindings, so **one tick costs 2N² unifications** with no option set,
    no arbitration and no candidate walk involved. Reported from `pystrider`,
    who measured it as the shape their whole corpus has -- *a broad structural
    join over one relation is not a corner of what recognition does, it is what
    recognition IS* -- and reproduced here before anything was changed.

    So an entry is also filed under each of its arguments: `(sign, relation,
    position, node)`. A member whose argument is bound looks there instead, and
    the join becomes O(N × matches).

     **Only when the argument is an ATOM**, and that is soundness rather than
    conservatism. `unify` compares a ground *structure* member-by-member, so it
    accepts a structurally equal node that is not the same node -- the twin
    trap, which this repo has recorded six times -- and an index keyed on
    identity would silently drop those. An atom has no members and no relation,
    so `unify` reduces to identity for it and the bucket is exactly the set that
    could match.

    ⭐ **The narrowing keeps the ORDER**, which is why nothing else had to change:
    every candidate it removes is one `unify` would have rejected, so the
    matching candidates and their sequence are identical. `pystrider` flagged
    picking the narrowest MEMBER as the risky part -- it reorders the antecedent,
    and §18's tiebreaks read the consumed entries -- and it is not needed: the
    narrowing is per member, in the authored order.

## The third index, and it is the one attenti

⭐⭐⭐ **The third index, and it is the one attention needs: which
RELATIONS a node is currently spoken of under.**

The two above are read by a pattern that already knows its relation.
Attention arrives from the other end -- it has a NODE and no relation
at all -- so neither answers it, and the question *which rules could be
about `goblin1`* has no cheap answer without this. With it: the node's
relations are a lookup, and the rules using those relations are a
second one, so a lift costs two dict reads and no matching. That is
what makes attention cheaper than the reranker it competes with, whose
every trigger is a match.

 **Counted, not a set**, because `drop` has to be exact. Two entries
can mention one node under one relation, and dropping either would
take the relation away from a node the other still speaks of.

 It is maintained off the SAME keys the argument index files under,
which is what keeps it honest: it indexes what that index indexes, and
`ugm.state` holds it to a rebuild. So it inherits that index's own
limit -- an argument that is a structure is not filed, and neither is
it here.

## Atoms here too, and for the same reason read f

 Atoms here too, and for the same reason read from the other end:
the only thing that ever looks in one of these buckets is a
pattern member that is an atom, and an atom cannot equal a
structure. Filing the structured members as well is a bucket per
deposit that nothing can ever read -- worth 4% of the suite
(6.60s against 6.33s), which is small and is the whole of it: I
first wrote 15% here from two runs that differed in another way
as well, and the A/B says otherwise.

## `match`

Unify a generic moment against an anchored one, over the current state.

    Records which entries it matched. That is not overhead: it is what makes a
    misbehaving rule distinguishable from a misresolving chain.

    `state` may be supplied by a caller that is matching several rules at one
    seat, and the loop does. It is the same walk for all of them -- recomputing
    it per rule was 86% of the engine's runtime, measured, because every
    proposition is `resolve`d and `resolve` is itself a walk. Not an
    optimisation of the read: the read is unchanged, and asked once.

    ⭐⭐⭐ `fresh` is the **delta**, and it is what makes the loop stop
    rediscovering what it already knew. Measured before building it: of 5,775
    applications a 600-fact corpus matched, **75 were new and 5,700 were
    re-derived** -- 98.7% waste; and 92.9% on the kettle fixture, so this was
    never a big-corpus concern. The loop recomputed its whole option set on
    every move and threw all but one away.

    An application is NEW only if it consumes at least one entry deposited since
    the last look. So with `fresh` given, this runs one pass per antecedent
    member: that member draws from the delta, the others from the full state.
    Union over the passes, deduped -- an application consuming two fresh entries
    is found once per fresh member and must be reported once.

     The delta is a `Situation` like any other, so this adds no representation.
    §4 already says *a moment is a signed delta*; the matcher simply had not
    been reading it that way.

    ⭐⭐⭐ **And the pivot is walked FIRST**, which is what makes the delta pass
    cost what the delta costs. Walked in authored order, a pass pivoting on
    member 1 draws member 0 from the whole state before it ever reaches the
    delta -- so a corpus deriving one fact per tick pays O(state) per tick and
    the join is quadratic again, in the one shape `Situation`'s argument index
    cannot help with. Measured: 4,994,004 unifications over a 1,000-node tree,
    of which the index removed a third and the ordering removed the rest.

     **What may be reordered is the WALK, never the antecedent.** `consumed` is
    filled by member position, so §12's trail and `heap`'s stamp -- which reads
    the consumed entries' nodes -- see exactly what authored order would have
    given them. What does change is the order applications are *discovered* in,
    and that is measured not to be load-bearing: since `heap` nothing reads it,
    and `ugm.arbitration` compares the move on every tick of every fixture.

## An evaluated member that reads the chain. It yie

An evaluated member that reads the chain. It yields each way
its arguments can be satisfied, anchored by what is bound.

⭐⭐⭐ **A MINUS here is negation as failure, and it needs no
notation.** On an ordinary member the sign says what an entry
claims; a structural member has no entry, so the only thing a
sign can mean is *this was not derived*. `-beaten(...)` is
exactly `stratum0`'s `Item(negated=True)`, written in the
surface a corpus already has.

 Safe only because the strata are ORDERED. §6's fixpoint
is built from below, so a negated member names a relation
whose derivation is finished before this rule is reached --
and `_settled` below is what makes that true of the run and
not only of the classification. Negating a relation still
being derived would answer from a half-built extension, which
is the one way a rule-level read could disagree with the walk
non-deterministically.

## A computator: evaluated, not matched. §12'

⭐ **A computator: evaluated, not matched.** §12's skeleton is
*conditions on the binding that claim nothing* -- distinctness
is already one -- and arithmetic is exactly that. Evaluating
it HERE is what makes an application atomic: the result is
available to the same consequent, in one moment, so a transfer
cannot be caught half-done (§22).

 The arguments must be ground by now. A member whose
arguments are still open computes nothing and matches nothing,
rather than guessing -- and the pivot never lands on one (see
`run`), so authored order is what decides.

## `_anchored`

`pred($m, $n)` / `sanc($m, $n)` -- read off the chain, anchored upward.

    ⭐⭐⭐ **This is where containment stays structural.** The first argument must
    already be bound: from an anchored moment we walk toward the root, and §11
    guarantees that walk is single-valued -- *a moment has one parent; forking
    produces several successors, never several parents.* So a structural member
    can only ever name moments on the frame's own walk, and a rule inside a
    hypothesis cannot reach a sibling.

    Nothing is refused to make that true. A pattern that would need to walk
    DOWNWARD -- an unbound first argument -- simply yields nothing, in the same
    way a rule matching an entry nobody wrote matches nothing. §4's *nothing is
    prohibited* survives, and an author who genuinely wants another frame's
    chain has §17's door: inspecting is matching, with an explicit anchor.

## n was a variable and this is its VALUE -- a th

`n` was a variable and this is its VALUE -- a thing the match has
already found, so it anchors this member however generic what is
INSIDE it may be. Recursing further asks whether some other rule's
pattern, quoted inside an entry about a rule, is ground; it is not,
and answering no refused the walk an anchor it had. That is what kept
deposit order from crossing a reified entry: `in_delta($m, $e)` bound
`$e` to such an entry, and `delta_next($e, $f)` then found no anchor
and enumerated nothing (docs/observations.md Part 6.3).

## `_stored`

A skeleton relation that is IN the graph -- `pred`, `in_delta`,
    `delta_next`, `rests_on`, and whatever a stratum-0 rule concludes --
    matched by unifying against its ground instances.

    ⭐⭐⭐ **This is the whole of the second matcher, and it is four lines.**
    `stratum0._facts` read exactly this: the ground instances of a relation,
    told apart from the patterns that look for them by §7's anchored/generic
    split. A separate engine was never needed to do it; the relations simply
    were not in the resolved state, which is what `match` was being handed.

     **At least one argument must be bound**, and the discipline is *bounded
    by something already known* rather than *bounded by a named position*. My
    first version fixed the anchor at argument 0, which reads `in_delta` only as
    *a moment's entries* -- and deposit order across moments needs it the other
    way, as *an entry's moment*. Both directions are bounded; neither
    enumerates the history.

     **This is weaker than `_anchored`'s guarantee and the difference is
    worth stating.** An upward walk cannot reach a sibling branch *whatever* is
    bound (§11: one parent, several successors). Here containment holds
    COMPOSITIONALLY instead -- the binding that anchors this member came from
    somewhere, and if that somewhere was on the frame's walk so is this. The
    forking-chain check is what holds it, and it is a measurement rather than a
    construction now. Recorded, not hidden.

## GROUND, not merely not-a-variable. This

 **GROUND, not merely not-a-variable.** This asked `is_var`, which is
False for any relation instance -- so `licensed_by($e, loaded($p))` counted
`loaded($p)` as an anchor although nothing in it was known, and the walk
enumerated every instance in the history. That is exactly the leak the
paragraph above says this line prevents, available to any corpus writing a
structured argument: `rests_on($e, foo($p))`, `in_delta($m, bar($x))`.

`has_var` is not the test either, because it cannot see through bindings:
`loaded($p)` with `$p` already bound is ground in fact and generic in
shape, and refusing it would break the anchored reads §12 relies on. So
the question is asked of the binding, recursively. Measured:
docs/observations.md §3.1, finding 2.

## `_holds_at`

`holds_at($p, $m, $sign)` -- what a proposition RESOLVED TO at a moment.

    §12's `at $m` binds the LOCUS OF THE ENTRY THAT SATISFIED a member, and the
    resolved state keeps one entry per proposition -- the winner. So a corpus
    can say *the goblin acted after the hero* (two propositions, two loci) and
    cannot say *p held then and does not now* (one proposition, two times): the
    earlier claim is not in the state to be matched against. Probed: `$then`
    bound to a real moment where `ill(paul)` held, and `+ill($x) at $then` still
    matched nothing.

    `Chain.resolve` has always answered the question. What was missing was any
    way for a rule to say WHICH LOCUS TO RESOLVE AT, and this is it.

    **The seat is the moment itself**, so the answer is *as believed AT that
    moment* rather than *as believed now about that moment*. That is the
    situation reading -- what the world looked like from there -- and it is the
    only one available, because a structural walker is handed no seat. The other
    question is a different relation and should say so in its name rather than
    quietly meaning something else.

    Containment holds compositionally, as it does for `_stored`: `$m` can only
    be bound by a walk the frame could make, so a moment on a sibling branch is
    unreachable to bind in the first place.

     Nothing is minted. Building the answer as a node and unifying against it
    would intern it, and the harness's question would then be findable as its
    own answer -- the interning trap's fourth face. Only the sign slot can need
    binding, so it is bound by hand.

## `_narrowed`

The instances worth offering this member, using §3's argument-position
    index instead of every instance of the relation.

    The pivot is the bound argument with the FEWEST instances, which is the same
    choice the entry side makes and for the same reason: a join is not a scan.
    An argument counts as bound if it is a value already -- an atom or a
    structure written in the pattern -- or a variable this match has bound.
    With none bound the answer is what it always was, every instance, and
    `_stored`'s anchor rule refuses that case before it is reached.

    A STRUCTURE THAT STILL CARRIES A VARIABLE IS NOT A VALUE, and reading it as
    one is the interning trap wearing an index. `said(implies($a, $c))` asks the
    bucket for the pattern node `implies($a, $c)` itself -- a node the graph
    minted when the rule was authored, which nothing was ever an instance
    against -- so the bucket is empty and the member matches NOTHING. No error,
    no scan, no candidate: the rule is well formed, every other member is fine,
    and it silently never applies. Found while writing an interpreter for
    rules-as-facts, where every member has this shape; a corpus that only ever
    writes atoms in argument positions cannot reach it, which is why 549 checks
    could not.

    Skipping it falls back to `instances_of`, which is the answer this function
    already gives when nothing is bound -- so the cost is the scan the docstring
    above already sanctions, paid only by a member that could not be indexed
    anyway.

    ⭐⭐⭐ **...and the fallback SAYS SO, which is
    `docs/interpretation-feedback.md` §3.** The paragraph above sanctions the
    cost and is silent about the count, and those are different things: an
    author cannot tell a member that joins from a member that scans, because
    both are well formed, both find the right answers, and only one of them is
    the difference between a parse and a hang on a corpus whose members are
    pattern-heavy by construction. The information exists exactly here, at the
    point where it was being discarded.

     Counted on the GRAPH rather than reported by return value, because this
    is a generator's inner loop reached through two structural readers that have
    no report to write on and no rule in hand. Keyed by the member as written,
    which is what an author has to go and change.

     **Both the count and the SIZE, because the count alone does not rank
    them.** Measured on `ugm.interpret`: `asking($s)` falls back 169 times and
    `met($a)` 16, which reads as one problem and one footnote -- and `asking`
    has a single instance, so those 169 fallbacks visit 169 nodes between them
    while the 16 walk a bucket that grows with the run. A member that cannot be
    indexed over a relation with one instance costs nothing and is not worth an
    author's afternoon. What was being discarded here is the join that did not
    happen; what decides whether that matters is how big the scan was.

## `_as_fact`

Unify a structural want against a candidate node, and answer only if the
    candidate is a FACT rather than a pattern.

    §7 splits generic from anchored, and this seam asked it as `has_var` over
    the whole candidate node. That is the wrong question for a chain-deposited
    relation, and the cost was measured: a reified rule is deposited as a
    mention, so its proposition is the rule's pattern, so the entry node carries
    that pattern's variables -- and with them every `mentioned`, `in_delta` and
    `delta_next` fact about it. On one four-line corpus, 97 of 125 `mentioned`
    facts and 175 of 216 `delta_next` facts were invisible to the matcher,
    although the chain deposited every one of them and nobody authored any of
    them as a pattern. `delta_next` is a chain, so each hidden link severed
    deposit order across it, and the rule-level read came back with two answers
    where `Chain.resolve` has one (docs/observations.md Part 6.3).

    The question §7 actually asks is already written down in `unify_patterns`'s
    own table: in MATCH, *a variable binds to a thing*; binding a variable to
    another variable is the pattern-against-pattern operation, and that is a
    different service. So that is the test -- match, and refuse the result if it
    bound a variable to a variable. A rule's own member, interned and therefore
    found among the instances of its relation, unifies with itself variable for
    variable and is refused; a chain fact about a generic proposition binds a
    variable to a STRUCTURE that contains variables, which is exactly what a
    rule reading about rules is for.

## `_bounded`

A skeleton relation that needs no anchor, because it is bounded by
    construction: `asking(<seat>)`, and whatever a stratum-0 rule concludes.

    ⭐⭐⭐ **This is where the anchoring discipline actually divides, and it is
    not where I first drew it.** `_stored` refuses an unbound pattern because
    the chain's own relations are facts about the WHOLE HISTORY -- deposited
    whether or not anything asked -- so an unanchored `in_delta` would walk all
    of it and reach another frame's delta.

    These are not that. `asking` IS the question, and a derived relation exists
    only because the question was asked: every instance of `cand` was reached
    through an anchored walk from a seeded seat, so enumerating them enumerates
    what the anchor already admitted. Requiring an anchor here refuses the read
    its own conclusions -- which it did, and `beaten` and `best` derived
    nothing at all while `cand` derived 193.

     The containment argument therefore rests on the SEED. A machinery that
    seeds a seat the frame cannot see would derive facts about it, and nothing
    structural would stop it. `Machine.ask_read` is the one caller.

## `_span_of`

`span_of($s, $start, $end)` -- a stretch of the chain (§11).

    `entry_of`'s shape one construct along, and read the same two ways:

      * **endpoints bound** -- the span is MINTED. §11 says spans are *minted by
        recognisers, never enumerated*, and a rule with this member is what a
        recogniser is: `<TT-base>` builds the stretch it has just recognised.
      * **the span bound** -- it is decomposed, like any other node's members.

     Unanchored it yields nothing, and here that is not politeness but the
    population: any two moments form a span, so enumerating them is quadratic in
    the history and every one of them meaningless until something recognises
    over it.

     **Yes, this MINTS while matching, and the interning trap is why that
    needs an argument rather than a shrug.** A quiescence verdict computed with
    `substitute` was unsound precisely because minting made the conclusion exist
    -- so a matcher that creates nodes is the same shape. The difference is what
    the node's existence means. A stratum-0 conclusion IS the fact, so creating
    it answers the question being asked; a span node is a *name for a pair of
    moments*, and nothing anywhere reads whether one exists -- `span` is in no
    structural relation, so no rule can enumerate spans and no walk visits them.
    Interning then makes this idempotent: the same endpoints give the same node
    however many times any path asks. So the match is pure in the only sense the
    trap is about -- asking twice gives the same answer, and asking does not
    change what anything else would answer.

## `structural_relations`

The skeleton, as members an ordinary rule may write (§6, §12).

    §6 says stratum 0 is *a property of a rule* -- every antecedent member is
    structural -- decided *by inspecting an antecedent rather than by a designer
    assigning layers*, and that it *runs under the same interpreter*. A separate
    engine with its own rule and item types is the branch that sentence forbids.
    This is what removes it.

    Two kinds, and the difference is whether the fact is stored:

      * **stored** -- `pred`, `in_delta`, `delta_next`, `rests_on` are relation
        instances the chain deposits as it builds. Matched against the graph.
      * **walked** -- `anc`, `sanc` are transitive closures, and §3 says a
        stored closure would be a cache of something derived. Anchored, upward,
        and single-valued by §11, which is what keeps containment structural.

     `entry_of` is a third thing again: not stored and not walked, but *read
    off the node's own members*. An entry is a relation instance like any other
    and always was.

## pred was the reflexive-transitive walk,

 **`pred` was the reflexive-transitive walk, under the name of the
immediate one.** It was registered for corpora to write (`machine.py`'s
name table) and no rule in this repo or the foreign one ever wrote it, so
nothing could see that `pred($m, $n)` yielded every ancestor AND `$m`
itself. `anc` is that walk and now carries the name; `pred` is the stored
immediate-predecessor fact the chain actually deposits. A name a corpus
may write whose meaning is not what the name says is worse than an absent
one, because a corpus that used it would have been right to trust it.

## `arbitrate`

Among the rules that matched, choose one. Total: it always answers.

    Two steps, and they are not the same step.

    **Out of the running first.** `dormant(<R>)` is not a ranking: a rule the
    graph claims is dormant is not considered at all, and it comes back when
    something claims `due`. Merely ranking it low would let it apply on a later
    tick and overwrite what the agent decided instead -- ordering is not
    removal, which is the whole reason the claim exists.

    **Then choose.** Three keys, in this order, and the order is the argument.

        apparatus     a `standing` rule keeps its authored place
        helpfulness   what the situation recommends (`prefer`)
        authoring     the order they were written in

    There is no authority key. It used to be `overrides`, applied above as
    defeat; a corpus that wants one rule to beat another says which of them is
    out, or writes the premise that tells them apart.

    The apparatus next, and this one was found by breaking it. Preference is
    derived from *what serves the current goal*, and let loose over everything it
    outranked the rules that notice a **surprise** -- so the agent carried on
    pursuing a goal while a channel was telling it the world had moved. Being
    helpful towards a goal is not a reason to outrank the machinery that decides
    whether the goal still makes sense. `standing` rules therefore keep the
    authored order they already had, and preference orders what is left.

    Helpfulness third is the change, and what it replaces is worth naming. The
    tie among applicable, undefeated rules used to be broken by **the order they
    happened to be written in** -- an accident of authoring, deciding which of
    several possible moves an agent makes, including the irreversible ones. A
    derived preference is not obviously right, but it is not an accident, and it
    is a claim the trail records and a corpus can argue with.

    Still a lookup that never searches (§14), so it stays total: with no
    preferences it is exactly the authored order it always was.

## What `defeat` was

`defeat` dropped the applications whose rule was overridden by another that
matched. It ran on everything that matched, before any quiescence filter, and
that order was load-bearing: filter first and the winner disappears as soon as
its conclusion is written, whereupon the loser is unopposed and overwrites it.
It had a fallback for a cycle in `overrides`, asked of the RULES rather than of
the applications handed in, so that arbitration stayed total.

All of it is deleted with the relation. A rule is out because the graph claims
`dormant(<R>)`, which is read once where the ordering is built -- there is no
set to compare, no cycle to break, and nothing that can make arbitration
partial.
