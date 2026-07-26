# Open question: should rules be attached to nodes?

**Status: open design question, raised 2026-07-26. Nothing built.** This records a proposal that is
probably more faithful to the vision than what `units/` currently does, together with what it would have
to replace and the problems it has to solve first. It is written down rather than acted on because it is
a re-architecture, and because the thing it would replace now works and is pinned by tests.

---

## 1. The proposal

> Physically connect the rule to the node — a graph in which rules are appended to the nodes they apply
> to. When run, they **dissolve** and materialise their result at that position in the graph.

So a rule is not retrieved, instantiated in a context and fed a value. It is **grafted onto the data at
the point where it applies**, fires there, and is consumed; its conclusion appears where it was grafted.

## 2. Why it is more faithful

`model.md` §1 says computation is *"scaffolding built over the data, used, and thrown away."* Attachment
is that sentence taken literally: the scaffolding is physically on the data, and dissolution *is* the
throwing away. `0005` — *the index indexes computation, never data* — survives as exactly this structure.

The stronger argument is that it **collapses three mechanisms into one**. Everything in the left column
exists in `units/` today, separately:

| today | under attachment |
|---|---|
| a scope-less rule is **instantiated once per active context** (`loop.step`) | the rule is *at* a position; there is nothing to instantiate |
| each instance is fed a **projection** of what is visible there (`graph.visible_at`) | its reach is its neighbourhood in the graph |
| the assembler threads a **`ScopePointer`** so conclusions land in the right containment (`unit.ScopePointer`) | the result materialises where the rule was grafted |
| a **cooldown table** suppresses re-derivation (`units/cooldown.py`) | dissolution — a spent rule is *gone* until re-attached |

The last row is the one that should be taken seriously. The cooldown is a side table with an arbitrary
size, and it carries a declared breach: *"scheduling policy leaks into semantics"*, because the cache
size changes what the system concludes. Under attachment, *"this rule already fired here"* is not a cache
entry at all — it is the absence of an attachment. And the refinement that a **change to a node cancels
the cooldown** becomes a *reason to re-attach* rather than a cache invalidation, which is a better shape
for the same idea.

Three mechanisms collapsing into one is usually the design saying something.

## 3. What it has to solve first

**Multi-premise anchoring — the crux.** *"If x is a bird and x is not a penguin, x can fly"* attaches to
*which* node? Two candidate answers, both with costs:

- **an anchor premise**, with the others resolved in the neighbourhood — but then the anchor choice is
  load-bearing and probably has to be authored, per rule. If so, the simplicity gain is smaller than it
  looks, and the CNL grows a concept.
- **all of its premises**, firing when they are co-present — closer to the token-passing/chart-parsing
  intuition that [[homoiconic-grammar-spike]] proved out, but it multiplies attachments and needs a
  co-presence test that is itself a small join.

**Defining *neighbourhood* without smuggling the projection back in.** A rule attached to a node must
reach its other premises somehow. The promising answer is that reach = the containing scope's subgraph,
found by walking up from the attachment point — position *is* scope, which is the whole appeal. But if
that walk ends up computing the same thing `visible_at` computes, the mechanism has been renamed rather
than removed.

**Dissolution versus reuse.** A rule is a general truth and applies in many places, so what dissolves is
a *copy* at one position, not the rule. That means attachment is per-(rule, position), which is what the
current cooldown key already is — evidence the two really are the same mechanism, and a reason to expect
the same combinatorics rather than fewer.

**Retrieval becomes attachment.** System 1's job stops being *"which rules come to mind"* and becomes
*"where do I graft what"*. That is a strictly larger question — it has to pick positions, not just rules
— and `model.md` §13 already lists the retrieval mechanism as undecided. This proposal makes that
question harder before it makes it easier.

**Ordering and termination.** Attachment creates structure that then fires and disappears. What stops a
rule re-attaching to its own conclusion forever is currently the outer budget plus the cooldown; under
attachment it would have to be the attachment policy, which is the same policy-into-semantics leak in a
new place unless it is designed out.

## 4. The acceptance harness

Any replacement has to reproduce these, all of which are currently green:

| behaviour | test |
|---|---|
| the same rule fires inside and outside a hypothesis, and no rule pattern names a scope | `test_tunnel.py` |
| two sibling hypotheses in one circuit do not contaminate each other | `test_tunnel.py` |
| a conclusion cannot leave a tunnel unless something attached to the end marker | `test_tunnel.py` |
| a general rule chains onto a conclusion made under an assumption — *"assuming x has wings, x is a bird"* then *"if x is a bird, x can fly"* | `test_scoped_writeback.py` |
| …and that chained conclusion stays **inside** the assumption | `test_scoped_writeback.py` |
| the base world cannot see into an assumption, but can see that it exists | `test_scoped_writeback.py` |
| conclusions do not accrete without bound across steps | `test_cooldown.py` |
| a change to a node makes the rule applicable again | `test_cooldown.py` |

That list is the real value of having built the current version: it is the specification the alternative
must meet, expressed as behaviour rather than as prose.

## 5. Recommendation

**Do not retrofit.** Spike attachment separately against the harness in §4. If it reproduces all eight
with less machinery, it wins on evidence rather than on intuition — and if it does, deleting
`visible_at`, the per-context instantiation, `ScopePointer` and `cooldown.py` in one move is a large
simplification.

**Resolve multi-premise anchoring first**, on paper, before writing any code. It is the only one of the
five problems that could make the proposal *worse* than what it replaces, and it is cheap to think
through and expensive to discover.
