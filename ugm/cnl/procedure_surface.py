"""The procedure authoring surface — `to NAME : STEP then STEP then …`
(docs/design/procedures_design.md §2 item 3; Procedures arc Slice 2).

A named, remembered step sequence is authored with a `to NAME : …` HEADER — the same shape as
`form KEY : …`, and like it a dedicated INTAKE ROUTE, not a fact-form. Why a route and not a
`FACT_FORM` in the recognition bank: (1) the fact bank is one non-stratified `run_bank`, where a
span-tag marking the procedure's `then`s would RACE `form.then` (`X then Y -> X before Y`) to those
tokens — `form.then` fires first and mints the planner's GLOBAL `before`; (2) a procedure needs
PROCEDURE-SCOPED order — `step_before`, lifted to `before` ONLY while the procedure runs (the ORDER
rule in `corpus/procedure.cnl`), so a step name shared by two procedures isn't ordered globally by
one of them. Parsing the header here sidesteps both: we emit `step`/`step_before`/`is_a procedure`
directly. This stays UGM-side of the tool boundary — pure CNL surface, no world action.

The generated facts are exactly what the stepping bank consumes (Slice 1):
    to brew : add_beans then heat
  ->  brew step add_beans     brew step heat        (membership — INVOKE reads `?p step ?s`)
      add_beans step_before heat                    (order   — ORDER reads `?a step_before ?b`)
      brew is_a procedure                           (metadata; not read by the 3 rules)
"""
import re

# `to NAME : BODY` — the header colon is the strong signal (a plain fact never carries the
# `to … : … then …` shape), exactly as `form KEY :`'s colon distinguishes it. Case-folded like
# every token (the tokenizer lowercases).
_HEADER = re.compile(r"^to\s+(.+?)\s*:\s*(.+)$")
_THEN = re.compile(r"\bthen\b")


def parse_define(text: str) -> tuple[str, list[str]] | None:
    """`to NAME : A then B then C` -> ("name", ["a", "b", "c"]); None if the header does not fire.

    Recognition (not a string sniff of content): the `to … :` header + a non-empty step body.
    A single-step procedure (`to greet : wave`) is valid — it just has no `step_before`."""
    m = _HEADER.match(text.strip().lower())
    if not m:
        return None
    name = m.group(1).strip()
    steps = [s.strip() for s in _THEN.split(m.group(2)) if s.strip()]
    if not name or not steps:
        return None
    return name, steps


def stage_procedure(kb, name: str, steps: list[str]) -> None:
    """Emit the procedure's facts into `kb`: membership (`step`), procedure-scoped order
    (`step_before`), and the `is_a procedure` marker. Nodes are REUSED by name (the steps name
    operators/tools that already exist), matching the recognition pipeline's interning — a fresh
    node only for a genuinely new name (the procedure's own)."""
    def ensure(n: str) -> str:
        found = kb.nodes_named(n)
        return found[0] if found else kb.add_node(n)

    proc = ensure(name)
    kb.add_relation(proc, "is_a", ensure("procedure"))
    for s in steps:
        kb.add_relation(proc, "step", ensure(s))
    for a, b in zip(steps, steps[1:]):
        kb.add_relation(ensure(a), "step_before", ensure(b))


# ---------------------------------------------------------------------------
# The invocation surface — `run NAME`  ->  `<run> proc NAME`
# ---------------------------------------------------------------------------

def parse_run(text: str) -> str | None:
    """`run NAME` -> "name" (the procedure to run); None if the invocation does not fire. Tolerates
    the noise words a caller might add (`run the brew`, `run procedure brew`, `run brew procedure`).
    A keyword-led COMMAND, like intake's `goal …` — recognition by the leading `run`, not KB state."""
    t = text.strip().lower()
    if not (t == "run" or t.startswith("run ")):
        return None
    rest = t[3:].strip()
    for pre in ("the ", "procedure "):
        if rest.startswith(pre):
            rest = rest[len(pre):].strip()
    if rest.endswith(" procedure"):
        rest = rest[:-len(" procedure")].strip()
    return rest or None


def stage_run(kb, name: str) -> None:
    """Seed the invocation request `<run> proc NAME` the stepping bank's INVOKE rule reads. The
    named procedure node is REUSED (authored earlier by `stage_procedure`)."""
    def ensure(n: str) -> str:
        found = kb.nodes_named(n)
        return found[0] if found else kb.add_node(n)

    kb.add_relation(ensure("<run>"), "proc", ensure(name))
