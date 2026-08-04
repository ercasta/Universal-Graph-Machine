"""Asm — the small assembly surface, and the boundary a language model writes to.

A line-oriented text that parses to stored programs and unparses back, so a model can emit it, a
human can read it, and the round trip can be checked.

    fn service_car(car):
        NATIVE "check" F(car) "car"
        SET F(car) "serviced" true

Assembly rather than a controlled language, for now. A controlled language is the eventual
surface for functions; starting there would mean designing a grammar before knowing what the
operations are. Assembly is unambiguous, so a translation is either right or loudly wrong, with
no interpretation layer to hide a mistake in, and a higher-level surface compiles to exactly this
later without wasting any of it.

Validation is the point rather than a nicety. A model emitting instructions will emit wrong ones,
so every opcode is checked against the actual vocabulary and an unknown one is refused with the
line number and the available set. Silent acceptance of a plausible-looking wrong opcode is the
failure worth engineering against, because it produces a function that runs and does something
else.

Operand syntax:

| written | means |
|---|---|
| `F(car)` | the node a focus head points at |
| `R(x)` | a register |
| `&node42` | a stored reference |
| `"text"` | a string literal |
| `42`, `true`, `false`, `null` | literals |
| `.loop` | a label reference (a string) |
| `.loop:` on its own line | a label definition |
| `bare_word` | a string literal, deliberately forgiving: `SET F(c) colour red` means the obvious thing |
| `param=F(x)` | a named binding, only in `INVOKE`, where the operand is a mapping rather than a list |
| `keep` | trailing, only in `INVOKE`/`ATTEMPT`: leave the callee's activation behind to be read |

`INVOKE` is the one opcode whose operand shape is checked, because it is the one with a shape.
Everywhere else an operand list is positional and an arity mistake shows up as a wrong argument;
`INVOKE` takes a mapping of parameter names to operands, so a positional call would parse, define
and fail only when run. The bindings have a surface (`INVOKE R(out) as_iteration it=F(f)
seq=R(s)`) and anything else is refused at the boundary. That also makes one function composable
from another in the authored surface: a bridge can delegate to a pattern instead of restating its
labels.

See `docs/reference/isa.md`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import isa
from .graph import Graph, Ref
from .isa import F, I, R

# `callable`, not just `isupper()`. `isa.__all__` also exports `WRITES_REGISTER` — a frozenset, not an
# opcode — so the old filter let it through, and `asm` would accept `WRITES_REGISTER` as an instruction at
# load time and fail opaquely inside the interpreter at run time. That is precisely the silent-acceptance
# failure this module's docstring says it exists to prevent, and the same shape the first consumer reported for
# `INVOKE`'s operands. An opcode is a thing you can call to build an `I`.
_OPCODES = {name for name in isa.__all__
            if name.isupper() and name not in {"R", "F", "I"} and callable(getattr(isa, name, None))}

# A quoted string is one token, and so is a named binding whose value is one — `key="two words"` used to
# tokenise as `key="two` and `words"`, so a rule could say `SET F(c) "note" "two words"` and could not say
# the same thing through `set_slot`. That is a gap in the *surface*, not in the vocabulary, and it would
# have looked like a reason the mediated form could not express what the bare one did.
_TOKEN = re.compile(r'\w+="[^"]*"|"[^"]*"|[^\s]+')
_HEADER = re.compile(r"^fn\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*(?:->\s*(\w+)\s*)?(?:mocks\s+(\w+)\s*)?:\s*$")
# `x` or `x: car` — an optional type annotation, which is what makes candidate generation possible:
# without it nothing can ask "which functions could apply to this node?"
_PARAM = re.compile(r"^(\w+)\s*(?::\s*(\w+))?$")
_CALLABLE = re.compile(r"^([FR])\((\w+)\)$")
_BINDING = re.compile(r"^(\w+)=(.+)$")


class AsmError(SyntaxError):
    """Refused at the boundary, with a line number — never a silently-accepted wrong instruction."""


def _operand(tok: str, lineno: int):
    m = _CALLABLE.match(tok)
    if m:
        return (F if m.group(1) == "F" else R)(m.group(2))
    if tok.startswith('"') and tok.endswith('"'):
        return tok[1:-1]
    if tok.startswith("&"):
        return Ref(tok[1:])
    if tok in ("true", "false"):
        return tok == "true"
    if tok in ("null", "none"):
        return None
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    if re.fullmatch(r"-?\d+\.\d+", tok):
        return float(tok)
    return tok                      # bare word, including `.label` references


_INVOKE_FORM = 'INVOKE R(dst) function_name param=operand ...'


def _invoke_args(toks: list, lineno: int) -> tuple:
    """Validate and build `INVOKE`'s operands: `(R(dst), name, {param: operand})`.

    The only operand-shape check in this module, and it is here because this is the only opcode with a
    shape. Every other instruction is a positional list the ISA reads element by element; `INVOKE`'s third
    operand is a *mapping*, so a positional call parses cleanly and then explodes at run time inside the
    interpreter — far from the line that was wrong. See the module docstring for the report."""
    if len(toks) < 2:
        raise AsmError(f"line {lineno}: INVOKE needs at least a destination and a function name — "
                       f"expected `{_INVOKE_FORM}`")
    dst = _operand(toks[0], lineno)
    if not isinstance(dst, R):
        raise AsmError(f"line {lineno}: INVOKE's first operand must be a register to put the result in, "
                       f"not {toks[0]!r} — expected `{_INVOKE_FORM}`")
    name = _operand(toks[1], lineno)
    # A focus head is a function operand like any other, and refusing one here was friction sitting
    # exactly on the pattern late binding depends on: a procedure passed as a *parameter* arrives as
    # `F(fn)`, so calling it needed a `COPY` into a register first for no reason the ISA has — `_v`
    # resolves `F` and `R` by the same line. The name is still what travels; only the operand form grew.
    if not isinstance(name, (str, R, F)):
        raise AsmError(f"line {lineno}: INVOKE's second operand must be a function name, "
                       f"not {toks[1]!r} — expected `{_INVOKE_FORM}`")
    # Two operand forms, and the second is what lets a program call something it worked out. A single
    # bare register is a NODE describing the bindings (`arg` edges carrying `param` and `value`), which is
    # how a caller assembles parameter *names* at run time — see `isa._bindings`. Named bindings stay the
    # ordinary form; nothing that reads well today changes.
    rest = toks[2:]
    # `keep` — a trailing word asking the call to leave its activation behind, so the caller can ask what
    # it did (`SELF`, then the last `called`). Stripped before the bindings are read, so it composes with
    # both operand forms below. Without it the call is discarded when it finishes: see `isa._keeps`.
    keep = ()
    if rest and _operand(rest[-1], lineno) == isa.KEEP:
        rest, keep = rest[:-1], (isa.KEEP,)
    # `with R(args)` — the bindings are a NODE describing them, so a program can assemble parameter
    # *names* at run time (`isa._bindings`). The keyword is not decoration: a bare register here would be
    # indistinguishable from the positional mistake this function exists to refuse, and that ambiguity
    # went red on the check that guards it.
    if len(rest) == 2 and rest[0] == "with":
        return (dst, name, _operand(rest[1], lineno)) + keep
    bindings = {}
    for tok in rest:
        m = _BINDING.match(tok)
        if not m:
            raise AsmError(
                f"line {lineno}: INVOKE binds parameters BY NAME, so {tok!r} has nowhere to go — "
                f"expected `{_INVOKE_FORM}`, e.g. `INVOKE R(out) {name} it={tok}`, or a single "
                f"register holding a binding set")
        if m.group(1) in bindings:
            raise AsmError(f"line {lineno}: INVOKE binds {m.group(1)!r} twice")
        bindings[m.group(1)] = _operand(m.group(2), lineno)
    return (dst, name, bindings) + keep


@dataclass
class Parsed:
    """One parsed function, including its natural language.

    `doc` is the comment block immediately above `fn`; `notes` maps instruction position to the comment
    block immediately above that instruction. Both are kept rather than stripped — see `function.define`
    for why that matters (a comment that lives only in a file is invisible to the running system)."""
    name: str
    params: tuple
    program: tuple
    doc: str | None = None
    notes: dict = field(default_factory=dict)
    ptypes: dict = field(default_factory=dict)     # param name -> declared type name
    returns: str | None = None                     # declared result type — what a planner chains on
    mocks: str | None = None                       # this function is one possible outcome of that one
    #: `when` / `unless` lines, as `(negated, words, line, lineno)` — the conditions under which THIS
    #: body is what the name means here. Kept as text and minted by `load_text`, because the condition
    #: grammar belongs to `intake` and parsing it twice is the drift this codebase keeps recording.
    guards: tuple = ()

    def __iter__(self):
        """Unpacks as `(name, params, program)`, so callers that predate `doc`/`notes` still work."""
        return iter((self.name, self.params, self.program))


def parse(text: str) -> list:
    """Parse to `[Parsed, …]`. Raises `AsmError` with a line number on anything unknown.

    Comment syntax is natural language by design: `#` to end of line. A comment block sitting immediately
    above `fn` documents the function; one sitting immediately above an instruction annotates it. A
    comment on the same line as an instruction is a trailing note for that instruction."""
    out, name, params, program = [], None, (), []
    doc, notes, pending, ptypes, returns, mocks = None, {}, [], {}, None, None
    guards = []

    def flush():
        if name is not None:
            out.append(Parsed(name, params, tuple(program), doc, dict(notes), dict(ptypes), returns,
                              mocks, tuple(guards)))

    for lineno, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        code, _, comment = raw.partition("#")
        code, comment = code.strip(), comment.strip()

        if not stripped:
            pending = []                          # a blank line breaks a comment block from what follows
            continue
        if not code:                              # a whole-line comment: accumulate
            pending.append(comment)
            continue

        header = _HEADER.match(code)
        if header:
            flush()
            name = header.group(1)
            params, ptypes, returns, mocks = [], {}, header.group(3), header.group(4)
            for raw_p in (x.strip() for x in header.group(2).split(",") if x.strip()):
                m = _PARAM.match(raw_p)
                if not m:
                    raise AsmError(f"line {lineno}: bad parameter {raw_p!r} — expected `name` or `name: type`")
                params.append(m.group(1))
                if m.group(2):
                    ptypes[m.group(1)] = m.group(2)
            params = tuple(params)
            program, notes, guards = [], {}, []
            doc = " ".join(pending) or (comment or None)
            pending = []
            continue
        if name is None:
            raise AsmError(f"line {lineno}: instruction outside any function — expected `fn name(...):`")

        first = code.split(None, 1)[0]
        if first in ("when", "unless"):
            # **A condition, not an instruction.** One per line, above the body, because that is what
            # lets a refusal name *which* one failed — the property `criterion.governing` is built on and
            # an opaque predicate could never give. It also scales: a header clause would have to hold
            # them all on one line.
            #
            # Only before the first instruction. A condition decides whether this body runs at all, so
            # one written halfway down reads as though it applied from there, and it would not.
            if program:
                raise AsmError(f"line {lineno}: `{first}` decides whether this body applies at all, so "
                               f"it belongs above the instructions, not among them")
            guards.append((first == "unless", code.split()[1:], code, lineno))
            pending = []
            continue

        note = " ".join(pending + ([comment] if comment else [])) or None
        pending = []
        if note:
            notes[len(program)] = note

        if code.endswith(":") and code.startswith("."):
            program.append(code[:-1])
            continue
        toks = _TOKEN.findall(code)
        op, args = toks[0], toks[1:]
        if op not in _OPCODES:
            raise AsmError(f"line {lineno}: unknown opcode {op!r}. "
                           f"Known: {', '.join(sorted(_OPCODES))}")
        # `ATTEMPT` has `INVOKE`'s shape with an error register in front of the name, so it gets the same
        # operand check rather than falling through to the positional reader — the reason that check
        # exists is that a positional call parses and then explodes far from the line that was wrong.
        if op == "ATTEMPT":
            if len(args) < 3:
                raise AsmError(f"line {lineno}: ATTEMPT needs a result register, an error register and "
                               f"a function name — `ATTEMPT R(out) R(err) <fn> [bindings]`")
            err = _operand(args[1], lineno)
            if not isinstance(err, R):
                raise AsmError(f"line {lineno}: ATTEMPT's second operand is the register the refusal "
                               f"lands in, not {args[1]!r}. Without one the refusal is discarded, which "
                               f"is `INVOKE` with the failure silently dropped")
            # Deliberately not `name` — that is the enclosing loader's variable for the function being
            # DEFINED, and assigning it here renamed the whole function to this call's target. Caught by
            # the function coming back defined under a register's name.
            dst, callee, binds, *keep = _invoke_args((args[0],) + tuple(args[2:]), lineno)
            program.append(I(op, (dst, err, callee, binds, *keep)))
            continue
        program.append(I(op, _invoke_args(args, lineno) if op == "INVOKE"
                         else tuple(_operand(t, lineno) for t in args)))
    flush()
    if not out:
        raise AsmError("no functions found — every instruction must sit under an `fn name(...):` header")
    return out


def _fmt(operand) -> str:
    if isinstance(operand, dict):
        # `INVOKE`'s bindings. Rendering the raw dict was a broken round trip that nothing noticed, because
        # `application.compile_episode` builds this operand in Python and the only check was that the word
        # INVOKE appeared in the dump — so a learned function could not be read back in.
        return " ".join(f"{k}={_fmt(v)}" for k, v in operand.items())
    if isinstance(operand, F):
        return f"F({operand.name})"
    if isinstance(operand, R):
        return f"R({operand.name})"
    if isinstance(operand, Ref):
        return f"&{operand.node}"
    if isinstance(operand, bool):
        return "true" if operand else "false"
    if operand is None:
        return "null"
    if isinstance(operand, (int, float)):
        return str(operand)
    # Labels render bare; every other string is quoted. Input is deliberately forgiving (a bare word
    # parses as a string, because a model writing `SET F(c) colour red` means the obvious thing) but
    # Output is canonical, so `dump` is textually stable and is safe to show a model as "here is what you
    # actually wrote." Asymmetry on purpose: lenient in, strict out.
    if isinstance(operand, str) and operand.startswith("."):
        return operand
    return f'"{operand}"'


def _fmt_call(step) -> str:
    """`INVOKE` and `ATTEMPT`, which are the only instructions whose operands are not a flat list.

    Rendering them positionally loses the two keywords that carry the shape. `with` went missing, so a
    function using the graph-data binding form — `step.mf`'s own dispatching call — dumped to text that
    would not parse back, and the error arrived at the *bindings* check, blaming the operand rather than
    the missing word. `keep` survives on its own as a quoted string, but it is rendered here too, so the
    whole shape is in one place rather than half of it relying on a literal happening to round-trip.

    This is `_fmt`'s recorded defect a second time — *a broken round trip that nothing noticed* — and
    for the same reason: the only check covered the named-bindings form, which is the one that worked."""
    at = 2 if step.op == "INVOKE" else 3               # where the bindings operand sits
    args = list(step.args)
    binds = args[at] if len(args) > at else {}
    body = [_fmt(binds)] if isinstance(binds, dict) else ["with", _fmt(binds)]
    parts = [step.op] + [_fmt(a) for a in args[:at]] + body + [_fmt(a) for a in args[at + 1:]]
    return " ".join(parts).rstrip()


def unparse(name: str, params: tuple, program: tuple,
            doc: str | None = None, notes: dict | None = None, ptypes: dict | None = None,
            returns: str | None = None, mocks: str | None = None, guards: tuple = ()) -> str:
    """Render back to text, natural-language comments included — for inspection, for round-trip checking,
    and for showing a model what it actually wrote after the graph stored it."""
    notes, ptypes = notes or {}, ptypes or {}
    lines = []
    if doc:
        lines.append(f"# {doc}")
    sig = ", ".join(f"{p}: {ptypes[p]}" if p in ptypes else p for p in params)
    arrow = f" -> {returns}" if returns else ""
    mk = f" mocks {mocks}" if mocks else ""
    lines.append(f"fn {name}({sig}){arrow}{mk}:")
    # Guards first, and they must survive the round trip: `unparse` silently dropped the `with` keyword
    # once, so a function using it dumped to text that would not parse back, and the check covered only
    # the form that worked.
    for negated, words, _line, _lineno in guards or ():
        lines.append(f"    {'unless' if negated else 'when'} {' '.join(words)}")
    for pos, step in enumerate(program):
        if notes.get(pos):
            lines.append(f"    # {notes[pos]}")
        if isinstance(step, str):
            lines.append(f"    {step}:")
        elif step.op in ("INVOKE", "ATTEMPT"):
            lines.append("    " + _fmt_call(step))
        else:
            lines.append("    " + " ".join([step.op] + [_fmt(a) for a in step.args]).rstrip())
    return "\n".join(lines)


def load_text(g: Graph, text: str) -> tuple:
    """Parse and store every function in `text`, natural language included. Returns the defined names.

    This is the whole boundary in one call: a model emits text, this validates it, and what lands in the
    graph is ordinary data any microfunction can read, rewrite, or generate more of.

    **A rule that reaches the graph through the closed vocabulary gets that vocabulary linked in**, which
    is the one thing this does beyond parse-and-store. A name is only meaning if something answers it, so
    resolving the names a body calls belongs at the boundary where the body arrives — the alternative is
    a precondition every caller keeps by hand, failing at run time far from the load that should have
    said so. Idempotent, and it cannot recurse: the vocabulary's own bodies use bare opcodes, because
    they are the mediation."""
    from . import access
    from .function import define
    defined, mediated = [], False
    for p in parse(text):
        fnode = define(g, p.name, p.params, p.program, p.doc, p.notes, p.ptypes, p.returns, p.mocks)
        for negated, words, line, lineno in p.guards:
            # The condition grammar is `intake`'s, and it is called rather than copied: a guard's names
            # are its parameters where a criterion's are roles, and the language cannot tell them apart,
            # which is the whole reason one reader serves both.
            from . import intake
            intake.condition(g, fnode, words, negated=negated, line=line, lineno=lineno, names=p.params)
        defined.append(p.name)
        mediated = mediated or access.calls_the_vocabulary(p.program)
    if mediated:
        access.bootstrap(g)
    return tuple(defined)


def load_file(g: Graph, path) -> tuple:
    """Load one `.mf` source file. Errors name the file as well as the line, since a library spread over
    files is otherwise painful to debug."""
    path = Path(path)
    try:
        return load_text(g, path.read_text(encoding="utf-8"))
    except AsmError as e:
        raise AsmError(f"{path}: {e}") from None


def load_dir(g: Graph, path, pattern: str = "*.mf") -> tuple:
    """Load a directory of rule files, sorted for determinism. This is how a KB lives on disk."""
    defined = []
    for f in sorted(Path(path).glob(pattern)):
        defined.extend(load_file(g, f))
    return tuple(defined)


def dump(g: Graph, name: str) -> str:
    from . import criterion as CR
    from .function import load, doc_of, notes_of, param_types, returns_of, mocks_target, guards_of
    params, program = load(g, name)
    # A guard is rendered from the stored test, not from the text it was written as — the same standard
    # every other part of this dump is held to, and the only one that can catch a condition that was
    # stored as something other than what it said.
    guards = tuple((bool(g.attr(t, "negated")),
                    CR.describe_test(g, t).removeprefix("not ").split(), None, None)
                   for t in guards_of(g, name))
    return unparse(name, params, program, doc_of(g, name), notes_of(g, name),
                   param_types(g, name), returns_of(g, name), mocks_target(g, name), guards)


__all__ = ["AsmError", "Parsed", "parse", "unparse", "load_text", "load_file", "load_dir", "dump"]
