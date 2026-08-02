"""DISCOURSE — what was SAID, in order, and what was later taken back.

**The hole this fills.** `intake.read` builds a goal, a criterion, a method — and records **nothing about
the fact that somebody said it**. Measured: authoring two blocks against a fresh thread left it with its
opening entry and nothing else. So the system could hold what it had been told and could not point at the
*telling*, which is the third time this project has hit the same defect in a different place — `goal.py`
exists because *"the one thing the system was trying to do was the one thing it could not point at"*, and
`thread.py` exists because attention was the one thing not homoiconic. An utterance was the next one.

## ⭐⭐⭐ AN UTTERANCE IS IN THE WORLD; THE THREAD MERELY ATTENDS IT

**The correction that shaped this module.** The first version made an utterance a *thread entry* and stored
its speaker as a **string attribute** (`by="user"`) — this project's standing rule broken in one line,
*never identify by name alone*. That is harmless with one actor and wrong the moment there are three, and
it can never represent an external system or another agent at all.

Two things had been conflated, and they separate cleanly:

* **the conversation** — utterances *by agents*. Real: it hangs off `root`, its speakers are **nodes**,
  another agent can quote it, and a rule can doubt it. This is where multi-party lives.
* **the system's own episode** — where attention went. Metadata, pointing inward, never pointed at.

So an utterance hangs off the conversation and the thread *attends* it. ⚠ `thread.attend` already linked an
entry to a world node, so this needed **no new entry kind** — the third kind the first version added was
given back, and `thread.py`'s *"two entry kinds, and deliberately only two"* turned out to be right.

⚠ Retraction still needs utterances and applications in **one order** — *was this already acted on?* — and
it has that, because an attention entry sits in the same `step` edge as everything else.

⭐ This is also the caller `not_supported.md` **G7** was missing. That entry (*"who said so"*, beliefs held
by someone other than the system) is recommended against on the stated grounds that *"neither has a
caller"*. Multi-party discourse is one; the deferral was conditional, and the condition is now met.

## ⭐⭐ RETRACT THE UTTERANCE, NOT THE WORLD

*"Ignore that"* looks like one move and is three, with wildly different costs. This module does the first
and **refuses to pretend about the other two**:

| what is asked | what happens here |
|---|---|
| stop consulting it | **this**: the block is marked withdrawn and every enumerator skips it |
| undo what it let us conclude | **not done.** `REVISION 01` deleted all retraction/TMS machinery deliberately |
| undo what was done in the world | **not possible.** The undo journal is transactional and *"a rollback boundary must never span a dispatch"* |

**⚠⚠ So withdrawal is prospective, and history is deliberately left standing.** A withdrawn criterion that
already shaped a plan is still cited by `why`, annotated as withdrawn. That is not a shortcut: `forget.py`
already settled that retention defaults to KEEP *because* `why`, `memory.attribute` and
`conflict.interference` all read history, and deleting what was reasoned from can contradict conclusions
already drawn. A record saying *"this happened because of something you later took back"* is strictly more
useful than one with a hole where the reason was.

⚠ **Withdrawal is a mark, never a deletion**, for the same reason. `is_withdrawn` is asked at enumeration
time by the three functions that enumerate authored data, so nothing has to remember to filter.

## ⭐⭐⭐ THE CONVENTIONS ARE A PROTOCOL, because the graph is shared

The premise (the user's, 2026-08-02): *another piece of software may write into the graph, using its own
locks, respecting the conventions for representing the discourse.* That makes the **conversation the
integration surface**, and these conventions stop being this module's private business. To participate,
write exactly this and nothing else is required:

| | |
|---|---|
| the utterance | a node of kind `utterance`, on the conversation's ordered `utterance` edge |
| who said it | a `by` edge to an **agent** node (kind `agent`, hanging off `root`) |
| what it says | `text` and/or `verb` attributes; an `about` edge if it authored something |
| standing | an `authority_over` edge between agents — transitive, and the only thing that lets one speaker withdraw another's |

⚠ **An utterance nobody has attended is heard by nobody, and that is the honest reading.** `utterances`
reads off the **thread**, so an external write is invisible until `attend_new` brings it in — measured, and
it was a real hole. Attending is what puts it into the one order retraction depends on.

⚠⚠ **Two constraints the locking discipline must respect, and they are not ours to enforce:**

* **A rollback boundary must not span an external write.** `intake.read` is savepoint-scoped and rolls back
  on refusal — a property `feedback_from_harneskills` §6 depends on for parse-as-you-type — so a concurrent
  writer inside that window would be undone by a rollback that has nothing to do with it. Exactly parallel
  to `dispatch.py`'s *"a rollback boundary must never span a dispatch"*, and for the same reason: past that
  point the journal is a lie about what can be undone.
* **Mint-then-link must be atomic to other readers.** An utterance linked to the conversation before its
  `by` edge exists is, for one instant, an utterance nobody said — and `attend_new` would take it.
"""
from __future__ import annotations

from . import intake as I
from . import thread as T
from .graph import Graph

#: Default speaker labels. ⚠ These name **nodes**, and that correction is the point of this module's
#: shape. The first version stored the speaker as a *string attribute* (`by="user"`), which is this
#: project's standing rule broken in one line — *never identify by name alone*. Harmless with one actor,
#: immediately wrong with three, and incapable of representing an external agent at all.
USER, SYSTEM = "user", "system"

UTTERANCE = "utterance"


def speaker(g: Graph, label: str = USER) -> str:
    """Find-or-mint the agent with this label. **A real thing, hanging off `root`.**

    ⚠ Refuses an ambiguous label rather than picking, like every other name resolution here."""
    hits = [a for a in g.of_kind("agent") if g.attr(a, "label") == label]
    if len(hits) > 1:
        raise ValueError(f"{label!r} names {len(hits)} agents; never identify by name alone")
    if hits:
        return hits[0]
    a = g.mint("agent", label=label, kind_of="agent")
    g.link("root", "has", a)
    return a


def conversation(g: Graph) -> str:
    """Find-or-mint *the* conversation. A world object: utterances hang off it, in order."""
    existing = [c for c in g.of_kind("conversation")]
    if existing:
        return existing[0]
    c = g.mint("conversation", kind_of="conversation", label="conversation")
    g.link("root", "has", c)
    return c


def say(g: Graph, thread: str, text: str, *, by=USER, under: str = "root",
        why: str | None = None) -> dict:
    """Read a block **and record that it was said, by whom**. Returns `{verb, node, utterance, entry}`.

    ⚠ This is `intake.read` plus the record, rather than a change to `read`: a caller with no thread — the
    self-test's fixtures, a KB loaded from disk — has nothing to record against, and making the thread
    mandatory would turn every one of those into a discourse of one remark."""
    verb, node = I.read(g, text, under=under)
    u = _utter(g, thread, by=by, verb=verb, about=node, text=text, why=why)
    return {"verb": verb, "node": node, "utterance": u, "entry": T.tip(g, thread)}


def _utter(g: Graph, thread: str, *, by, verb: str | None, about: str | None,
           text: str | None, why: str | None = None) -> str:
    """Mint the utterance **in the world** and have the thread ATTEND it.

    ⭐⭐ Two records, and they are not a duplicate — they are the two halves the first version conflated.
    The utterance is a world event: it has a speaker, another agent may quote it, a rule may doubt it. The
    *thread* holds the system's attention on it, which is metadata and points inward exactly as
    `thread.py` requires. `attend` already linked an entry to a world node, so this needed no new kind."""
    who = by if by in g.nodes else speaker(g, by)
    u = g.mint(UTTERANCE, kind_of=UTTERANCE,
               **{k: v for k, v in (("verb", verb), ("text", text)) if v is not None})
    g.link(conversation(g), "utterance", u)
    g.link(u, "by", who)
    if about is not None:
        g.link(u, "about", about)
    T.attend(g, thread, u, why=why, note=verb)
    return u


def utterances(g: Graph, thread: str, *, by=None) -> tuple:
    """Everything said, **in the order the system attended it**, optionally filtered by speaker.

    ⚠ Read off the thread rather than off the conversation, and that is deliberate: retraction's question
    is *what happened in between*, which needs utterances and applications interleaved in one order. The
    conversation holds the same utterances for anyone who wants to reason about them without a thread."""
    who = None if by is None else (by if by in g.nodes else speaker(g, by))
    out = []
    for e in T.entries(g, thread):
        u = g.target(e, "at")
        if u is not None and g.kind(u) == UTTERANCE and (who is None or g.target(u, "by") == who):
            out.append(u)
    return tuple(out)


def unattended(g: Graph, thread: str) -> tuple:
    """Utterances in the conversation this thread has **not** attended — what somebody ELSE wrote.

    ⭐⭐ **This is the interop hole, and it falls straight out of the graph being shared.** The premise
    (the user's, 2026-08-02) is that *another piece of software may write into the graph, using its own
    locks, respecting the conventions for representing the discourse*. Under that premise the conversation
    is the **integration surface** — an external agent mints an utterance with a speaker and links it,
    exactly as `_utter` does — and the engine was structurally unable to see it: `utterances` reads off the
    **thread**, which is the record of what *this* system attended. Measured: two utterances in the
    conversation, one visible.

    ⚠ So the conventions stop being an implementation detail of this module and become a **protocol**.
    An utterance is: kind `utterance`, on the conversation's `utterance` edge, with a `by` edge to an
    agent, optional `text` / `verb`, optional `about`. Anything writing that shape is a participant."""
    seen = set(utterances(g, thread, by=None))
    return tuple(u for u in g.targets(conversation(g), "utterance") if u not in seen)


def attend_new(g: Graph, thread: str, *, why: str = "heard") -> tuple:
    """Bring everything somebody else said onto this thread, in conversation order. Returns what arrived.

    ⚠ **Attending is what puts an external utterance into the ONE order retraction depends on** — *was
    this already acted on?* is answerable only because utterances and applications share the thread's
    `step` edge. An utterance sitting in the conversation unattended is heard by nobody, which is the
    honest reading: the system has not looked at it yet."""
    fresh = unattended(g, thread)
    for u in fresh:
        T.attend(g, thread, u, why=why, note=g.attr(u, "verb"))
    return fresh


def last_said(g: Graph, thread: str, *, by: str | None = USER):
    """The most recent utterance, or `None`.

    ⭐ **This is what *"that"* denotes, and it needs no naming at all.** `intake.py` records the blocker for
    `replan` — goals do not hang off `root`, so `resolve` cannot find one by label, and inventing a naming
    scheme would be the guess a controlled language exists to refuse. Deixis sidesteps it: the most recent
    thing said is identified by the order, which the thread already has. Same move as `what`/`where`, which
    locate a thing in an order the world already has rather than describing it."""
    said = utterances(g, thread, by=by)
    return said[-1] if said else None


# --- withdrawal -------------------------------------------------------------------------------------
def authority(g: Graph, holder, over) -> str:
    """*`holder` may withdraw what `over` said.* **Ordinary world data**, authored like anything else.

    ⭐⭐ This is where multi-party discourse stops being a single-actor case with extra names. *"Ignore
    that"* is not a global fact once there are three speakers — it is an **act by somebody**, and whether
    it takes effect is a question about standing. Three answers were defensible; this is the one that
    keeps the engine free of a built-in social model:

    * the **default** is that only the speaker withdraws their own utterance, so a one-actor session
      behaves exactly as it did before any of this existed;
    * anything else must be **said**, in the world, where it can be inspected, disputed and withdrawn like
      any other claim.

    ⚠ **Transitive, via `path.reaches`** — a supervisor over a lead over an agent reaches the agent, and it
    is the same reader `goal.holds` and a `+` condition use, so the three cannot disagree about what
    reachability means."""
    return g.link(holder if holder in g.nodes else speaker(g, holder),
                  "authority_over", over if over in g.nodes else speaker(g, over))


def may_withdraw(g: Graph, who, utterance: str) -> bool:
    """Has `who` the standing to withdraw this utterance? Speaker themself, or authority over them."""
    from .path import reaches
    who = who if who in g.nodes else speaker(g, who)
    said_by = g.target(utterance, "by")
    return who == said_by or reaches(g, who, "authority_over", said_by)


def retract(g: Graph, thread: str, target: str | None = None, *, by=USER) -> dict:
    """*"Ignore that."* Withdraw an utterance so nothing consults what it authored any more.

    `target` is an utterance entry; omitted, it means **the last thing said that has not already been
    withdrawn** — so a second "ignore that" reaches further back rather than uselessly re-withdrawing.

    ⚠ The retraction is **itself an utterance** and goes on the record. A discourse move that left no trace
    would make the thread say the block was authored and never say why it stopped applying, which is the
    hole this module exists to close."""
    if target is None:
        target = _last_live(g, thread)
    if target is None:
        raise ValueError("nothing has been said on this thread that could be ignored")
    if g.kind(target) != UTTERANCE:
        raise ValueError(f"only an utterance can be withdrawn, and {target!r} is a {g.kind(target)}")
    if g.attr(target, "withdrawn"):
        raise ValueError("that has already been withdrawn")
    if not may_withdraw(g, by, target):
        # ⚠ Refused rather than silently ignored. The first version had no notion of standing and let
        # anybody withdraw anything — a policy nobody chose, which is the same drift this session deleted
        # from three hand-written parsers.
        mine, theirs = speaker(g, by) if by not in g.nodes else by, g.target(target, "by")
        raise ValueError(
            f"{g.attr(mine, 'label')!r} cannot withdraw what {g.attr(theirs, 'label')!r} said. A speaker "
            f"may withdraw their own utterance; anything else needs authority, which is world data — "
            f"say it with `discourse.authority`.")
    u = _utter(g, thread, by=by, verb="retract", about=None, text="ignore that", why="retracted")
    g.link(u, "withdraws", target)
    g.put(target, withdrawn=True)
    entry = T.tip(g, thread)
    node = g.target(target, "about")
    if node is not None:
        # ⚠ The mark goes on the AUTHORED NODE as well as the utterance, because the enumerators below are
        # handed nodes and have no thread to consult. Both, not either: the utterance carries *when* it was
        # taken back, the node carries *that* it was — and `why` needs the first while `criteria` needs
        # the second.
        g.put(node, withdrawn=True)
    return {"said": u, "withdrew": target, "entry": entry, "node": node}


def _last_live(g: Graph, thread: str):
    for e in reversed(utterances(g, thread, by=None)):
        if g.attr(e, "verb") != "retract" and not g.attr(e, "withdrawn"):
            return e
    return None


def is_withdrawn(g: Graph, node: str) -> bool:
    """Has this authored block been taken back? Asked at enumeration time, never cached."""
    return bool(g.attr(node, "withdrawn"))


def live(g: Graph, nodes) -> tuple:
    """`nodes`, minus anything withdrawn. **The one filter**, so the three enumerators cannot drift."""
    return tuple(n for n in nodes if not is_withdrawn(g, n))


def withdrawn_at(g: Graph, node: str):
    """The utterance that took `node` back, if one did — what `why` cites when it explains a decision that
    was made while a since-withdrawn block still applied."""
    for e in g.sources(node, "about"):
        if g.kind(e) == UTTERANCE and g.attr(e, "withdrawn"):
            for r in g.sources(e, "withdraws"):
                return r
    return None


# --- the system asking -------------------------------------------------------------------------------
#: The tool a host registers to actually put a question in front of a person.
#: `dispatch.register(ASK_USER, handler, observes=True)` — **observing**, because asking costs time and
#: changes nothing, which is exactly the distinction `dispatch.register` was given `observes` for.
ASK_USER = "ask_user"


def ask(g: Graph, thread: str, question: str, *, note: str | None = None) -> dict:
    """The system asks; the answer comes back and **both** land on the record.

    ⭐⭐ *"Confirm"* is not a discourse primitive — it is this. A system that can only *receive* utterances
    cannot be confirmed with, because there is nothing on the record for an answer to be an answer *to*.
    So the discourse is two-directional, and a question is an utterance with `by=SYSTEM`.

    **⭐ Asking is a DISPATCH, and needed no new machinery.** It is a world crossing like any other: it
    leaves the graph, it comes back with information, and it is `observes=True` because it costs time and
    changes nothing — the distinction `dispatch.register` grew `observes` for. That buys:

    * a standing prohibition can **veto** asking, like anything else, through the one choke point;
    * the question is **committed before** the handler runs, so a host that never answers still leaves a
      thread that says what was being waited for.

    ⚠⚠ **What it does NOT buy, measured rather than assumed.** `service` refuses a target that lives inside
    a workbench, and the first version of this docstring claimed that therefore *"the planner structurally
    cannot ask"*. It does not follow and it is **false**: the target here is the question node, minted
    fresh in the real graph, so `_in_workbench` is false however imagined the caller is. The protection is
    real for a dispatch aimed at a *world* node and simply does not reach this one. Today nothing can
    trigger it — `ask` is Python and no ISA opcode reaches it, so a `.mf` body running on a workbench
    cannot call it at all — which makes this a **latent** gap rather than a live one. Recorded here rather
    than fixed with a guard nobody can currently exercise; if `ask` ever becomes reachable from a
    microfunction body, it needs its own refusal and a check that plants the imagined case.

    ⚠ **The answer is returned, not interpreted.** Whether *"yes"* settles anything is the caller's to
    decide — and if the answer is itself a block worth authoring, the caller passes it to `say`. Reading it
    here would make this module quietly the second parser."""
    from . import dispatch
    q = _utter(g, thread, by=SYSTEM, verb=ASK_USER, about=None, text=question, why=note)
    g.put(q, pending=True)
    answer = dispatch.service(g, ASK_USER, q, record_on=q)
    return answered(g, thread, q, answer)


def answered(g: Graph, thread: str, question: str, answer: str) -> dict:
    """Record a reply to `question`. Separate from `ask` so a host that answers **later** — the realistic
    case, since a person is not a function — records it the same way a synchronous handler does."""
    if g.kind(question) != UTTERANCE or g.attr(question, "verb") != ASK_USER:
        raise ValueError(f"{question!r} is not a question this system asked")
    reply = _utter(g, thread, by=USER, verb="answer", about=None, text=str(answer), why="answered")
    g.link(reply, "answers", question)
    g.put(question, pending=False)
    return {"question": question, "reply": reply, "entry": T.tip(g, thread), "answer": answer}


def pending(g: Graph, thread: str) -> tuple:
    """Questions the system has asked and nobody has answered — *what is it waiting for?*

    ⚠ Derived from the record rather than stored in a queue. A second list of outstanding questions would
    be a second thing to keep true, and `thread.py` already refuses a stored `tip` for that reason."""
    return tuple(e for e in utterances(g, thread, by=SYSTEM) if g.attr(e, "pending"))


def describe(g: Graph, thread: str) -> str:
    """The discourse, for a reader."""
    out = []
    for u in utterances(g, thread, by=None):
        mark = " [withdrawn]" if g.attr(u, "withdrawn") else ""
        first = (g.attr(u, "text") or "").splitlines()[0] if g.attr(u, "text") else g.attr(u, "verb")
        out.append(f"{g.attr(g.target(u, 'by'), 'label')}: {first}{mark}")
    return "\n".join(out)


def said_by(g: Graph, utterance: str):
    """The agent who said it — **a node**, so it can be reasoned about, given authority, or disbelieved."""
    return g.target(utterance, "by")


__all__ = ["USER", "SYSTEM", "UTTERANCE", "ASK_USER", "speaker", "conversation", "say", "utterances",
           "unattended", "attend_new", "last_said", "authority", "may_withdraw", "retract", "is_withdrawn", "live", "withdrawn_at",
           "ask", "answered", "pending", "said_by", "describe"]
