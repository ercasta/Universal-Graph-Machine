# Reply to HarneSkills — `microfunctions` engine

Answering `docs/feedback_from_harneskills.md` (collected 2026-08-02). Engine now at **204 checks, 0
FAILED**. Every item below has a self-test check behind it, and where you gave a repro we ran *yours*
rather than a unit test of our own — twice that caught something a unit test had already passed.

⚠ **Your measurement note was right and worth repeating back.** You measured against our working tree
mid-refactor, and §6 cites `_SHAPE_FORMS` at `intake.py:245` — a constant that was *hours old* when you
read it. Nothing in your document was already-fixed work; you landed in the middle of a surface arc, and
two of your asks turned out to be the next step of it.

**Everything here is uncommitted.** Pull when it lands.

---

## §1 — a guideline is silently inert without `rank=` — **FIXED (warning)**

Your repro, verbatim, now:

```
rank= OMITTED -> alpha | 1 guideline(s) declared and none will be consulted: `pursue` was called
                        without `rank=`, so authored `prefer`/`avoid` blocks have no effect here.
                        Pass `rank=guideline.ranker(g)`.
rank= PASSED  -> beta  | (no warning)
```

You diagnosed this exactly right: it was the one place our refusal discipline stopped at the parser.

**A `RuntimeWarning`, not a refusal**, and we took your framing for why — the composition is deliberate and
a caller may legitimately bring its own ranker. What was missing was only that nobody was *told*.

⚠ **One thing to know:** anything passed as `rank=` is taken at its word. If you supply a custom ranker
that does **not** consult guidelines, you will not be warned. We considered inspecting the ranker and
rejected it: a false warning teaches people to ignore warnings, which would cost more than it saves.

The check asserts the warning fires with advice and no ranker, and is **silent** in both other cases.

## §2 — multi-block diagnostic — **FIXED**

```
MULTIBLOCK: line 4: 'type b:' looks like a second block; `read` takes ONE block per call.
                    Split the text on blank lines and call `read` for each.
BADLINE   : line 2: cannot read 'frobnicate the widget' — the type vocabulary is closed (…)
```

Same exception type; only the message differs. A check asserts a genuinely bad line still gets the *other*
message, so the two cannot collapse back together.

## §6 — body-line FORMS as data — **DONE, and it landed on top of the same refactor**

`intake.FORMS` and `intake.forms_for(family)`:

```python
>>> intake.forms_for("goal")
('x l y', 'x l+ y', 'x.k = v', 'x.k known', 'x is a T', 'x is there',
 'some T', 'never f', 'never touch x', 'must f', 'at most n steps')
```

Families: `goal`, `type`, `advice`, `method`, `method step`, `criterion`, `condition`, `question`.

⚠ **Keys are family names as they appear in refusals, not verbs** — `method`/`procedure`,
`criterion`/`directive` and all four goal verbs share a body, which is the whole point of a force pair.
Map from verb to family on your side, or ask us for that mapping and we will export it too.

**Every raise site now renders *from* the table.** The check asserts a form's text appears in a real
refusal, because two copies that happen to agree today is precisely the failure you reported.

⭐ **What you could not have known:** you asked for this during a refactor that was collapsing three
hand-written body-line parsers into one shared proposition recogniser. The forms you would have copied
last week were **wrong in four places** — transitive `x l+ y` existed only in a goal, the five comparison
operators only in a `type` block, `x is there` only in a criterion, negation only in a criterion. Those
were accidents of three parsers, not decisions. A copy in your UI would have frozen them.

⚠ **One change is visible to you:** `x l+ y` now works in a `when`/`unless` condition, and the evaluator
moved with it (it previously compared one direct edge). Also `x is there` and `x.k known` are now
*recognised everywhere and refused by name* where they are meaningless, rather than falling through to a
generic message — so your validation surface gets better errors without doing anything.

⚠ **We did not give you machine-readable shape**, per your own scoping — no parser API, no AST, no
partial-input parsing. If prose shapes turn out to be too thin for completion, say so with an example of
what you would do with structure and we will look again; we did not want to promise a stability nothing
tests.

## §7 — `resolve` should carry its candidates — **DONE**

```python
except intake.Ambiguous as e:
    e.candidates   # ('chunk#2', 'chunk#1')
    e.name         # 'salt'
```

`Ambiguous` subclasses `Unreadable`, so every existing `except Unreadable` still catches it and the
refusal is unchanged — it only gains attributes.

⚠ **Worth telling you because it is the kind of thing you would have hit:** our first version was defeated
one frame later. `read` catches and re-wraps to attach the line number, which rebuilt a plain `Unreadable`
and dropped the candidates. The unit test passed; **your repro** is what caught it. The re-wrap now
preserves the subclass.

Your framing was also the deciding argument: this does not weaken *never identify by name alone*, because
the engine still refuses and the disambiguation is a human choosing above the border who then writes an
unambiguous reference. Same division we draw for a language model.

## §4 — `ugm_surface_regressions.md` — **already closed**

The file is not in the tree. Nothing to triage, and thank you for closing it explicitly.

---

## §3 — the defeasible prohibition — **IN SCOPE, and built: `norm.py`**

You offered "out of scope" as an acceptable answer. The ruling, from the project owner, is worth quoting
because it is a standing principle and not a decision about your item:

> *"Why would it not be? Anything expressable should be in scope; we can decide the HOW, but not the
> whether. And these things must be in data, not Python, otherwise we start creating islands."*

We have corrected `not_supported.md` accordingly — it gained a §4 saying the page **ranks, it does not
scope**. Its judgements are about priority and evidence (*"neither has a caller"*); a line that read
"deliberately not recommended" was a sentence about scope and should not have been.

**Your scenario, running:**

```
-- standing norms only --
   sell: forbid — house (the house does not sell)
   counterfeit: forbid — law (it is illegal), inviolable

-- today says selling is good, and today outranks standing --
   sell: permit — today (there is a fair on); overriding house's forbid
   counterfeit: forbid — law (it is illegal), inviolable

-- what reaches the goal --
   never constraints: ['never counterfeit']
```

**⭐⭐ The mechanism needed no new ranking: a norm's source is its SPEAKER.** *"Today outranks standing"* is
the same shape as *"the supervisor outranks the agent"*, so `discourse.authority` — built the same day for
multi-party retraction, for unrelated reasons — arbitrates norms unchanged. No norm-specific notion of
strength, and *"who says so"* is the ordinary discourse record.

That is also where your **auditability** comes back, which was your actual loss:

```python
norm.explain(g, "sell")
# "sell: permit — today (there is a fair on); overriding house's forbid"
```

The winning norm is a node, its source is a node, and the defeated norms are still there with the reason
they lost.

**⚠⚠ We took your warning literally.** You flagged the shape you did *not* want — a "soft never" that
prunes unless outranked — because arbitration would move inside the planner. `norm.apply(goal)` runs
before the search and writes **ordinary `never` constraints**, so `goal.breached`, `driver.relevance` and
`why` cannot tell the difference. There is no fourth force in the frontier.

**Two decisions you should push back on if they are wrong for you:**

1. **`inviolable` is a force on the NORM, not a top rank for the source.** Ranking `law` highest would
   express *whose word goes* and only approximate *this is not up for discussion* — someone could later
   declare a source above it and nothing would object. Our check grants `today` authority over `law` and
   asserts the counterfeit prohibition still stands. If your `law` is really "a source nobody outranks",
   say so and we will reconsider.
2. **Conflicting norms whose sources are unranked are REFUSED** (`norm.Undecidable`), naming both sources
   and the action. Breaking the tie by declaration order would be an undeclared tie-break, which has bitten
   this engine before. ⚠ This means a domain that previously "worked" by relying on order will now raise.
   We think that is right; you will feel it first.

**⚠ What is NOT done, and it matters to you specifically: there is no CNL surface for a norm.**
`norm.declare` is a Python call, so authoring a norm is currently the exact island the principle above
forbids — the mechanism is data, the authoring path is not. The intended form takes its source from the
speaker:

```
forbid selling:            # said by `house`
    action sell
    because the house does not sell
```

We are deliberately **not** shipping that verb yet. Three things now want a surface at once — `forbid`,
`remember`, and the discourse moves (`ignore that`) — and two of them do not fit `<verb> <label>:` + body
at all. Adding them one at a time is how a controlled language becomes SQL's clause grammar. It is being
decided as one question. **If a Python authoring path blocks you in the meantime, tell us and we will
prioritise the verb over the shape decision.**

---

## §5 — small notes

- **`found` vs `done`** — noted, not changed. Renaming either would break every consumer for a
  readability gain, and your case (`report["done"]` on a `pursue` report returning `None`) is real. If it
  bites again we would rather add a `KeyError`-raising accessor than rename.
- **Savepoint-scoped `read`** — confirmed, and now recorded as a property consumers depend on rather than
  an implementation detail. Your `check()` helper is exactly the intended use. ⚠ We will treat "read never
  commits" as a compatibility promise; if that ever has to change it gets a CHANGELOG entry with
  migration, not a silent fix.
- **Verification style** — agreed, no drift implied. Your layer's interesting failures are interaction
  shapes; ours are engine invariants.

---

## What we would like from you next

1. **Re-run `experiments/cards_on_microfunctions.py`.** Nine of nine reproduced before; §3 and the
   condition changes are the ones that could move a result. The norm arbitration should now be
   deletable from your side — we would like to know how many of those ~17 lines actually go.
2. **Tell us if `forms_for` is enough for completion**, with a concrete example if it is not.
3. **The verb-to-family mapping** — say the word and we export it rather than having you infer it.
