# Planning, the closed class rechallenged, and meta-concept unification — how this arc actually went

**Status: design note, 2026-07-30. Written in prose, deliberately, because the shorthand this project
usually writes in compresses an argument that needs its reasoning kept visible to be trustworthy later.**
This document narrates one continuous conversation, starting from a seemingly narrow question — how does
an agent go from having explored a plan to actually executing it? — and ending somewhere much larger: a
challenge to what this project has been calling the closed class, and a first confirmation that four
things that looked like they might need separate architectures (goals, procedures, questions, and
prohibitions) are actually one thing wearing different surfaces. Read `goal_machinery.md` first for the
goal/subgoal machinery this whole arc builds on; `closed_class_rechallenged.md` for the sharper, standalone
version of the closed-class argument; this document is the connective tissue between them, told in the
order it was actually discovered, including the wrong turns, because the wrong turns are part of why the
right answer is trustworthy.

---

## 1. Where this started: exploration versus execution

The immediate question was mechanical. Suppose an agent is considering a plan — say, searching a
knowledge base by listing some files and then examining each one. Before actually running any of it, the
agent might want to explore: is this plan any good? What would it produce if it worked? The engine already
had a mechanism for exactly this kind of cheap, discardable reasoning — the supposition machinery
(`suppose()`/`supposing()`, and the write-back filter that ensures a mutating rule powered by a
supposition can never actually touch the real world, proven by `test_a_mutating_rule_inside_a_supposition_
does_not_act_on_the_world`, the "umbrella" test). So the first-pass answer was: let exploration happen
inside a supposition, and let execution happen for real once the agent commits. That much held up, and it
still holds up — but it was incomplete in a way that took a few more steps to see clearly.

The incompleteness was this: scoping (inside a supposition versus not) determines whether an action is
*safe*, but it says nothing about *what gets minted*. A rule that would explore "what would listing files
produce" has to mint something different from a rule that actually dispatches a real tool call — not
because one is scoped differently, but because they are, literally, different acts. Trying to make one
rule behave differently depending on where it happens to be wired was a category error, caught directly in
conversation: the fix was to author the plan step itself as neutral, mode-independent data (just "this
step means: run this tool, bind the result to this name"), and to write two small, generic interpreter
rules that read that same neutral data — one mints a placeholder standing in for "whatever this would
produce," wired under a supposition; the other mints a real `<call>` occurrence (reusing the old `ugm`
engine's already-validated suspend-and-dispatch mechanism), wired only once the plan has actually been
committed to. Both interpreters are written once, generically — a plan's every step is just more
step-shaped data, and which interpreter gets to see it is a matter of wiring, not of the step's content.

Deciding when to actually cross from exploring to committing turned out to have its own small trap. A rule
whose *input* reads inside a supposition and whose *effect* is meant to be real runs straight into the
same wall `cnl_engine_goal_plan.md` had already found and shelved for SUPPOSE's discharge: the engine's
support-tracking mechanism (`powering()`, a backward walk over wiring) taints anything downstream of a
supposition regardless of what it chooses to conclude, so a naively-wired "commit" rule would itself become
trapped inside the hypothesis it's trying to escape. The way out did not require reviving the shelved
discharge mechanism. It came from a different, already-established finding — that the *outer driver*
(ordinary Python orchestrating the engine, the same layer `system1_experiment.py` already established does
retrieval) has no tunnel of its own, because `powering()` only constrains wired `StandingUnit`s, never a
plain Python read. So the outer driver can read across as many supposition-scoped candidate plans as it
likes, pick a winner by whatever judgment it wants to apply, and then commit by writing one real fact
directly — the one deliberate, explicit crossing of the boundary, and the only place in the whole design
where anything is decided outside of ordinary rule matching.

## 2. Real side effects force honesty about recomputation

Once execution was on the table, tool calls with real, persistent side effects raised a sharper concern
than anything purely reasoning-shaped had: if a mutating rule invoking a tool ever fires more than once for
the same underlying reason, that is not a bookkeeping nuisance, it is a real, possibly expensive or
dangerous mistake. This produced two intertwined findings, discovered partly by making the mistake and
catching it.

The first is that avoiding a double-firing rule does not need a new engine mechanism, but it does need a
correct choice between two existing shapes. A defeasible, revisable conclusion — "assumed safe until shown
otherwise" — should be a computation unit's output (`mutating=False`), because a computation unit's cell is
discarded and recomputed fresh every revive; nothing accumulates, so nothing can double-fire, by
construction. A sticky, one-way transition — a case moving from "new" to "handled," a signal being logged
as a complaint — needs the opposite: a mutating rule whose own positive premise is invalidated by its own
effect, so the second attempt simply finds nothing left to match. Building this directly surfaced a subtlety
worth stating precisely: it is not enough for the rule to flip a status attribute; if the axiom that first
delivered the *original* value is never retired, the read layer keeps that stale value alive forever as a
second, disagreeing "reading," and a conflicted read is silently `None` rather than the true, updated value
(`View.attr`'s documented behavior, `overlay.py`). This was caught directly — an experiment reporting
`status: None` when the underlying graph plainly held `"handled"` — and the fix was exactly the discipline
`goal_experiment.py`'s corrected lineage check had already established for an unrelated reason: null a
stale axiom's held value the moment a reused reflective snapshot takes over as the ongoing channel.

The second finding sharpened a claim that looked plausible at first and turned out to be subtly wrong: that
genuinely repeatable events (a customer complaint, as opposed to a one-way state transition) are naturally
exempt from double-firing risk, since two complaints really are two different things. Checked directly, an
unmarked triggering signal produced not one complaint per distinct signal but an unbounded stream of new
complaints from the *same* signal, once per idle turn, forever — because the signal itself persists in the
graph and nothing about "it's an event" stops a rule's positive premise from matching it again. The correct
discipline turned out to be uniform across both cases: whatever triggers a mutating rule's action must
itself be marked consumed in the same firing that reacts to it, whether the mint is a bare attribute flip
or a brand-new record. There is no third, dedup-exempt category for events; there is only whether the
trigger has, or does not have, its own consumption marker.

Both findings converged on a conclusion about *when the outer driver should even call `revive()`* — not
merely how a fired rule should protect itself. A rule with a real side effect, even correctly guarded, is
only ever safe to consider firing *at all* when there is something new to react to. Calling `revive()` on
a blind cadence, "just to check," turns a single missed guard into an unbounded stream of repeated
side effects rather than a single, bounded mistake. The two disciplines are complementary rather than
redundant: consumption-marking makes a rule safe within a revive that had to happen anyway; recomputing
only on genuine change stops revives from happening when nothing gave them a reason to, bounding the
damage even a real authoring mistake could do.

## 3. Closed-world defaults, and trying hard before assuming no

A separate thread ran alongside this one, about what a rule should conclude when the thing it is looking
for simply is not there. The old `ugm` engine had already worked this question out once, with a
four-status model — a goal can be derivable (a real yes), its negation can be derivable (a hard, entailed
no), or, if neither is derivable, the concept in question is either closed-world (a defeasible "no, to the
best of current knowledge," revisable later) or open-world (absence proves nothing; go gather evidence).
Crucially, that engine also refused to read fuel exhaustion as a no — running out of budget mid-search
produces an honest "I did not finish looking," never a decided negative.

Porting the *shape* of this distinction across, rather than the specific mechanism, took some care, because
the old engine's per-predicate policy was a Python object passed at call time — exactly the kind of
hardcoded, ungraph-reachable stance this project's composability principle already rules out. The
translation that actually worked, checked against a real worked example, was to make openness an ordinary
fact on the concept's own node, consulted as a positive premise by whichever rule needs it — nothing new
at the engine level, just a fact like any other. A second, easy-to-miss requirement turned out to matter
just as much: a defeasible "assumed no" conclusion should itself be a computation unit's output, not a
mutating rule's, for exactly the reason worked out in the previous section — a computation unit is
recomputed fresh every revive, so it is revisable for free the instant new evidence appears, with no
retraction machinery needed at all. And the "try hard first" instinct — do not conclude absence just
because nothing has shown up *yet* — turned out to need no new primitive either. A flagged concept's own
investigate rule, wired with the stance fact as an ordinary positive premise, only fires for concepts that
were actually flagged; nothing about "configurable per concept" needed anything beyond which fact happens
to be true of a given node. Checked directly, a flagged concept produced no defeasible middle state at all
— it stayed honestly pending until a real subgoal resolved it one way or the other, never silently falling
back to a guess.

## 4. Planning under genuine, unenumerable uncertainty

The most important correction in this whole arc came from pushing back on an idea that sounded
sophisticated but was actually the wrong tool for the job: proving, in advance, that a plan handles every
possible outcome. The counterexample that settled it was mundane and definitive — nobody planning a drive
enumerates every possible red light or moment of traffic in advance, and no computational technique changes
that fact, because the domain genuinely is open-ended. Trying to prove a plan schema sound for *every*
instantiation, the way `smt_sieve.py` already does for the small, genuinely closed vocabulary of connective
forms, would be exactly the eager, exhaustive-completion posture this project has already and repeatedly
rejected under the "agent, not theorem prover" banner.

The actual answer was already present in pieces, just not yet assembled for this purpose. A plan should
anticipate only a small, human-scale set of expected branches, each an ordinary rule matching one specific
outcome. Reality, once a step actually executes, either matches one of them, in which case an ordinary rule
fires and an ordinary `achieved` follows, or it matches none of them — and *that* case needs no advance
knowledge of what specifically went unforeseen. A catch-all rule, gated on positive evidence that the step
genuinely completed and the absence of any anticipated match (the same closure-before-NAC shape
`goal_decomposition_experiment.py` had already needed for an unrelated reason), concludes `diverged`
honestly, without needing to know why. From there, `diverged` is just another positive fact, and the old
`ugm` plan-act-check-replan loop — already validated as portable prior art, discrepancy as an ordinary
fact a rule reacts to, no special replanning mechanism required — picks it up. This is not merely a
workaround for the limits of proof; it is closer to how planning actually works for any agent operating in
a genuinely open world, which is presumably why the old engine's designers built it that way the first
time.

One further, complementary piece belongs here, though it turned out to be an addition rather than a
requirement: the engine already carries a real possibilistic layer, inherited whole from an earlier design
pass and simply unused by anything built this session — a finite ordered scale of band words, a default
theta threshold, and a min-join across a derivation chain, already wired directly into the matcher's
handling of graded premises and graded negation. This lets an anticipated branch carry its own likelihood,
so a consumer can decide how decisively to commit to the most plausible branch before it is confirmed, or
wait for real evidence when the cost of being wrong is high — exactly the cautious-versus-decisive dial the
old engine already had as a swappable stance. It matters that this stays a refinement of *which* branch to
prepare for, never a way to loosen the catch-all's honesty; the catch-all should stay crisp, because that is
precisely the one place a false positive would be actively dangerous.

## 5. The conflation underneath all of it: representation is not execution

Designing the mechanism that would actually turn a plan's causal or business content into an executable
step surfaced something that had been quietly present in several earlier worked examples without ever being
named. A fact like "doing X usually causes Y," or a business rule like "orders over 500k must ship early,"
is not something the engine should ever execute directly, as though its left-hand side and right-hand side
were an ordinary `StandingUnit`'s pattern and effect. It is content — open-ended, unbounded, and, crucially,
something the engine has no notion of understanding. What the engine actually has is a small, fixed,
genuinely engine-native convention for physically manipulating the graph — mint a node, add an edge, set an
attribute, merge, drop — and a causal or normative fact should be authored as ordinary data in *its own*
conventional shape, then *read*, never executed, by a generic meta-rule whose left-hand side matches that
shape without caring what the specific content means. A meta-rule reading "X causes Y" does not conclude Y;
it mints a plan step describing "do X, expect Y." A meta-rule reading "orders over 500k must ship early"
does not conclude that the order must ship early; it mints a `requires` fact, and a second, equally generic
meta-rule matches `requires` facts against separately-authored `satisfies` facts to arrive at an actual
action. This is not a novel invention — it is precisely what `test_a_rule_writes_a_whole_rule_with_nothing_
authored_in_python` already proved was possible (a rule reading a description and minting another
description), aimed correctly for the first time at business content rather than at the engine's own rule
representation.

This same conflation, once named, turned out to have already been found and resolved once before, in the
old engine, without the connection ever being made explicit. `causation-core-was-sugar` records that the
entire causation core, when actually built, resolved as a generic propagation schema plus one declared
fact, never a new primitive — the empirical confirmation of exactly the distinction just described, made
three weeks before this session and never reconciled with `closed_class_inventory.md`'s own table, which
still lists causation as closed-class content awaiting formalization.

## 6. Rechallenging the closed class

Pulling on this thread further raised an uncomfortable, genuinely open question: if causation was
miscategorized this way, what else was? Conditional had already been flagged, in this project's own prior
work, as "the first form whose real home is a unit rather than a field... a relation between two
occurrences" — different in kind from a claim decoration like negation or degree, though the difference had
not yet been drawn all the way out. Quantification's hardest case had already been resolved via goal
machinery rather than a new primitive. Force had already been described as "intake routes, not form" —
never claimed to generate content directly. Once these were laid side by side, a sharper dividing line
emerged: not the CONTENT-versus-FORCE-versus-LEVEL axes this project had been using, but single-claim
modifiers (negation, degree — properties any claim can carry, true regardless of domain) versus
multi-occurrence relations (conditional's relational core, causation, quantification's open case, force and
level's routing, procedures, plans, business norms). Every relational form checked so far, without
exception, has resolved to open content read by a meta-rule.

Two external comparisons, requested directly rather than assumed, turned out to converge on the same
answer from different directions. Linguistic closed-class inventories — the roughly forty to sixty
grammaticalized categories catalogued across the world's languages, including causation, which reliably
grammaticalizes as dedicated causative morphology — answer a different question than the one this project
actually cares about. They enumerate which functions a language gives a *dedicated surface marker*, which
is a property of the parsing layer, not of what the engine executes once something is recognized. Datalog's
several decades of practice gave the sharper, formal check: its entire closed algebra is conjunction,
stratified negation-as-failure, and recursion to a fixpoint. A causal predicate is an ordinary predicate in
Datalog; propagation is an ordinary recursive rule, never a new construct — precisely mirroring this
project's own finding, arrived at independently. Gradedness is the one place worth extending past vanilla
Datalog, and there is real, established precedent for doing exactly that as an algebraic annotation — a
semiring, in the formal literature on provenance and possibilistic logic programming — rather than as a
new logical primitive, which is exactly what this engine's finite band scale with a min-join already is.

The resulting, tentative closed algebra is small: conjunctive matching, theta-gated negation-as-failure, a
meet-semilattice for gradedness, and the five raw substrate effects. Everything else — force, level,
conditional's relational core, quantification's open case, causation, procedures, plans, business norms —
is open content, read by meta-rules that are themselves ordinary rules over this same small algebra, never
executed as if the algebra understood the content directly. It matters to be honest about which parts of
this are actually confirmed and which are a strong, unproven pattern: causation and quantification's open
case are empirically checked; force, level, and identity (which has no analog at all in Datalog, and which
this project's own "identity is decided, not interned" stance already suggests belongs in the open pile) are
structurally implied but not yet probed the way causation was. The old engine's own stated lesson about this
exact situation applies without modification — expect a surface slice, not engine work, and probe first,
every time, rather than betting the inventory on a pattern alone.

## 7. Composing the open middle tier, without needing to prove it sound

A further refinement, raised directly, distinguished a third tier from the closed algebra and the
essentially infinite open class of ordinary business content (the web of belief Quine's confirmation
holism already commits this project to treating as a whole, never definable piece by piece). Between them
sits a middle tier of open "meta-concepts" — goals, procedures, questions, standing prohibitions — each
manipulated by its own meta-rules, and the real worry was not whether any one of them, in isolation, is
well-formed, but whether they can genuinely *combine*, the way an agent (as opposed to a scripted chatbot)
needs them to: a procedure whose steps require answering a question, a question about a procedure, an
action blocked by a standing rule about what never to do.

The telecom feature-interaction literature (Zave, already cited elsewhere in this project's own design
work for an unrelated reason) turned out to be exactly the right precedent, and instructively so, because
of how that field's own thinking evolved. Its earliest approach tried to prove, once and for all, that no
combination of independently-designed features could interact badly — tractable only because, like this
project's closed class, the feature vocabulary was small and fixed. As the feature set grew without bound,
the field moved toward detecting interactions at runtime and arbitrating them, rather than trying to
re-verify an ever-growing system from scratch. That shift is exactly right for this project's open middle
tier, which is unbounded and growing by design, and the good news is that the runtime mechanism it needs
is not something to build — it already exists. Two rules concluding incompatible things about the same
fact are already caught, mid-revive, by the engine's own conflict-detection machinery, surfaced as an
ordinary fact on a wire rather than one conclusion silently overwriting the other; this is the same
mechanism that already keeps a mutating rule from acting on the world from inside a supposition. What is
still missing, honestly, is a declared convention for *arbitration* — "this norm overrides that one," as
its own piece of data, the same way every other stance fact in this arc has been authored — without which a
detected conflict stays honestly unresolved rather than silently decided. And it is worth being precise that
this resolution, per the engine's own documented design, spans at least two revives — detect and report this
turn, retract next — consistent with every other "accept the lag, make it explicit" finding already reached
in this session.

## 8. The meta-concept unification, checked rather than assumed

The sharpest form of the composition question, finally, was whether goal, procedure, question, and
prohibition are four architectures that happen to resemble each other, or one representational shape
wearing different surfaces. Working through it directly, each of the apparent differences dissolved. A
procedure is a goal decomposition — exactly `goal_decomposition_experiment.py`'s already-built shape —
with one additional sequencing edge among the children. A question is a goal whose wanted condition is a
knowledge-claim rather than a world-state claim, resolved by the same `achieved`/`diverged` discipline
either way. A procedure whose step requires answering a question is nothing more than recursion — a step
that is itself a nested goal, satisfied once that nested goal resolves. A question about a procedure is an
ordinary read of another goal's own plan data, not execution of anything. A standing trigger needs no new
mechanism at all, because a wired `StandingUnit` already is the engine's own notion of a standing trigger. A
prohibition is the same stance-fact pattern already built for closed-world defaults, generalized: a
declared `forbidden` fact, consulted as an ordinary negative premise by whichever rule would otherwise act,
tied to the specific candidate it concerns through an ordinary bound variable rather than a hardcoded name.

This was not left as an argument. A single worked example combined all of it in one scenario — a
"procedure" goal decomposing, one-shot, into two ordered steps, the first a question (resolved externally,
exactly like any goal's outcome), the second an action gated both on the question's own `achieved` and on
the absence of a standing prohibition matching the specific agent it names. Run against the real engine,
three things held without needing any adjustment to the underlying mechanism: the procedure decomposed
into two differently-kinded, correctly-sequenced steps with nothing new minted for the purpose; with no
prohibition present, the action step stayed honestly unexecuted until the question genuinely resolved, then
executed, and the procedure's own `achieved` only landed once both steps genuinely had, in order; and with
a standing prohibition present, the question still resolved on its own schedule but the action step never
executed, across many idle turns, and the procedure honestly never reached `achieved` at all. Nothing about
supposition scoping, the commit boundary, closure-before-NAC, the reflective-axiom discipline, or
`AttrVar`-linked negation needed to change to make this work — they composed exactly as designed, in a
scenario built specifically to see whether a seam would appear.

## 9. Three more candidates, and one paradox that turns out not to apply

Before moving on to actually probing anything, three further questions were raised and worked through,
because lumping them in with "more relational forms, presumably open" would have been too quick. The
first was modus ponens itself — surely, if a business conditional's elimination is open content read by a
meta-rule, then modus ponens is too? Working through it slowly showed this is not so. Every `StandingUnit`
in the engine, the moment it matches its pattern and fires its effect, already *is* an instance of modus
ponens — that is simply what matching and firing mean, for any rule at all, and it has nothing to do with
business content. What is genuinely open is a step *adjacent* to modus ponens, not modus ponens itself:
getting from an openly-authored conditional claim, sitting as data with an antecedent and a consequent
connected by a role, to something the substrate can actually execute. That step needs a meta-rule, exactly
like causation did; the substrate's own execution of a rule once compiled needs nothing further at all.
This matters because it draws the line differently than "conditional is relational, therefore open" would
suggest on its own — the relational, open part is the authored *claim*; the execution, once compiled, was
never anything but substrate.

Transitivity turned out to sit unambiguously on the open side, but with a real mechanism behind it rather
than a vague gesture at "some meta-rule or other." The old engine had already built this, in a different
context, and found something specific: transitivity did not need one hand-written rule per transitive
relation. It needed one rule, written once, quantifying over the relation itself as a variable — for any
relation `r`, if `x` relates to `y` and `y` relates to `z` under `r`, conclude that `x` relates to `z` under
`r` — and this worked "on demand," supplying whichever relation a query actually asked about. Left
unguarded, though, this schema is simply wrong for the many relations that are not transitive; a person's
mother's mother is not their mother. The honest version needs a declared fact, per relation, saying that
relation is transitive — the same discipline this whole arc keeps reaching for: declare the exception as
data, never bake the exception into which content the engine happens to treat specially. Whether this
predicate-variable mechanism exists, or is even needed, in the current engine was not checked, and belongs
on the same list as force and level rather than being assumed to transfer.

The third question was sharper and more uncomfortable: does authoring an explicit definition — "call this
combination of conditions X," the substitution mechanism already built earlier this session — run into
the classical philosophical problem with defining concepts at all? Jerry Fodor's argument, cited already
elsewhere in this project's own design work, is that trying to explain most ordinary concepts through
definitions fails empirically — nobody has ever produced a definition of an everyday word that survives
counterexamples — and his own alternative is that most concepts are primitive, their content fixed by
nothing more than a causal connection to whatever they denote in the world, with no internal structure to
decompose. Working through this carefully rather than dismissing it, the answer is that this project never
attempted the thing Fodor showed does not work. Ordinary open-class words in this system are never given
explicit definitions at all — they are handled holistically, absorbed by an embedding model, exactly the
practical shape of Fodor's own alternative, and exactly what this project's existing distinction between
baroque and fundamental content already commits to: content that can be paraphrased without changing what
the system believes does not need decomposing, an LLM already carries it. The explicit `define` mechanism
was only ever meant for a narrower, different case — a domain or a user *stipulating* an equivalence, the
one place definition genuinely does work without controversy, the way a legal or mathematical term is
often definitionally fixed by convention rather than discovered by philosophical analysis. Fodor's paradox
is a warning against a project this one never signed up for.

Checking whether these compose safely turned out to be the same runtime-detection answer already reached
for the open middle tier generally, sharpened by one thing genuinely specific to this group: transitivity
and definitional substitution are both recursive, in a way force-routing or a one-shot causal-to-plan
translation are not. Transitivity composed with itself keeps deriving longer chains; a defined equivalence
combined with a transitive relation or an ordinary business rule could, in principle, keep unfolding
indefinitely. This is not a new category of risk — it is exactly the termination and honesty work already
done for cycles in general, the fix that stopped a truncated derivation from being silently read as a
complete one, simply not yet connected to these particular schemas. One risk really is specific to
definition, though, and worth stating precisely rather than folding into the general recursion worry:
because additive rewriting deliberately keeps both the old and the new form of a rewritten fact alive
side by side, a rule reacting to one form and a different rule reacting to the other could produce two
representations of what is, underneath, the same conclusion — and unless the engine's conflict-detection
is checked directly against this specific case, there is a real possibility it would read two equivalent
conclusions as a disagreement rather than an agreement. That is a concrete thing to build and check, not
something safe to assume from the general argument alone.

## 10. Force, probed rather than assumed

The pattern predicted force would resolve the same way causation did, and it was worth resisting the
temptation to simply believe the pattern. `units/force_probe_experiment.py` built the smallest version of
the actual claim: given an utterance already tagged with its force — recognizing that tag is parsing's job,
genuinely out of scope here, exactly as `force-is-the-missing-axis` already argued — does routing "ask" and
"command" toward the goal machinery need anything beyond a trivial meta-rule minting a goal wanting the
utterance's content? Two routing rules were written, one per force, deliberately almost identical to each
other, because if ask and command genuinely needed different machinery to route, the two rules would have
had to look different, and they don't — they differ only in which literal force value they match. Both mint
a goal, both mark their utterance consumed in the same firing so neither can double-fire on a later idle
turn, exactly the discipline already established for sticky transitions earlier in this arc.

The more interesting confirmation came from what happened next. The two resulting goals — one born from a
question, one from a command — were handed to the ordinary, unmodified `achieved`/`diverged` rules already
built for goals with no relationship to force at all, and both resolved correctly: the question's goal
reached `achieved` once its content was confirmed, the command's goal reached `diverged` once the
world-state it wanted failed to materialize. Neither achieved/diverged rule reads which force produced its
goal, and none needed to. This is the sharpest form of the claim this whole arc has been building toward:
by the time a goal exists, its originating force has already done its one and only job — deciding that a
goal should exist — and has nothing further to contribute. Force earns its place in the confirmed column
alongside causation, not merely the hypothesized one.

## 11. Level, checked the same way, and made to earn a real distinction rather than a cosmetic one

Level asks something different from force — not how a claim was delivered, but what the claim is even
about: the world, or the system's own reasoning about the world. It would have been easy to build a probe
that only repeated force's shape with different labels, which would have proven nothing beyond "labels can
differ." `units/level_probe_experiment.py` was built to avoid that trap deliberately: a `world` utterance
asks whether a customer is a VIP, an ordinary claim answered by external input, exactly like anything in
the force probe. A `theory` utterance asks something categorically different — whether the engine's own
`vip_rule` has *already concluded* that the customer is a VIP — a claim about the system's own reasoning,
not about the customer directly.

Routing both utterances to a goal needed nothing beyond the identical meta-rule shape already confirmed for
force. What made the check meaningful was showing the theory goal's content is genuinely satisfied by a
different *kind* of thing, using no new machinery to do it: an ordinary rule reacts to `vip_rule`'s own
conclusion exactly the way any rule reacts to any fact, because a rule's output is already ordinary graph
data and provenance was already established, several sections back in this same arc, as free. Checked
directly, the theory goal stayed honestly unresolved through a turn where only the world question got its
external answer — proving the "about the system" reading is real rather than a label with no behavioral
consequence — and resolved only once `vip_rule` itself actually fired. Both goals, once minted, were
resolved by the exact same two rules, with no level-specific branch anywhere. That is four relational forms
now checked in a row — causation, quantification's open case, force, and level — with the pattern holding
every single time.

## 12. Where this leaves things

The concrete claim standing at the end of this arc is that this engine's genuinely closed, executable
core is small — conjunctive matching, theta-gated negation-as-failure, gradedness as a meet-semilattice,
and five raw substrate effects, with modus ponens properly understood as part of that same substrate rather
than a meta-rule in its own right — and that everything else this project has been building toward an agent
needing, including goals, procedures, questions, prohibitions, causal reasoning, transitivity, definitional
substitution, and business policy, is open content read by a comparatively small number of generic
meta-rules, all sharing one representational shape. Causation, quantification's open case, force, level, and
the goal/procedure/question/prohibition unification are now checked, not merely argued. What remains
genuinely unconfirmed is identity/merge and whether transitivity's predicate-variable mechanism exists or is
needed in this engine at all — each named rather than assumed, each waiting on the same kind of small,
concrete worked example that resolved everything checked so far, rather than on the pattern alone.
