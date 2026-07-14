"""Phase 8.3a — the discourse focus stack (docs/design/cnl_intake_design.md §3).

Focus is control-layer structure; ops are content-blind; the explicit CNL is recognized as forms.
"""
from ugm import focus
from ugm.intake import ingest
from ugm.world_model import Graph


RULES = """
?x is innocent when ?x in library
?x is cleared when ?x is innocent
?x is thief when ?x is a suspect and ?x is not cleared
"""


# --- the stack ops in isolation ------------------------------------------------------------------

def test_widen_creates_and_grows_top_frame():
    kb = Graph()
    focus.widen(kb, {"ada"})
    assert focus.top_centers(kb) == ["ada"]
    focus.widen(kb, {"bo"})
    assert focus.top_centers(kb) == ["ada", "bo"]      # widen-only accretes the SAME top frame


def test_push_is_a_topic_switch():
    kb = Graph()
    focus.widen(kb, {"ada"})
    focus.push_focus(kb, ["cy"])                        # new topic
    assert focus.top_centers(kb) == ["cy"]             # top is the new frame, not ada's


def test_drop_pops_to_the_frame_below():
    kb = Graph()
    focus.widen(kb, {"ada"})
    focus.push_focus(kb, ["cy"])
    focus.drop_focus(kb)                               # forget the cy topic
    assert focus.top_centers(kb) == ["ada"]


def test_reenter_pops_to_named_frame():
    kb = Graph()
    focus.push_focus(kb, ["ada"])
    focus.push_focus(kb, ["bo"])
    focus.push_focus(kb, ["cy"])
    focus.reenter_focus(kb, "ada")
    assert focus.top_centers(kb) == ["ada"]


def test_drop_is_not_a_fact_deletion():
    # the entity survives a focus drop (§5): only the focus pointer is cut
    kb, rules = _corpus("ada is a suspect")
    ingest(kb, rules, "ada is a suspect")
    focus.drop_focus(kb)
    assert ingest(kb, rules, "is ada a suspect").answer == ["yes"]


# --- the explicit control-CNL, routed through ingest by FORM recognition --------------------------

def _corpus(text=""):
    from ugm.cnl.authoring import load_corpus
    return load_corpus(text)


def test_focus_on_pushes_via_ingest():
    kb, rules = _corpus()
    out = ingest(kb, rules, "focus on ada")
    assert out.kind == "focus"
    assert out.focus_op[0] == "push"
    assert "ada" in focus.top_centers(kb)


def test_forget_that_drops_via_ingest():
    kb, rules = _corpus()
    ingest(kb, rules, "focus on ada")
    ingest(kb, rules, "focus on bo")
    out = ingest(kb, rules, "forget that")
    assert out.kind == "focus"
    assert focus.top_centers(kb) == ["ada"]


def test_back_to_reenters_via_ingest():
    kb, rules = _corpus()
    ingest(kb, rules, "focus on ada")
    ingest(kb, rules, "focus on bo")
    out = ingest(kb, rules, "back to ada")
    assert out.kind == "focus"
    assert focus.top_centers(kb) == ["ada"]


def test_assertion_implicitly_widens_focus():
    kb, rules = _corpus()
    ingest(kb, rules, "ada is a suspect")
    assert "ada" in focus.top_centers(kb)              # implicit widen on assert, no explicit focus move


def test_question_widens_focus_with_its_subject():
    kb, rules = _corpus()
    ingest(kb, rules, "ada is a suspect")
    ingest(kb, rules, "is ada thief")
    assert "ada" in focus.top_centers(kb)              # the thing asked about is now in play


def test_spent_scaffolding_does_not_accrete():
    kb, rules = _corpus()
    ingest(kb, rules, "ada is a suspect")
    ingest(kb, rules, "bo is a suspect")
    ingest(kb, rules, "is ada thief")
    assert kb.nodes_named("<sentence>") == []          # no sentence chains piled up in the KB


def test_fact_survives_scaffolding_gc():
    kb, rules = _corpus()
    ingest(kb, rules, "ada is a suspect")              # chain GC'd after
    assert ingest(kb, rules, "is ada a suspect").answer == ["yes"]   # the fact is still there


# --- 8.3b seed-from-focus: bounded attention, caller-selected ------------------------------------

def test_focus_bounds_attention_vs_global():
    kb, rules = _corpus(RULES)
    ingest(kb, rules, "ada is a suspect")
    ingest(kb, rules, "cy is a suspect")               # an independent second suspect
    ingest(kb, rules, "focus on ada")                  # top frame = {ada} only

    focused = ingest(kb, rules, "who is thief", attention="focus")
    assert focused.answer == ["ada is thief"]          # bounded: cy is out of attention

    glob = ingest(kb, rules, "who is thief", attention="global")
    assert set(glob.answer) == {"ada is thief", "cy is thief"}   # whole KB


def test_focus_still_answers_a_bound_question_about_the_subject():
    kb, rules = _corpus(RULES)
    ingest(kb, rules, "ada is a suspect")
    ingest(kb, rules, "cy is a suspect")
    # a bound question widens focus with its subject BEFORE answering, so ada is in scope
    assert ingest(kb, rules, "is ada thief", attention="focus").answer == ["yes"]


# --- anaphora is a BOUNDARY concern (2026-07-12): the substrate EXPOSES centers, the SLM resolves ----

def test_top_centers_exposes_the_working_set_for_boundary_resolution():
    kb, rules = _corpus()
    ingest(kb, rules, "ada is a suspect")
    ingest(kb, rules, "bo is a suspect")
    # the external SLM reads these to resolve 'she' / 'the suspect' on the NL->CNL side; the substrate
    # never sees a pronoun and reasons over already-resolved CNL (no in-substrate anaphora resolver).
    assert set(focus.top_centers(kb)) == {"ada", "bo"}
