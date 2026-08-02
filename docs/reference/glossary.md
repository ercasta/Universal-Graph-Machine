# Reference: glossary

One sentence per term, in alphabetical order.

**activation** — the interpreter's own state as graph data: program counter, call stack, registers
and focus, so a running program can be stopped and asked what it was doing.

**agenda** — the ordered list of steppable tasks the outer loop rotates through, one primitive step
at a time.

**application** — a node recording that a function was applied to particular arguments in a
particular episode.

**assumption** — the choice of one mock outcome over another, recorded as a hypothesis so a plan can
say which of its steps are guesses.

**candidate** — a function whose declared parameter type a node satisfies, so it *could* be applied
to it.

**cast** — applying a function declared to return a stronger type; since a type is a shape, nothing
records that a mutation happened.

**consequent** — the tagged right-hand side shared by the authored families that have one: either a
subgoal to achieve or a call to make.

**constraint** — one thing a goal requires: a link between individuals, an attribute value, a type,
or that something be known.

**criterion** — authored expert judgement that names the action to take in a recognised situation;
falls silent when it cannot act.

**deviation** — a real result failing the cast its step promised, or failing a derived expectation.

**directive** — a criterion with mandatory force: it does not defer to alternatives, and refuses when
it cannot act.

**dispatch** — the single door through which an effect leaves the graph, and the checkpoint that
guards it.

**episode** — an ordered record of applications; compiling one produces a reusable function.

**expectation** — a qualitative prediction derived from the two frames a workbench already holds,
never authored and never stored.

**focus** — a set of named heads pointing into the graph; the mechanism that decides what a rule acts
on.

**frame** — one imagined state on a workbench; steps extend a path of frames and assumptions fork it.

**goal** — a node holding the constraints that must hold, the prohibitions on the route, and the
subgoals raised under it.

**guideline** — authored preference that reorders what is tried and can never exclude anything.

**head** — one named pointer into the graph, movable forward, backward, or through a reference.

**hypothesis** — an ordinary node under which a rival version of something is built, with a verdict
that persists as a fact.

**interference** — two independently authored functions writing the same slot for *different* goals;
the same two writes serving one goal are a deliberate sequel.

**kernel** — the part Python may implement: substrate and scheduling, never anything decided about
how something is represented.

**liveness constraint** — a requirement that a plan *include* something; it is checked only at the
end and must never prune.

**mapping** — a node tying a workbench image to its original, which is what makes an imagined plan
replayable against the real world.

**method** — an authored decomposition of a goal into ordered subgoals; falls back to search when it
does not fit.

**mock** — a rule whose return type is the outcome it assumes about a real call, so each possible
outcome can be planned differently.

**moment** — a time node that points at what it dates; one action produces one moment shared by
everything it observed or produced.

**native** — a primitive the kernel executes by name through a table it does not populate.

**norm** — a prohibition or permission attributed to a source, arbitrated against others by a
declared authority ordering.

**pending call** — an unexecuted call in a lazy chain; planning composes them and nothing runs until
something asks it to.

**procedure** — a method with mandatory force: when it does not fit, it refuses rather than falling
back to search.

**pursuit** — the loop of planning by imagining, acting for real, checking, and replanning.

**reference** — a stored pointer held as an attribute value; distinct from an edge, which is a claim
that two nodes are related.

**relevance** — a structural score for a proposal, read off the stored body of the function it would
call; it only ever orders.

**replay** — running a plan's frames against the real world, one action at a time.

**safety constraint** — a prohibition or budget whose breach proves every extension of a branch is
dead, so it prunes before the step is imagined.

**sighting** — an observation of a slot recorded at the dispatch boundary, with the moment it was
taken.

**stance** — a per-question choice about whether to close the world, never a property of the
machinery.

**thread** — materialised short-term memory: attention shifts and applications in order, each
carrying why it followed the last.

**type** — a schema over a subgraph, declared as graph data, satisfied by looking at a node rather
than by consulting a tag.

**unmet** — the constraints of a goal that are still false; what turns search from generate-and-test
into means–ends.

**volatility** — how often a slot has been observed to change, and how much of that change was not
the agent's doing.

**witness** — a particular individual that satisfies an existential constraint.

**workbench** — a private copy of everything reachable from a subject, on which steps are imagined
without touching the world.
