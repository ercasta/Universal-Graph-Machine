# Aspects — concerns that are woven, not written

> **The concern, stated 2026-08-02.** Some concerns should be automatically **woven** into the procedures,
> the way transaction management is. Timestamping, for example: *"I don't expect each business rule to
> handle it manually. And it's not that each node gets a different timestamp — when listing files in a
> folder, the entire list of files should get the same timestamp, because it corresponds to a single
> action."*

This note records what is **measured** to be true today, because two of the three things it implies were
already the design and the third turned out to point the other way.

---

## 1. Time: woven, at the granularity of the action ✅

Measured in `docs/microfunctions/probe_woven_time.py`, on the exact example.

| claim | verdict |
|---|---|
| a business rule must not call the clock | ✅ already true — `dispatch.service` records the sighting |
| one action produces **one** moment, shared | ✅ already true — `record_sighting` passes one `when` for a whole look, and `clock.py` was built for that cardinality |
| …covering **what the action produced** | ⚠ **was false, now fixed** |

**The gap was scope, not mechanism.** A look at a folder recorded three sightings sharing one moment —
and the three file nodes it minted had **no moment at all**. Listing a folder left *the file list* — the
whole point of listing a folder — with no time on it. `dispatch.service` now mints the moment once and
gives it to both the sightings and the products. Pinned by
`check_ONE_ACTION_IS_ONE_MOMENT_including_what_the_action_PRODUCED`, whose guard is set **equality** of the
two moment sets rather than mere presence: a product with its *own* moment would be a second action.

⚠⚠ **DATING IS NOT ENCODING, and keeping them apart is what made this safe.** `record_sighting`
deliberately encodes only the slots of *the thing being looked at* — *"everything else the tool happened
to touch is the walk to school, not encoded, and that is the correct outcome rather than a loss."* That is
about **attention** and is untouched: the products are **dated and not observed**. Widening the encoding
instead would have overturned a decision made on purpose.

## 2. ⭐⭐ The obvious generalisation is WRONG, and the measurement says so

The natural next step is *"then date everything that gets minted."* Measured: a node minted by an ISA body
(`NEW R(n) "chunk"`) carries **no moment** — and it should not.

```
world arrival   (dispatch)   -> TEMPORAL provenance:  a moment dates it
internal mint   (ISA body)   -> CAUSAL   provenance:  activation.minted names what made it
```

Both already work. They are **different answers to different questions**, at different join points, and
`clock.py`'s rule is precisely *"everything observed **or acted**"* — a derived node is neither.

> ⭐ **And stamping every mint would produce exactly the per-node timestamping the concern rejects.** A
> moment per `NEW` is *"each node gets a different timestamp"*, which is the thing being argued against.
> The concern's own principle rules out its most obvious implementation.

## 3. Transaction management: a second aspect, and it weaves differently

It is genuinely already woven, at **four hand-placed sites**:

| site | boundary |
|---|---|
| `isa.Machine.run` | one program — a failed run rewinds in O(changes) |
| `intake.read` | one authored block — *"a refusal leaves nothing behind"* |
| `intake` (block seal) | the same, at the second entry point |
| `dispatch.service` | `g.commit()` — the point after which nothing is undoable |

⚠ So there are **two aspects and at least five weaving sites**, every one of them written by hand at the
place it applies. That is the "second caller" the standing rule cares about, and it is why this note
exists rather than a `weave()` function.

## 4. ⚠ What is NOT being built, and what would decide it

**No general aspect mechanism, yet.** The two aspects weave at **different join points** — an *action*
crossing the world boundary versus a *program or block* beginning and ending — and they are not variations
of one thing. A generic mechanism would have to invent a join-point vocabulary, which is a real design and
not a refactor. `islands.md` §3(f) is the argument for waiting: *the second use is free only if the first
was reachable*, and neither of these is reachable as a concern today — each is a line of code at its site.

**What would settle it, in order:**

1. **A third aspect that wants an existing join point.** Authorisation (*"who may do this?"*) and quota
   both want exactly `dispatch.service`'s boundary, which already has two concerns on it. Three would make
   the case.
2. **A concern that wants a join point nobody has.** *"Every write to a slot a norm governs"* has no site
   at all today, and that is a different problem from weaving — it is a **trigger**, which `north_star.md`
   already separates from microfunctions.
3. ⚠ **The kernel/business split applies here too, and it is the sharp part.** The *weaving* — "run these
   registered concerns at this boundary" — is **scheduling**, so it is kernel. The *aspect* — what a
   moment means, what a transaction is for — is **business**. So the shape, when it comes, is the one
   `native.py` already has: a table the kernel consults at a boundary and does not populate. **What must
   not happen is a kernel that knows what a timestamp is.**

⚠ Today `dispatch.py` is above the line and holds both concerns inline, which is fine for two and would
not be for five.
