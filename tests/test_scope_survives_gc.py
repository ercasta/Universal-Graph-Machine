"""A scope node (`<hypothesis>`) must SURVIVE an interleaved fact/rule ingest — the foundational GC
fix (2026-07-22). A scope is edgeless BY DESIGN (its pencils reference it by a `scope` VALUED ATTR,
not a graph edge), so the incidental edge-based GC passes (`lowering.final_gc`, which runs whenever a
bank carries drops — e.g. the fact path's determiner-strip; and `AttrGraph.gc_disconnected`) used to
sweep it as "orphaned scaffolding." That silently destroyed a fork/holder/temporal scope on the NEXT
fact line — reading it back `assumed-no`. The fix EXEMPTS `<hypothesis>` nodes from both (a scope is
deleted only explicitly, by `suppose._drop_scope`). This bug affected the WHOLE scope-generalization
family (holder/temporal/hedge), not just hedges — their own tests never interleaved a fact after
authoring the scope, so it went unseen.
"""
from ugm.cnl.authoring import load_corpus
from ugm.intake import ingest
from ugm.scope_kinds import consider, holds_for
from ugm.scope_kinds import at_time, holds_at, order
from ugm.cnl import uncertainty
from ugm.check import POSITIVE


def test_holder_scope_survives_a_later_fact_ingest():
    kb, rules = load_corpus("nemo is a diver")
    consider(kb, "nemo", ("lion", "is_a", "cat"))
    assert holds_for(kb, "nemo", ("is_a", "lion", "cat")) == POSITIVE      # before
    ingest(kb, rules, "coral is a reef")                                   # a fact line runs the GC
    assert holds_for(kb, "nemo", ("is_a", "lion", "cat")) == POSITIVE      # still relative to nemo


def test_temporal_scope_survives_a_later_fact_ingest():
    kb, rules = load_corpus("")
    at_time(kb, "t1", ("sky", "is", "red")); order(kb, "t1", "t2")
    assert holds_at(kb, "t1", ("is", "sky", "red")) == POSITIVE
    ingest(kb, rules, "coral is a reef")
    assert holds_at(kb, "t1", ("is", "sky", "red")) == POSITIVE


def test_hedge_fork_survives_later_fact_ingests():
    kb, rules = load_corpus("cy is a suspect")
    uncertainty.load_line(kb, "cy is unlikely alibied")
    assert uncertainty.ask(kb, "is cy alibied") == "unlikely"
    ingest(kb, rules, "coral is a reef")           # a plain fact
    ingest(kb, rules, "dan is a suspect")          # another
    ingest(kb, rules, "cy wants freedom")          # a fact ABOUT the fork's own subject
    assert uncertainty.ask(kb, "is cy alibied") == "unlikely"


def test_a_rule_line_also_preserves_a_scope():
    """A rule line carries drops too (its body/ellipsis normalization), so `final_gc` runs — the scope
    must survive that path as well, not only the plain-fact path."""
    kb, rules = load_corpus("cy is a suspect")
    uncertainty.load_line(kb, "cy is unlikely alibied")
    ingest(kb, rules, "?x is watched when ?x is a suspect")
    assert uncertainty.ask(kb, "is cy alibied") == "unlikely"


def test_scope_deletion_still_works():
    """The exemption must NOT block explicit scope deletion (`suppose._drop_scope`) — a read-only
    `suppose` opens a scope, reasons, and drops it, leaving NO `<hypothesis>` node behind."""
    from ugm.suppose import suppose
    from ugm.attrgraph import AttrGraph
    from ugm import assemble_facts
    from ugm.machine import Machine
    from ugm.vocabulary import HYPOTHESIS
    g = AttrGraph()
    Machine().run(g, assemble_facts([("socrates", "is_a", "man")]))
    suppose(g, [("socrates", "is_a", "mortal")], [("is_a", "socrates", "mortal")])
    assert not any(g.has_key(n, HYPOTHESIS) for n in g.nodes())   # the scope was dropped, not leaked
