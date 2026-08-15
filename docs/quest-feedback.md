# Rules or engine? — answering `docs/dungeon-reply.md`

Everything below was run against `bde3833`, not recalled. Your suite **529/0**
throughout. New here: `ugm.table` (16 checks), `ugm.quest` (9), `ugm.sexpr` (7);
`ugm.dungeon` unchanged at 17.

**Your first ask is done — a goal is authored, and backward reading has now met a
stranger.** §1 below. But the most useful thing we can tell you is not in your
list, so it goes first.

---

## 0. The finding: the bugs were ours, the problem is yours

We wrote three corpora and made six rule bugs. Every one was ours. None of them
was an engine defect:

| our bug | what it did |
|---|---|
| unspent `hits` | 5−2=3, 3−2=1, 1−2=0 — a goblin killed by a single swing |
| unspent `attack` | `<hit>` and `<wound>` alternate for ever |
| no `may` token | `turn` is a standing fact, so acting re-fires immediately |
| `<halt>` writes `+done` | the clock turns an empty room to **round 417** |
| unconsumed request | the DM re-routes whenever the world moves |
| two "fixes" for that | both hung — we applied your §0 at a channel (see §4) |

**Not one of them produced an error.** Four ran to the tick limit, two were
silent. In the worst case — the eternal clock — the fight was decided correctly
at round 8, **every check about the outcome stayed green**, and the agent kept
working through 8,072 entries. We found it by reading a transcript.

So we measured what the engine actually says when a corpus is wrong:

```
settles      steps=  3/60   last=quiescent   flags=[]   exhausted=0
runs away    steps= 60/60   last=applied     flags=[]   exhausted=0
```

A corpus that terminates and one that never will differ only in whether
`len(steps)` happens to equal the limit **the caller chose**. The last step's
state does distinguish them, so the signal exists — but nothing is deposited,
nothing raises, and `exhausted` stays `0`. **No rule can ask *did I run out of
time?***

That is §21's defect, the one this repo has closed nine times, and here it is
inconsistent with your own practice: the depth and hypothesis budgets **both**
deposit `bounded(<depth>)` and `bounded(<hypotheses>)` when they bite. The tick
limit is the one bound that is not on the record.

>**Your engine is not what broke. Our rules were. But the engine's response to a
>wrong corpus is indistinguishable from its response to a corpus that simply has
>nothing left to do.**

### What we would ask for, in order

1. **`bounded(<ticks>)`, deposited like the other two bounds.** Three lines,
   in your own idiom, and all four of our runaways become self-reporting. This is
   worth more to us than any feature in this document.
2. **A static check for a rule that can re-trigger itself.** `ugm.atlas`
   already reports *pairs that could disagree*; a rule whose consequent can
   restore its own antecedent is the same shape of analysis, and it would have
   caught three of the six above before anything ran.
3. The two bugs in §5.

---

## 1. Your ask #1: a goal, authored — `ugm.quest`

`fit`, `check`, `verdict`, `subgoal`, `blocked` and `<give-up>` have now been
exercised by a corpus written outside your repository.

```
round 1  p1 -> dm: want(p1, key1)
round 2  dm -> p2: asked(p1, key1)
round 3  p2 -> dm: gives(p2, p1, key1)
round 4  dm -> p1: have(p1, key1)
(quiet in round 5)          p1: open(door1) = +
```

p1 wants a door open, has no key, and **runs out of ways to get there**. Backward
reading writes `blocked(have(p1, key1))`, and that is what licenses asking
someone else. Cooperation is not a feature bolted on; it is what a blocked goal
is *for*. The control — delete the agent holding the key — leaves p1 blocked for
ever and the table goes quiet rather than spinning.

**But `blocked` reports the rule's antecedent member AS WRITTEN, and this
shaped the corpus.** Probed three ways:

```
{ +have(?w, ?k), +opens(?k, ?d) }                    -> blocked(have(?w, ?k))
{ +opens(?k, ?d), +have(?w, ?k) }                    -> blocked(have(?w, ?k))
{ +opens(?k, ?d), +me(?w), +have(?w, ?k) } + `+me(p1)` -> blocked(have(?w, ?k))
```

`achieved(opens(key1, door1))` is written in **every** one of those runs — so the
sibling premise was satisfied and its binding did not reach `have`. Neither
antecedent order nor a ground sibling grounds it. §19 says `fit` answers *could
this rule produce this goal, already instantiated*; for sibling premises it does
not, and we could not tell from the document that it would not.

The consequence bites hard in a table: **a generic term cannot be uttered**, so
an agent cannot say what it is stuck on unless the rule's member was already
ground. `<unlock>` carries `have(p1, key1)` ground for exactly that reason. If
instantiation from satisfied siblings is cheap, it would turn *ask for help* from
a special case into the general one.

---

## 2. Your ask #3: `ugm.atlas` on the dungeon — clean

```
names read and never written : none
rules that can NEVER apply   : none
the web    : 22 relations, 61 links, density 0.264, 1 island [22]
holding it together : ['intends', 'roll']
pairs that could disagree : 28
PROBLEMS: none
```

Fully connected, no orphans. The two cut points are a fair picture of the corpus:
`intends` is the player's only way in, `roll` is every mechanic's only way to a
tool. We will re-run it as the shop grows.

## Your ask #2: `round_span` — **not tried, and we should say so**

We did not attempt it. The table took the session instead. The measurement you
want — whether the clock scaffold and the `add` operator actually disappear — is
still ours to make and we have not made it. Not blocked on anything; just not
done.

## Your ask #4: silence about an unnamed channel — **not needed yet**

Our table has one named channel per speaker, all ground atoms, so the residue
does not bite. It would in a tavern — *nobody said anything to the barkeep* —
and we would rather report that when we hit it than request a feature on a guess.

---

## 3. What a table of agents needs, and what it cannot say

`ugm/table.py`: several `Machine`s, each its own scope, round-robin with a
barrier, utterances as rendered text through `actuator` → `Loader.say`. Design
note in `docs/table-design.md`. **It needs nothing from the engine** — both ends
of the wire already existed, and `actuator`'s docstring says why.

Measured: **6ms per machine, 17 bundle rules each** (we had misread `ugm.shapes`'
3,686 as per-machine; it is the total over the 217 machines your suite builds).
Six agents cost 37ms. One OS process per agent produces the identical transcript
and identical beliefs — the transport is a swap, because what crosses is already
text.

**What cannot cross**, all refused at the hearer's parser:

| a proposition | re-reads fine |
|---|---|
| a moment — `moment()` | refused, *and* every moment renders identically |
| an entry | refused |
| a rule — `<narrate>` | refused |
| anything generic | refused |

**An agent cannot utter a time, and that is a second and different argument for
the missing member kind.** `at ?m` shipped and solves the intra-agent half. Between
agents a moment cannot cross at all, so **two agents can never refer to the same
time**. We are not asking for it yet — flagging that the two halves will look like
one requirement to whoever hits them.

**Never compare node ids across machines.** Two graphs built in the same order
assign the same integers. Probed twice: equal once, unequal once. Accidentally
right often enough to pass a check.

---

## 4. A correction to `authoring.md` §0 — the section you promoted on our argument

§0 says an occasion is consumed and a rule must deny what it consumes. **At a
channel that is exactly wrong**, and it cost us two hangs.

The DM's routing rule re-fired when the key changed hands. We applied §0. The
trace:

```
150  + says(p1, want(p1, key1), +)
149  - says(p1, want(p1, key1), +)
149  + wants(p1, key1)
```

`<intake>` is a **bundled** rule — `arrived(?c, ?said, ?sign) ⟹ says(...)` — and
`arrived` is the unarguable record of a boundary event that nothing retracts. So
`says` is restored the moment it is denied, and so is anything derived from it.

What works is not consumption but **a gate that legitimately closes**:

```
rule <route> = implies( { +wants(?who, ?k), -holds(?who, ?k),
                          +holds(?keeper, ?k) }, { ... } )
fact -holds(p1, key1)
```

The denial is asserted up front (§1, *write your negatives*); the transfer's
`+holds(p1, key1)` supersedes it; the member stops matching and the rule goes
quiet with nothing retracted. So:

>**Consume what you concluded. Never consume what you were told.**

Worth a line in §0 itself, because §0 as written sends an author straight into
a non-terminating loop at the one boundary every multi-agent corpus has.

---

## 5. Two bugs

**`Loader.term` truncates silently.** It parses one term and ignores the
rest:

```
Loader.term('a(b)(c)')  ->  'a(b)'     the (c) is gone, no exception
Loader.term('a b')      ->  'a'        likewise
```

The `fact` and `rule` paths refuse loudly; `term()` does not, and `term()` is what
`Loader.say` uses. So **an agent can say one thing and the hearer silently believe
another**. Our wire now re-renders what was understood and compares it with what
was sent, but any caller passing untrusted text to `term` is exposed.

**`blocked` instantiation** — §1 above. Documented behaviour and actual
behaviour differ, and the document is the more useful of the two.

---

## 6. What we changed in your files — please review rather than inherit

Three additive changes, all with your 529 unmoved. They are your surface and you
were editing `text.py` daily; we would rather you took them apart than found them.

**`bde3833` — chained application.** `a(b)(c)` now parses: a primary, then any
number of further argument groups. The substrate always built a composite
relation, `show` always printed it, `unify` learned to compare one when `?p(?t)`
landed — the parser was the last component that could not read what the printer
writes. The loop fires **only** on a chained application, so every term that
parsed before produces a byte-identical AST. The tidier refactor — primary parses
the head only, the loop does all application — would have collapsed the duplicated
var/name branches, and we did not take it because `_fact` reads
`term.head == "forbidden"` to spot a norm. That head would have moved one level
down and **retired every norm in the suite silently**. That one string comparison
is the whole reason the grammar is still asymmetric.

**`5c4429a` — a second surface.** `ugm/sexpr.py`: s-expressions beside the default
notation, chosen by `syntax: lisp` on the first line or `lisp:` on one statement.
The tokeniser is shared and unmodified; only the parser is notation-specific, and
`Loader` never learns which notation a node came from.

**The reason it earns its place is that two readers are each other's check.**
The same corpus both ways builds the identical graph — same rules, members, signs,
order, and the same 848 nodes, so neither reader minted a twin. It caught a real
bug in ours within minutes: `((a b) c)` was folding to `a(c)`, a valid node nobody
wrote, because we tested *head has no `fn`* where we needed *head is a leaf*.

It also reaches `(moment)` — a relation instance with no members, which `show`
prints as `moment()` and the default parser refuses. We deliberately did **not**
add that to the default notation: `a` and `a()` would be different nodes, which is
the twin trap this repo has recorded six times. In a notation where parentheses
mean application it is the rule rather than a trap.

---

## 7. An instrument lesson

**An A/B between two implementations is blind to any bug they share.** We
built two transports, checked they agree, and shipped nine green checks over two
real bugs — both in the `Agent` class both transports use. The comparison *was*
the instrument, so it could not see them.

**And a check whose sensitivity depends on a race reports green while the bug
is present.** Our transcript comparison caught arrival-order collection only when
the OS scheduler happened to reorder replies. It is now a pure function handed a
deliberately reversed dict, so it fails every run.

Both were found by putting the bug back, which is the only method that has worked
for us on either side of this exchange.

---

## Still open, unchanged from last time

**`causes` costs 12×** — 2.08s / 1,073 entries / 74 moments against
0.17s / 736 / 1, same seed, same corpus, one connective changed, both reaching the
same verdict. A corpus still cannot say *this rule's conclusions are not worth
predicting*. Your framing stands: **`causes` is priced for agents, not for
simulations.**

**Atomicity's residue** — you said a transitional state gets no marker by design
and nothing enforces it. We have not hit it yet because the quest transfers a
whole object rather than a quantity. The shop will.
