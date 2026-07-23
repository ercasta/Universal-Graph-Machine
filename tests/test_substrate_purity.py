"""SUBSTRATE-PURITY GUARDRAIL — an architectural fitness function against Python drift.

THE PRINCIPLE (docs/design/reactive_core.md §Composability principle; memory `composability-principle`):
reasoning / governance / policy must live in BANKS — data + rules on the ONE substrate — so mechanisms
combine freely. Hardcoding a policy in Python makes an ISLAND no rule can reach; it cannot compose with
authority, reconsider, the governor, or anything else. Python may ONLY be engine MECHANISM or a thin
EVENT→FACT BRIDGE. But Python is Turing-complete and right there, so the drift "comes natural" — this test
makes it VISIBLE and REVIEWED instead of silent.

HOW: an AST scan of `ugm/` for calls to the raw domain-content mutators (`add_relation`, `set_attr` — the
"author a fact/attribute directly" tells). Every writer must be an explicitly CATEGORIZED entry in MANIFEST.
A NEW module that writes the substrate fails the test until someone adds it with a category + reason — so the
decision "this must be Python" is made consciously, at review, against the principle.

SCOPE (honest limits): this catches a new module quietly AUTHORING graph content — the drift we keep
noticing. It does NOT catch policy logic routed through an already-sanctioned bridge, nor pure-Python
branching that never touches the graph (the deeper tell — decision logic that should be rules — is not
statically detectable). Mutation is the tell in ~all real cases; this is a ratchet, not a proof. Raw
`add_edge`/`add_node` evasion is out of the threat model (the threat is unconscious drift, not adversarial
circumvention).
"""
from __future__ import annotations

import ast
import pathlib

WATCHED = {"add_relation", "set_attr"}          # the "author domain content directly" mutators
_UGM = pathlib.Path(__file__).resolve().parent.parent / "ugm"

# The sanctioned substrate-WRITE surface: every ugm/ module that authors graph content, categorized so each
# is a reviewed decision. CATEGORIES:
#   substrate  — defines the mutators (the graph itself)
#   engine     — the interpreter / drivers / demand solver (mechanism; writes derived facts + control state)
#   surface    — CNL parsing/lowering: turns text into the graph structures the engine reads (mechanism)
#   bridge     — turns an engine-internal EVENT into a substrate fact, then steps out of the way
#   tool       — the §8 tool/calculator boundary (external results → facts)
# A new entry here is a claim that the write is one of these, NOT policy. Policy/governance belongs in banks.
MANIFEST: dict[str, tuple[str, str]] = {
    "attrgraph.py":            ("substrate", "defines add_relation/set_attr; internal graph maintenance"),
    "machine.py":              ("engine", "the ISA interpreter — MINT/EMIT effect application"),
    "apply.py":                ("engine", "forward rule firing (effect application)"),
    "chain.py":                ("engine", "demand solver — materializes derived facts + provenance"),
    "dispatch.py":             ("engine", "tool-call dispatch scaffolding"),
    "interpretation.py":       ("engine", "surface/interpretation scope bookkeeping"),
    "rule_control.py":         ("engine", "rule enable/disable control state"),
    "mode_calls.py":           ("engine", "firmware modes as §8 calculators over the fixed bank"),
    "learner.py":              ("bridge", "learning arc — persists a learned rule as graph data"),
    "licensing.py":            ("bridge", "born-hedged licensing marks on intake"),
    "provenance.py":           ("bridge", "event→fact: justifications / <assumed> NAF-leap records"),
    "flare.py":                ("bridge", "event→fact: fuel exhaustion → the <goal> unresolved flare"),
    "external.py":             ("tool", "tool boundary — external RESULT nodes → facts rules react to"),
    "cnl/grammar.py":          ("surface", "grammar chart parsing builds graph structure"),
    "cnl/forms.py":            ("surface", "CNL form parsing builds graph structure"),
    "cnl/rule_graph.py":       ("surface", "reifies rules into graph data the engines read"),
    "cnl/procedure_surface.py":("surface", "procedure authoring (to …/run …) builds graph"),
    "cnl/comparative.py":      ("surface", "comparative surface — stages gradable facts"),
    "cnl/query.py":            ("engine", "ask_goal: materializes gathered evidence + fires the gate"),
}

VALID_CATEGORIES = {"substrate", "engine", "surface", "bridge", "tool"}


def _writes_substrate(source: str) -> bool:
    """Does `source` CALL a watched mutator? AST, so a mention in a string/comment never false-positives
    and only an actual `x.<mutator>(...)` call counts."""
    tree = ast.parse(source)
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in WATCHED
               for n in ast.walk(tree))


def _writers() -> set[str]:
    """Every ugm/ module (posix path relative to ugm/) that authors domain content."""
    return {p.relative_to(_UGM).as_posix() for p in _UGM.rglob("*.py")
            if _writes_substrate(p.read_text(encoding="utf-8"))}


def test_every_manifest_entry_is_categorized():
    for mod, (cat, reason) in MANIFEST.items():
        assert cat in VALID_CATEGORIES, f"{mod}: unknown category {cat!r}"
        assert reason, f"{mod}: a manifest entry must carry a reason"


def test_no_unsanctioned_module_writes_the_substrate():
    """THE RATCHET. Any ugm/ module that authors domain content must be a categorized MANIFEST entry."""
    writers = _writers()
    undeclared = writers - set(MANIFEST)
    assert not undeclared, (
        "\n\nUNSANCTIONED substrate write(s) — a module authors graph content but is not in the "
        "MANIFEST:\n  " + "\n  ".join(sorted(undeclared)) + "\n\n"
        "The composability principle (docs/design/reactive_core.md §Composability principle): reasoning / "
        "governance / policy belongs in BANKS (data + rules), so it composes. Before allowlisting, ask: is "
        "this really ENGINE MECHANISM or a thin EVENT→FACT BRIDGE? If it is DECISION LOGIC (branching on "
        "graph state, comparing thresholds, choosing actions), it is policy — express it as a rule/corpus, "
        "not Python. If it genuinely is mechanism/bridge, add it to MANIFEST with a category + reason.")


def test_manifest_has_no_stale_entries():
    """Keep the manifest TRUTHFUL: an entry that no longer writes the substrate should be removed."""
    stale = set(MANIFEST) - _writers()
    assert not stale, (
        "\n\nMANIFEST lists module(s) that no longer author the substrate — remove them so the manifest "
        "stays an honest map of the write surface:\n  " + "\n  ".join(sorted(stale)))


def test_the_guardrail_has_teeth():
    """The gate's own gate: the detector must flag a raw content WRITE and ignore a READ or a string
    mention — else the ratchet above would pass vacuously (a drift-shaped module WOULD be caught)."""
    assert _writes_substrate("def f(kb, a, b):\n    kb.add_relation(a, 'p', b)")   # a fact write
    assert _writes_substrate("g.set_attr(n, 'flare_count', v)")                     # an attribute write
    assert not _writes_substrate("x = kb.out(n); y = kb.predicate(r); z = kb.name(n)")  # pure reads: fine
    assert not _writes_substrate("doc = 'call kb.add_relation() to author a fact'")     # a string: not a call
