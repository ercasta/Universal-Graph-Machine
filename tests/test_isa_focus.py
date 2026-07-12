"""Phase 8.3a — the discourse focus stack (docs/cnl_intake_design.md §3).

Focus is control-layer structure; ops are content-blind; the explicit CNL is recognized as forms.
"""
from ugm import focus
from ugm.intake import ingest
from ugm.world_model import Graph


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
