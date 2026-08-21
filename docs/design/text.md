# `core/text.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

A surface for authoring graphs (§3, §8).

One grammar, because it is all one kind of thing: a rule is a relation instance,
`by(R, boss)` is a relation instance, `raining(here)` is a relation instance.
That is R3 and R4 in the surface rather than claimed in prose -- there is no rule
syntax distinct from fact syntax, because there is no rule *node* distinct in kind
from a fact node.

What the language may NOT write is an entry, a moment or a stamp. §13 scores
`authors write entries natively` as a leak: an author who can supply a deposit can
date a claim to when it was not held. So the locus, the deposit, the licence and
the source come from the gate, always.

The line is §4's anchored/generic split. A rule's members are *generic* entries --
signed, with variable loci -- and those are authorable, because a variable commits
to no occasion. Anchored ones never are.

Three statements, with the author saying which, so the loader branches on nothing:

    rule  boil = causes( { +heat(?a,?w), +water(?w) }, { +boiling(?w) } )
    fact  +on(a, b)                    standing knowledge, stamped source=kb
    say   user: +raining(here)         an arrival on the channel `user`
    fact  overrides(<boil>, <cool>)        an ordinary claim, and it seeds precedence
    fact  <how-many> = count(harm(?x))            a named statement
    fact  -<no-harm>                       ...which other statements can be about

A fact may carry a name, in the same angle brackets a rule's goes in, because
`<...>` is the namespace of **statements** and a rule is a statement. It earns its
place on descriptions: `count(harm(?x))` contains variables, and §8
scopes a statement's variables to it, so writing it twice writes two nodes that
say a similar thing. A description has no identity but the one an author gives it,
and without a name a norm could be stated and never retired.

The notation is the design document's own, in ASCII: `-` for the minus sign it
writes as an en dash, `->` for its arrow. §8's worked rules parse as printed.

## `Term`

A relation instance, an atom, a variable or a rule reference, still
    unresolved against a graph.

    ⭐ `fn` is the relation slot when it holds a whole TERM rather than a name --
    `a(b)(c)`, the node whose relation is `a(b)`. The substrate has always built
    one (a node's relation is a node like any other, and `show` renders it by
    recursing), `unify` learned to compare one when `?p(?t)` landed, and this is
    the last component that could not read it.

    ⚠ Set only for a CHAINED application, so every term that parsed before this
    existed still parses to the identical shape. `a(b)` is `Term("a", (b,))` as
    it always was, not `Term("", (b,), fn=Term("a"))` -- which matters because
    `_fact` reads `term.head` against `DESCRIBES` to spot one, and rewriting the
    common case would have moved that head one level down and retired every norm
    in the suite silently.

## `PostClause`

A postcondition, as written: a query, and what it spends if it holds.

        rule <classify> = implies( { +asked(?x) }, { +considered(?x) } )
          after { +penguin(?x) } => attend(?x, 3)
          frozen after => unattend

    The query is an ordinary antecedent -- no new notation, and the same
    matcher -- and it is matched with the rule's OWN bindings already in hand,
    so `?x` above is the `?x` the rule bound. A bare `after` is the query that
    asks nothing and always holds.

    `frozen` marks what a calibration process may not touch, and `learned` its
    complement -- what play added rather than what a person wrote. Neither
    changes how the postcondition RUNS, which is the point: an authored lesson
    and a learned one are the same construct, and only the learner treats them
    differently.

    ⭐⭐⭐ **Three provenance levels over one mechanism**, and they are what make
    the learned half separable:

        frozen      the machinery may not touch this
        (plain)     a person wrote it
        learned     play added it, and re-learning may replace it

    ⚠ And learning ADJUSTS rather than replaces, which needs no arithmetic at
    all: two postconditions on one rule both spend, so an authored `attend(?x)`
    beside a learned `attend(?y)` leaves the agent thinking about both. Measured.
    Strip every `learned` line and the bootstrap is exactly what is left.

## Which expert the rules below belong to, and op

⭐ Which expert the rules below belong to, and optionally which
other expert's rules it inherits:

    expert geometry
    expert geometry extends arithmetic

It declares nothing the surface could not already write --
`knows(geometry, <R>)` and `extends(geometry, arithmetic)` are
ordinary facts, and staying ordinary facts is what makes *which
rules does this expert have* an ordinary query (R4). What the
keyword buys is not having to name every rule twice.

## The action palette, declared:

⭐⭐⭐ **The action palette, declared:**

    action move(?x, ?y)

A SIGNATURE and nothing else. It says what the agent may ask to
do; the world model's own rules say what happens when it asks, and
one of them may refuse. Keeping those apart is the point: an
illegal request that merely fails to match is silence, and this
design's standing complaint is that silence reads as a corpus bug.

⚠ No angle brackets. `<...>` names STATEMENTS, and an action is
not a statement -- it is a term the agent may deposit, so it is
named the way a relation instance is named, by being written.

## A fact may be NAMED, and the name goes in the sa

A fact may be NAMED, and the name goes in the same angle brackets a
rule's does, because it is the same namespace: names of
*statements*, kept out of the relation namespace.

It earns its place on descriptions. `count(harm(?x))`
contains variables, and §8 scopes a statement's variables to it --
so writing it twice writes two nodes that say a similar thing, and
a denial of the second leaves the first forbidding. A description
has no identity but the one the author gives it.

## `trigger`

`after <A> { ... } => attend(?x, 3)`.

        `after` fires when its rule applies and its query holds. `frozen` marks
        what a calibration process may not touch.

        ⚠⚠⚠ **`when` IS REFUSED, and that is a change from a silent no-op.** A
        `when` trigger fired at RANKING time and belonged to no rule; the only
        thing that ran one was `_rerank`, which reordered a shortlist by the
        buffs the trigger spent. Both are retired, so a `when` trigger now
        reaches nothing at all -- it would parse, load, and never run. A corpus
        whose lesson silently does nothing is the worst outcome available here,
        so it is an error instead. Everything a reranker could say, an `after`
        trigger on the rule that RAN can say, and it says it about a move that
        actually happened.

## +acts(goblin) at ?m -- WHERE the entry sits.

⭐ `+acts(goblin) at ?m` -- WHERE the entry sits. §12 calls the short
form an abbreviation for the entry, whose locus the frame supplies;
this is how a rule says otherwise, and it relates two moments.

⚠ Written out rather than punctuated. `@` used to mean a grade and is
now refused with a message (above); reusing it would be the island §2
warns about, on the page. A bare name here is unambiguous because a
member is followed by `,` or `}`.

## The name scope, and whether it is shared.

⭐⭐⭐ **The name scope, and whether it is shared.** A corpus is a bound:
`kettle` means one node inside it, by construction and not by
inference, which is why coreference does not arise in authored
knowledge at all. What that cost, until now, is that two documents
could not be about the same kettle -- each `load` had a private table,
so a book split into chapters was forty disconnected islands and
nothing could bridge them.

Naming the bound fixes it without weakening it. Documents loaded under
the same scope resolve names against one table, so identity is still
decided at intake and still by construction; documents under different
scopes stay apart, which is the default and is what a fresh corpus
wants.

⚠ Note what this deliberately does NOT do: assert identity in the
graph. `sameas(a, b)` would need equals-for-equals in matching, and
congruence is either machinery (a decision nobody can argue with) or a
rule per relation per position (combinatorial). Deciding identity when
the name is READ keeps it a construction. Identity discovered later is
then a revision of intake -- re-read the document with the binding
corrected -- which is the same shape `learned()` already has for rules.

## A domain is a channel, and that is the wh

⭐⭐ **A domain is a channel**, and that is the whole of what a domain
needs to be. §13 already says the knowledge base IS a channel; a named
scope refines it rather than adding a fourth concept, so a fact loaded
under `scope="billing"` is stamped as having come from billing and
provenance answers *which domain is this from* with nothing new.

What it is FOR: deciding what is in mind. Measured before building --
three domains loaded, a goal in one of them, 23.5s and 600 ticks; the
same goal with only its own domain in mind, 1.6s and 198 ticks, and
**the identical 196 conclusions, none missing and none extra**. The
agent has always narrowed which RULES come to mind (`dormant`/`due`)
and has never narrowed which facts do.

⚠ Unscoped documents keep `kb`, which is what every corpus has had.
⚠⚠⚠ **Sharing names and sharing provenance are DIFFERENT things**, and
tying them together was wrong -- caught by the first fixture that used
both. Rules about billing must resolve `owes` to the same node the
billing facts do, so they share a *scope*; but they are not billing
data, and unloading billing must not unload the rules that read it.
So a document declares its name table and its domain separately, and
`domain` defaults to `scope` because the simple case is one of each.

## The bundle, by name. Every section of the design

The bundle, by name. Every section of the design that says *a corpus
can override this* depended on it and none of it was true: the loader
knew only the names a corpus had declared itself, so `<assert-act>`,
`<give-up>` and the rest were unnameable and therefore unarguable --
shipped as data and reachable only from Python.

One table, so a corpus rule may not reuse a bundled name. That is the
marker doing its job: two statements with one name is what `<...>`
exists to prevent.

## `answerer`

Register a tool **in this corpus's scope**, which is the only scope in
        which its request has a meaning.

        A tool answers a request, a request is a relation, and a relation is a
        name -- and names are not identity here. Registering `oracle` to answer
        `guess` through `Machine.answerer` mints a *second* `guess` beside the one
        the corpus will write, so the tool sits waiting for a request nobody can
        make. Measured, and it is the same twin the bundle's vocabulary turned up
        an hour earlier: **anything that binds a name has to go through the table
        that resolves it.**

        Registered before `load`, because a rule may name the tool (`<oracle>`)
        and `<...>` is resolved at authoring.

        `fn(machine, frame, entry)` returns the answer node, or `None` for *I
        have nothing to say*. ⚠ Said here as well as on `Machine.answerer`
        because this is the door the note above tells everyone to use, and a
        reader who never opens the other one has no way to learn the arity from
        the one they are told to call.

## The apparatus must not be joined on its ow

⚠⚠⚠ **The apparatus must not be joined on its own requests, and this
was found by the apparatus squatting on a name a fixture already
used.** `_answer` calls EVERY answerer bound to a relation, so a
corpus tool registered on `compose` and the apparatus's own composer
both fire on every such write -- and they coexisted only because each
declined the other's arity, which is coincidence, not design.

It is the twin trap inverted: not two nodes for one name, but two
answerers for one node. The consequence is worse than a twin, because
a tool PROPOSES and the apparatus CONCLUDES (§19), so the collision
silently gives a corpus's tool a share of a request whose answer the
agent acts on directly.

Refused at registration, which is where the claim is made and the only
moment the caller is looking at it -- the same argument the arity check
beside this one is made from.

## A NUMERAL is not this document's name for

⚠⚠⚠ **A NUMERAL is not this document's name for something.** Two
corpora may be about different kettles and are never about
different 2s. `Machine.NUMERAL` already says so and `reserved`
already seeds this table from it -- but `reserved` is a snapshot
taken at boot and it stops at nine, so `12` fell through to
`g.atom` and minted a node per document. Nothing had computed a
numeral before, so nothing had noticed; `_count` computes one, and
a count of twelve would have been a twin of every authored 12.
The twin trap, seventh time, and the same answer as the other six.

## `_note_shadow`

A bare name in an ARGUMENT position that resolves to a reserved node.

        ⚠⚠⚠ **One node with two meanings, which is the twin trap inverted.**
        `reserved` binds `plus`/`minus` to the SIGN atoms and every corpus's
        table is seeded from it, so a domain author writing an arithmetic
        operator gets the sign: `calc(minus, 5, 2)` lands as `calc(-, 5, 2)`,
        the tool declines a request it should have answered, and the run stalls
        with nothing saying why. Reported from a foreign corpus, which lost a
        debugging session to it.

        It is a **report and not a refusal**, and that is forced rather than
        timid: `+expects(?p, plus)` and `+says(user, ?p, plus)` are legitimate
        and there are twenty-odd of them, so the loader cannot tell an operator
        from a sign. What it can do is stop being silent -- which is §5's rule
        about the places machinery declines without saying so, arriving at the
        one place a name changes meaning under the author's feet.

## `term`

Resolve one term against this corpus's names, for asking questions.

        Names are not identity (see `graph.py`) -- a node is identified by being
        the node it is, and `atom()` mints a fresh one every call. What gives a
        name meaning is a *scope*, and the corpus is that scope. So a question
        about what was loaded has to be asked through the loader that loaded it,
        which is the honest arrangement rather than an inconvenience.

        ⚠⚠⚠ **It refuses leftovers, and until a foreign corpus reported it, it
        did not.** `term("a b")` returned `a` and `term("a(b) junk here")`
        returned `a(b)`, silently -- one term parsed and the rest of the string
        dropped. The `fact` and `rule` paths refuse loudly; this one did not, and
        this one is what `Loader.say` uses. So **an agent could say one thing and
        the hearer believe another**, with nothing anywhere reporting a
        difference (`docs/quest-feedback.md` §5).

        That is worse than a parse error, because a truncation is still a valid
        term: it fails as a **wrong answer** rather than as a crash, which this
        repository has recorded as its most expensive failure shape.

## A fact that NAMES a rule is mentioning it, and a

A fact that NAMES a rule is mentioning it, and a rule node contains the
variables of its own patterns. `overrides(<why>, <boil>)` is a ground
claim about two rules, not a generic claim -- R3 depends on being able
to write it. The `<...>` marker is what makes the distinction visible
here, where structurally the two are identical (§13).
A norm's argument is a DESCRIPTION, not a proposition:
`count(harm(?x))` names a class of acts, exactly as
`ant(<R>, heat(?a, ?w))` names a class of premises. Both are ground
claims that happen to contain variables, and §13 says what tells them
apart is who is writing -- here, an author who wrote a described head.

This is one name in Appendix C's census, and it is the honest price of
letting a corpus state a norm at all: a norm about one act would be
useless, and a norm expressed as a rule is a competitor in recall.

## : Heads whose ARGUMENT is a description rather t

: Heads whose ARGUMENT is a description rather than a proposition, so a
: variable inside one is a class and not an unbound conclusion.
:
: ⚠⚠⚠ **A tuple rather than a third scattered string comparison.** `_fact` read
: `term.head` against `DESCRIBES` in one place and the consequent check knew nothing
: about it, and `docs/quest-feedback.md` §6 reported how sharp that edge is: a
: foreign corpus declined the tidier parser refactor precisely because moving
: that head one level down would have *retired every norm in the suite
: silently*. Adding `count` as a second literal in two more places is how that
: happens again, so the set is named once and read everywhere.
:
: `count(goblin(?x))` names a class of things to be counted, and a norm's
: shape is now said in a trigger's antecedent instead. Same price, same reason
: §13 allows it: what tells a description from a generic claim is who is
: writing.

## `_vars_in`

Every variable in a structure -- **including one in RELATION position.**

    ⚠⚠⚠ It did not look at the relation, and `Graph.has_var` always has: `_mint`
    computes genericity as *the relation is generic, or any member is*. So the
    two disagreed about `?verb(?a, ?b)`, and the binding check is built from
    both -- `has_var` decides whether a consequent needs checking and this
    decides what would satisfy it.

    The disagreement cut both ways, which is why it survived. A consequent
    `+?r(?x, ?y)` passed the check because `?r` was never *wanted*; an antecedent
    `+ev_at(?verb(?a, ?b), ?t)` failed it because `?verb` was never *had* -- so
    destructuring a description was refused at the surface while `match` handled
    it perfectly (measured: 2 matches, `?verb` bound to `attack` and `steal`).

    ⭐ That is what blocked a **generic** interpreter: one rule per predicate was
    forced, because a rule could not be written over the predicate itself.

## `_report_unwebbed`

Say when a rule reads a name nothing anywhere writes.

    ⭐⭐⭐ **The open class's own price, detected by the open class's own
    property.** A proposition needs no implementation, so a name awaiting its
    meaning and a name that is a typo are both well formed and both inert --
    and nothing in the engine could tell them apart. Meaning is the web, so a
    name with no web is the mistake, and this is where an author is looking.

    A note rather than an error, deliberately, and `_report_shadowed`'s argument
    applies unchanged: **we cannot catch every mistake, so this must not pretend
    to.** A corpus fed by a live channel legitimately reads what its own text
    never writes; refusing it would be wrong, and staying silent is the failure
    being repaired.

    ⚠⚠⚠ **Called from the DOOR, not from `load`, and that is a measurement.**
    Wired into every `load` it fired **91 times across the suite** -- and every
    one was correct, because a suite is made of deliberately partial fixtures:
    a rule loaded to test something else, whose premise nobody ever supplies.
    Correct and useless is still useless, because a note that fires ninety-one
    times is a note an author learns to skip. The four real corpora report
    **zero**. So it is said where an author actually loads a corpus to run it,
    and `Machine.unwebbed` stays available to anything that wants to ask.

    ⚠ Computed over the WHOLE machine rather than one document, because a corpus
    may span documents (§17's scopes) and the fact that satisfies a rule may
    arrive in the next one.

    ⚠ A fact arriving on a CHANNEL does not count as written, and that is right:
    `say user: +heat(...)` deposits `arrived(user, heat(...), +)`, so `heat` is
    an argument and not a claim until some rule asserts it. A corpus that never
    writes that rule genuinely cannot fire, and the note says so.
