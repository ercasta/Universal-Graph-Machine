"""
Verb catalog — n-ary/relational NL through a DECLARED vocabulary (the principled successor to
universals→laws; docs/handoff_redesign.md). An undeclared verb is indistinguishable from a
multi-word noun phrase, and the engine has no learning yet, so we do NOT infer a word's lexical
category from position (a weak stand-in for the learning we deliberately deferred, vision §10).
Instead the domain's verbs are a CATALOG — data in the KB, declared like everything else
(`eat is a relation`), exactly the standing "lexicon is DATA" constraint. The CNL stays
"caveman": one canonical (base) verb form; English inflection is a corpus-adaptation concern, not
grammar.

The payoff is that the catalog reuses ALL existing machinery: a declared relation word becomes a
surface KEYWORD, which (a) stops the noun-phrase decomposition from eating it as an adjective — the
same fix that enables recognition — and (b) lets the generic body clause fold it inside a universal
rule. These tests lock the round-trip: relational facts + verb-clause rules + reasoning + the
`does S V O` yes/no question.
"""
import ugm as h


def _session(*lines):
    s = h.Session()
    for ln in lines:
        s.submit(ln)
    return s


# ---------------------------------------------------------------------------
# The catalog is load-bearing — a declared verb parses, an undeclared one does not
# ---------------------------------------------------------------------------

def test_declared_relational_fact_parses_and_is_not_mis_decomposed():
    s = _session("eat is a relation", "the dog eat the squirrel")
    # declaring `eat` makes it a keyword -> the NP decomposition stops at it, so we get the binary
    # relation, NOT the adjective mush `squirrel is dog` / `squirrel is eat`.
    assert "dog eat squirrel" in s.facts()
    assert not any(f.startswith("squirrel is") for f in s.facts())


def test_undeclared_verb_is_not_recognized_no_inference():
    # No catalog entry, no guessing: an undeclared verb sentence is reported unrecognized (the
    # linter's "no form recognized this"), never silently turned into a relation by position.
    s = h.Session()
    r = s.submit("the dog eat the squirrel")
    assert not r.recognized
    assert "dog eat squirrel" not in s.facts()


# ---------------------------------------------------------------------------
# Verb clauses inside a universal rule, end-to-end
# ---------------------------------------------------------------------------

def test_universal_rule_over_verb_clauses_reasons():
    s = _session(
        "eat is a relation", "chase is a relation",
        "if something eat the cat then it chase the dog",
        "the squirrel eat the cat",
    )
    # something/it -> ?y; the generic body clause folds `?y eat cat`, the if/then head `?y chase dog`
    [rule] = [r for r in s.rules if r.key.startswith("rule.")]
    assert [p.tokens() for p in rule.lhs] == [("?y", "eat", "cat")]
    assert [p.tokens() for p in rule.rhs] == [("?y", "chase", "dog")]
    assert "squirrel chase dog" in s.facts()          # derived by the rule


# ---------------------------------------------------------------------------
# Binary-relation yes/no questions — `does S V O`
# ---------------------------------------------------------------------------

def test_relational_yesno_question():
    s = _session(
        "eat is a relation", "chase is a relation",
        "the dog eat the squirrel",
        "if something eat the cat then it chase the dog",
        "the squirrel eat the cat",
    )
    assert s.submit("does the dog eat the squirrel").answer == ["yes"]   # asserted
    assert s.submit("does the dog eat the cat").answer == ["no"]         # CWA
    assert s.submit("does the squirrel chase the dog").answer == ["yes"] # DERIVED via the rule


def test_relational_question_is_distinct_from_assertion():
    # The bare declarative `the dog eat the squirrel` is an ASSERTION; only the `does …` form is a
    # question (so asking never depends on a fact already being present to be recognized).
    s = _session("eat is a relation")
    assert not s.submit("the dog eat the squirrel").is_question   # asserted
    assert s.submit("does the dog eat the squirrel").is_question  # queried


# ---------------------------------------------------------------------------
# Definiteness -> uniqueness -> merge (the opt-in domain policy)
# ---------------------------------------------------------------------------

def _same_named_linked(g, nm):
    """True if two mentions of `nm` are linked by an additive `same_as` (the §5-preserving
    coreference that replaced the destructive merge)."""
    ids = set(g.nodes_named(nm))
    return any(g.name(r) == "same_as" and (set(g.into(r)) | set(g.out(r))) & (ids - {n})
               for n in ids for r in g.out(n))


def test_definite_reference_links_mentions_additively():
    # `the is a definite` opts in: `the dog` denotes ONE individual, so all `dog` mentions are
    # force-coreferenced. Additive (`same_as`, never a merge — §5: no fact edge is deleted): the
    # mentions stay distinct nodes LINKED by `same_as`, and their facts compose across the link.
    s = _session("the is a definite", "eat is a relation",
                 "the dog eat the squirrel", "the dog eat the cat")
    assert _same_named_linked(s.kb, "dog")            # mentions coreferenced via additive same_as
    assert "dog eat squirrel" in s.facts() and "dog eat cat" in s.facts()  # both facts compose


def test_without_definite_opt_in_mentions_are_distinct_witnesses():
    # The default (no `the is a definite`) keeps the pure-§3 distinct-witness model: `the` is just a
    # stripped determiner, and repeated mentions are NOT merged (each `dog` its own node).
    s = _session("eat is a relation", "the dog eat the squirrel", "the dog eat the cat")
    assert len(s.kb.nodes_named("dog")) > 1
    assert not any("is_unique" in f for f in s.facts())


def test_definiteness_composes_relational_reasoning():
    # End-to-end with definiteness: merged entities let a verb-clause universal chain correctly.
    s = _session("the is a definite", "eat is a relation", "chase is a relation",
                 "if something eat the cat then it chase the dog",
                 "the squirrel eat the cat")
    assert s.submit("does the squirrel chase the dog").answer == ["yes"]


def test_multiword_definite_entity_links_and_reasons():
    # A DEFINITE multi-word entity (`the bald eagle`) decomposes to head `eagle` + attribute `bald`;
    # marking the whole NP span unique (not just the first token) force-coreferences the HEAD, so the
    # `eagle` mentions are linked by an additive `same_as` (never merged — §5) and their relational
    # facts compose. Relational queries decompose the same way on both sides, so they match.
    s = _session("the is a definite", "eat is a relation",
                 "the bald eagle eat the dog", "the bald eagle is young")
    assert _same_named_linked(s.kb, "eagle")             # multi-word head coreferenced additively
    assert "eagle is bald" in s.facts()                  # the modifier became an attribute
    assert s.submit("does the bald eagle eat the dog").answer == ["yes"]


def test_stopword_name_is_not_coreferenced():
    # A name borne by many nodes (a relation predicate, or a mis-parsed query slot) is a STOPWORD:
    # coreference skips it (the df cap, vision §14), so a query naming it answers fast instead of
    # hanging on O(k²) mention pairs. Here `eat` appears in many facts; asking it as an entity slot
    # must return promptly (the answer is just 'no' — there is no entity named `eat`).
    s = _session("the is a definite", "eat is a relation",
                 *[f"the animal{i} eat the plant{i}" for i in range(30)])
    assert s.submit("does the dog eat eat").answer in (["no"], ["yes"])  # completes, no hang
