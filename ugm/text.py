"""A surface for authoring graphs (§3, §8).

One grammar, because it is all one kind of thing: a rule is a relation instance,
`by(R, boss)` is a relation instance, `raining(here)` is a relation instance.
That is R3 and R4 in the surface rather than claimed in prose -- there is no rule
syntax distinct from fact syntax, because there is no rule *node* distinct in kind
from a fact node.

What the language may NOT write is an entry, a moment or a stamp. §13 scores
`authors write entries natively` as a leak: an author who can supply a deposit can
date a claim to when it was not held. So the locus, the deposit, the licence and
the source come from the gate, always.

The line is §4's anchored/generic split. A rule's members are *generic* entries --
signed, with variable loci -- and those are authorable, because a variable commits
to no occasion. Anchored ones never are.

Three statements, with the author saying which, so the loader branches on nothing:

    rule  boil = causes( { +heat(?a,?w), +water(?w) }, { +boiling(?w) @certain } )
    fact  +on(a, b)                    standing knowledge, stamped source=kb
    say   user: +raining(here)         an arrival on the channel `user`
    fact  overrides(<boil>, <cool>)        an ordinary claim, and it seeds precedence

The notation is the design document's own, in ASCII: `-` for the minus sign it
writes as an en dash, `->` for its arrow. §8's worked rules parse as printed.
"""

from typing import Dict, List, NamedTuple, Optional, Tuple

from .chain import GRADES, MINUS, PLUS, UNSURE
from .graph import NodeId
from .machine import Machine
from .rules import CAUSES, IMPLIES, Member

SIGNS = {"+": PLUS, "-": MINUS, "?": UNSURE}


class ParseError(Exception):
    pass


# -- tokenising -------------------------------------------------------------


class Tok(NamedTuple):
    kind: str  # name | var | punct
    text: str
    line: int


_PUNCT = set("(){},=:@+-?")

# Rule names live in angle brackets, as the design document writes them: `<R1>`.
# Without the marker they share one namespace with relations, and a rule named
# `cause` silently becomes the relation in `cause(filter, blocked)` -- the rule
# applies, and the fact it concluded is about a different node than anyone asked
# about. Two things with one name, again.


def tokenise(src: str) -> List[Tok]:
    toks: List[Tok] = []
    line = 1
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if ch.isspace():
            i += 1
            continue
        if ch == "#":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if ch == "<":
            j = src.find(">", i)
            if j < 0:
                raise ParseError(f"line {line}: unclosed rule name")
            toks.append(Tok("rulename", src[i + 1 : j], line))
            i = j + 1
            continue
        if ch == "?" and i + 1 < n and (src[i + 1].isalnum() or src[i + 1] == "_"):
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] in "_-"):
                j += 1
            toks.append(Tok("var", src[i:j], line))
            i = j
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
                # a hyphen continues a name only when a name character follows,
                # so `TT-base` is one name and `-liquid(w)` is a sign and a term
                if j < n and src[j] == "-" and j + 1 < n and (src[j + 1].isalnum() or src[j + 1] == "_"):
                    j += 1
            toks.append(Tok("name", src[i:j], line))
            i = j
            continue
        if ch in _PUNCT:
            toks.append(Tok("punct", ch, line))
            i += 1
            continue
        raise ParseError(f"line {line}: unexpected character {ch!r}")
    return toks


# -- parsing ----------------------------------------------------------------


class Term(NamedTuple):
    """A relation instance, an atom, a variable or a rule reference, still
    unresolved against a graph."""

    head: str
    args: Tuple["Term", ...]
    is_var: bool
    is_rule: bool = False


class RuleMember(NamedTuple):
    sign: str
    term: Term
    grade: str


class Statement(NamedTuple):
    kind: str  # rule | fact | say
    name: str
    connective: str
    antecedent: Tuple[RuleMember, ...]
    consequent: Tuple[RuleMember, ...]
    member: Optional[RuleMember]
    channel: str
    line: int


class Parser:
    def __init__(self, toks: List[Tok]) -> None:
        self.toks = toks
        self.i = 0

    # -- helpers
    def peek(self) -> Optional[Tok]:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def next(self) -> Tok:
        t = self.peek()
        if t is None:
            raise ParseError("unexpected end of input")
        self.i += 1
        return t

    def expect(self, text: str) -> Tok:
        t = self.next()
        if t.text != text:
            raise ParseError(f"line {t.line}: expected {text!r}, found {t.text!r}")
        return t

    def at(self, text: str) -> bool:
        t = self.peek()
        return t is not None and t.text == text

    # -- grammar
    def program(self) -> List[Statement]:
        out = []
        while self.peek() is not None:
            out.append(self.statement())
        return out

    def statement(self) -> Statement:
        t = self.next()
        if t.kind != "name":
            raise ParseError(f"line {t.line}: expected `rule`, `fact` or `say`, found {t.text!r}")
        if t.text == "rule":
            return self.rule(t.line)
        if t.text == "fact":
            return Statement("fact", "", "", (), (), self.member(), "", t.line)
        if t.text == "say":
            ch = self.next()
            if ch.kind != "name":
                raise ParseError(f"line {ch.line}: expected a channel name")
            self.expect(":")
            return Statement("say", "", "", (), (), self.member(), ch.text, t.line)
        raise ParseError(
            f"line {t.line}: unknown statement {t.text!r} -- expected `rule`, `fact` or `say`"
        )

    def rule(self, line: int) -> Statement:
        name_tok = self.next()
        if name_tok.kind != "rulename":
            raise ParseError(
                f"line {name_tok.line}: a rule is named in angle brackets, as the design "
                f"writes it -- `rule <{name_tok.text}> = ...`. The marker is what keeps rule "
                f"names out of the relation namespace."
            )
        self.expect("=")
        conn = self.next()
        if conn.text not in (CAUSES, IMPLIES):
            raise ParseError(
                f"line {conn.line}: {conn.text!r} is not a connective. The closed set is "
                f"`{CAUSES}` and `{IMPLIES}` (§10), and a third earns its place only by "
                f"licensing a different (forward, backward) reading pair."
            )
        self.expect("(")
        ant = self.block()
        self.expect(",")
        con = self.block()
        self.expect(")")
        return Statement("rule", name_tok.text, conn.text, ant, con, None, "", line)

    def block(self) -> Tuple[RuleMember, ...]:
        self.expect("{")
        out = [self.member()]
        while self.at(","):
            self.next()
            out.append(self.member())
        self.expect("}")
        return tuple(out)

    def member(self) -> RuleMember:
        t = self.peek()
        if t is None:
            raise ParseError("unexpected end of input in a member")
        sign = PLUS
        if t.kind == "punct" and t.text in SIGNS:
            # `?` is the unsure sign here; `?x` tokenised as a var, never as this
            sign = SIGNS[self.next().text]
        term = self.term()
        grade = "certain"
        if self.at("@"):
            self.next()
            g = self.next()
            if g.kind == "var":
                raise ParseError(
                    f"line {g.line}: `@ {g.text}` names a locus, and slice one carries "
                    f"the one-locus case only -- an antecedent whose members all sit at "
                    f"the same moment needs no skeleton (§8)."
                )
            if g.text not in GRADES:
                raise ParseError(
                    f"line {g.line}: {g.text!r} is not a grade. The ordinal set is "
                    f"{', '.join(GRADES)} (§10)."
                )
            grade = g.text
        return RuleMember(sign, term, grade)

    def term(self) -> Term:
        t = self.next()
        if t.kind == "var":
            return Term(t.text, (), True)
        if t.kind == "rulename":
            return Term(t.text, (), False, True)
        if t.kind != "name":
            raise ParseError(f"line {t.line}: expected a term, found {t.text!r}")
        if not self.at("("):
            return Term(t.text, (), False)
        self.next()
        args = [self.term()]
        while self.at(","):
            self.next()
            args.append(self.term())
        self.expect(")")
        return Term(t.text, tuple(args), False)


# -- loading ----------------------------------------------------------------


class Loader:
    """Binds parsed statements into a machine.

    Rule names are resolved so `overrides(<boil>, <cool>)` can name rules -- which is
    R3: a rule is a thing other facts can be about.
    """

    def __init__(self, machine: Machine) -> None:
        self.m = machine
        self.atoms: Dict[str, NodeId] = {}
        self.vars: Dict[str, NodeId] = {}
        self.rule_nodes: Dict[str, NodeId] = {}
        self.rules_by_name: Dict[str, object] = {}
        self.channels: Dict[str, NodeId] = {}
        self.LOADED = self.m.g.atom("loaded")
        # Every name the loader itself needs goes through the SAME table the
        # surface resolves against. A relation minted beside the table is a
        # second node with one name -- which is how `says` and `overrides` each
        # silently stopped matching what the surface wrote.
        self.atoms.update(self.m.reserved)
        self.OVERRIDES = self.atom("overrides")

    def rule_ref(self, name: str) -> NodeId:
        if name not in self.rule_nodes:
            raise ParseError(f"no rule named <{name}> was declared")
        return self.rule_nodes[name]

    def atom(self, name: str) -> NodeId:
        if name not in self.atoms:
            self.atoms[name] = self.m.g.atom(name)
        return self.atoms[name]

    def var(self, name: str, scope: Dict[str, NodeId]) -> NodeId:
        # Variables are scoped to a rule: `?w` in two rules is two variables,
        # because a rule is a statement and not a fragment of a larger one.
        if name not in scope:
            scope[name] = self.m.g.var(name)
        return scope[name]

    def build(self, t: Term, scope: Dict[str, NodeId]) -> NodeId:
        if t.is_rule:
            return self.rule_ref(t.head)
        if t.is_var:
            return self.var(t.head, scope)
        if not t.args:
            return self.atom(t.head)
        return self.m.g.rel(self.atom(t.head), *[self.build(a, scope) for a in t.args])

    def term(self, src: str) -> NodeId:
        """Resolve one term against this corpus's names, for asking questions.

        Names are not identity (see `graph.py`) -- a node is identified by being
        the node it is, and `atom()` mints a fresh one every call. What gives a
        name meaning is a *scope*, and the corpus is that scope. So a question
        about what was loaded has to be asked through the loader that loaded it,
        which is the honest arrangement rather than an inconvenience.
        """
        t = Parser(tokenise(src)).term()
        return self.build(t, {})

    def load(self, src: str) -> List[Statement]:
        statements = Parser(tokenise(src)).program()
        # Rules first, so a fact may name a rule declared further down the file.
        for s in statements:
            if s.kind == "rule":
                self._rule(s)
        for s in statements:
            if s.kind == "fact":
                self._fact(s)
            elif s.kind == "say":
                self._say(s)
        return statements

    def _rule(self, s: Statement) -> None:
        if s.name in self.rules_by_name:
            raise ParseError(f"line {s.line}: rule {s.name!r} is already defined")
        scope: Dict[str, NodeId] = {}
        ant = [Member(m.sign, self.build(m.term, scope), m.grade) for m in s.antecedent]
        con = [Member(m.sign, self.build(m.term, scope), m.grade) for m in s.consequent]
        unbound = [
            m for m in con if self.m.g.has_var(m.pattern) and not self._covered(m.pattern, ant)
        ]
        if unbound:
            raise ParseError(
                f"line {s.line}: rule {s.name!r} concludes about a variable its antecedent "
                f"never binds -- the gate would refuse to deposit it (§13)."
            )
        r = self.m.rules.rule(s.connective, ant, con, s.name)
        self.rules_by_name[s.name] = r
        self.rule_nodes[s.name] = r.node

    def _covered(self, pattern: NodeId, ant: List[Member]) -> bool:
        g = self.m.g
        wanted = _vars_in(g, pattern)
        have = set()
        for m in ant:
            have |= _vars_in(g, m.pattern)
        return wanted <= have

    def _fact(self, s: Statement) -> None:
        assert s.member is not None
        scope: Dict[str, NodeId] = {}
        prop = self.build(s.member.term, scope)
        # A fact that NAMES a rule is mentioning it, and a rule node contains the
        # variables of its own patterns. `overrides(<why>, <boil>)` is a ground
        # claim about two rules, not a generic claim -- R3 depends on being able
        # to write it. The `<...>` marker is what makes the distinction visible
        # here, where structurally the two are identical (§13).
        mentions = _mentions_a_rule(s.member.term)
        if not mentions and self.m.g.has_var(prop):
            raise ParseError(
                f"line {s.line}: a fact may not contain a variable -- only a rule's members "
                f"are generic (§4)."
            )
        self.m.gate.write(
            self.m.focus,
            prop,
            s.member.sign,
            grade=s.member.grade,
            licence=self.m.g.rel(self.LOADED, prop),
            source=self.m.KB,
            mention=mentions,
        )
        self._maybe_precedence(s, prop)

    def _maybe_precedence(self, s: Statement, prop: NodeId) -> None:
        """`overrides(A, B)` is an ordinary claim *and* seeds the authored
        precedence table §14 requires. Both, because arbitration must be a lookup
        that never searches, and because *which rules override which* has to stay
        an ordinary query."""
        g = self.m.g
        if g.relation_of(prop) != self.OVERRIDES:
            return
        a, b = g.members(prop)
        by_node = {v.node: v for v in self.rules_by_name.values()}  # type: ignore[attr-defined]
        if a in by_node and b in by_node:
            self.m.rules.overrides_rule(by_node[a], by_node[b])

    def _say(self, s: Statement) -> None:
        assert s.member is not None
        if s.channel not in self.channels:
            # Through `atom`, so a channel named in a rule and a channel
            # delivered on are the same node.
            self.channels[s.channel] = self.m.channels.use(self.atom(s.channel))
        scope: Dict[str, NodeId] = {}
        prop = self.build(s.member.term, scope)
        if self.m.g.has_var(prop):
            raise ParseError(f"line {s.line}: an arrival may not contain a variable")
        self.m.channels.deliver(self.channels[s.channel], prop, s.member.sign, s.member.grade)


def _mentions_a_rule(t: Term) -> bool:
    return t.is_rule or any(_mentions_a_rule(a) for a in t.args)


def _vars_in(g, node: NodeId) -> set:
    if g.is_var(node):
        return {node}
    out = set()
    for m in g.members(node):
        out |= _vars_in(g, m)
    return out


def load(machine: Machine, src: str) -> Loader:
    """Returns the loader, which is the corpus's name scope -- ask questions
    through it, since a bare name outside a scope names nothing."""
    ldr = Loader(machine)
    ldr.load(src)
    return ldr


def load_file(machine: Machine, path: str) -> Loader:
    with open(path, "r", encoding="utf-8") as fh:
        return load(machine, fh.read())
