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

    rule  boil = causes( { +heat(?a,?w), +water(?w) }, { +boiling(?w) } )
    fact  +on(a, b)                    standing knowledge, stamped source=kb
    say   user: +raining(here)         an arrival on the channel `user`
    fact  overrides(<boil>, <cool>)        an ordinary claim, and it seeds precedence
    fact  <no-harm> = forbidden(doing(harm(?x)))   a named statement
    fact  -<no-harm>                       ...which other statements can be about

A fact may carry a name, in the same angle brackets a rule's goes in, because
`<...>` is the namespace of **statements** and a rule is a statement. It earns its
place on descriptions: `forbidden(doing(harm(?x)))` contains variables, and §8
scopes a statement's variables to it, so writing it twice writes two nodes that
say a similar thing. A description has no identity but the one an author gives it,
and without a name a norm could be stated and never retired.

The notation is the design document's own, in ASCII: `-` for the minus sign it
writes as an en dash, `->` for its arrow. §8's worked rules parse as printed.
"""

import sys
from typing import Dict, List, NamedTuple, Optional, Tuple

from .chain import MINUS, PLUS, UNSURE
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
        if ch.isdigit():
            # Numerals. The design had no cardinal quantity until preference
            # strength became one, and a tolerance has to be writable in a
            # corpus. A numeral is an ordinary atom whose NAME reads as a
            # number, so nothing in the graph learns about arithmetic -- only
            # the one reader that wants it does.
            j = i
            while j < n and src[j].isdigit():
                j += 1
            toks.append(Tok("name", src[i:j], line))
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
    at: Optional[Term] = None


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
            # A fact may be NAMED, and the name goes in the same angle brackets a
            # rule's does, because it is the same namespace: names of
            # *statements*, kept out of the relation namespace.
            #
            # It earns its place on descriptions. `forbidden(doing(harm(?x)))`
            # contains variables, and §8 scopes a statement's variables to it --
            # so writing it twice writes two nodes that say a similar thing, and
            # a denial of the second leaves the first forbidding. A description
            # has no identity but the one the author gives it.
            name = ""
            if self.peek() is not None and self.peek().kind == "rulename":  # type: ignore[union-attr]
                name = self.next().text
                self.expect("=")
            return Statement("fact", name, "", (), (), self.member(), "", t.line)
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
        # ⚠ `@` is refused rather than ignored. It used to carry a GRADE, and
        # grades are gone: an uncertain conclusion is `+likely(p)`, an ordinary
        # proposition a rule can read. A corpus written against the old notation
        # is a corpus that means something this one no longer does, and §5 says
        # the silence is the defect -- so it is told, and told what to write.
        if self.at("@"):
            g = self.next() and self.next()
            raise ParseError(
                f"line {t.line}: `@` is gone with the grades. Uncertainty is a "
                f"proposition now -- write `+likely(p)` in the consequent and let "
                f"a rule cross it, rather than annotating how strongly `p` is held."
            )
        # ⭐ `+acts(goblin) at ?m` -- WHERE the entry sits. §12 calls the short
        # form an abbreviation for the entry, whose locus the frame supplies;
        # this is how a rule says otherwise, and it relates two moments.
        #
        # ⚠ Written out rather than punctuated. `@` used to mean a grade and is
        # now refused with a message (above); reusing it would be the island §2
        # warns about, on the page. A bare name here is unambiguous because a
        # member is followed by `,` or `}`.
        at = None
        if self.at("at"):
            self.next()
            at = self.term()
        return RuleMember(sign, term, at)

    def term(self) -> Term:
        t = self.next()
        if t.kind == "var":
            # ⭐ `?p(?t)` -- a variable in the RELATION slot. The substrate has
            # always been able to build one; `unify` learned to bind it, so the
            # surface stops being the thing that forbids it. This is what makes
            # *apply the effect named by this ability* one rule instead of one
            # fact per (ability, target) pair.
            if not self.at("("):
                return Term(t.text, (), True)
            self.next()
            args = [self.term()]
            while self.at(","):
                self.next()
                args.append(self.term())
            self.expect(")")
            return Term(t.text, tuple(args), True)
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

    def __init__(self, machine: Machine, scope: Optional[str] = None,
                 domain: Optional[str] = None) -> None:
        self.m = machine
        self.scope_name = scope
        # ⭐⭐⭐ **The name scope, and whether it is shared.** A corpus is a bound:
        # `kettle` means one node inside it, by construction and not by
        # inference, which is why coreference does not arise in authored
        # knowledge at all. What that cost, until now, is that two documents
        # could not be about the same kettle -- each `load` had a private table,
        # so a book split into chapters was forty disconnected islands and
        # nothing could bridge them.
        #
        # Naming the bound fixes it without weakening it. Documents loaded under
        # the same scope resolve names against one table, so identity is still
        # decided at intake and still by construction; documents under different
        # scopes stay apart, which is the default and is what a fresh corpus
        # wants.
        #
        # ⚠ Note what this deliberately does NOT do: assert identity in the
        # graph. `sameas(a, b)` would need equals-for-equals in matching, and
        # congruence is either machinery (a decision nobody can argue with) or a
        # rule per relation per position (combinatorial). Deciding identity when
        # the name is READ keeps it a construction. Identity discovered later is
        # then a revision of intake -- re-read the document with the binding
        # corrected -- which is the same shape `learned()` already has for rules.
        self.atoms: Dict[str, NodeId] = (
            {} if scope is None else machine.scopes.setdefault(scope, {})
        )
        self.vars: Dict[str, NodeId] = {}
        self.rule_nodes: Dict[str, NodeId] = {}
        self.rules_by_name: Dict[str, object] = {}
        # Names this corpus used in an ARGUMENT position that resolved to a
        # reserved node -- see `_note_shadow`. Collected rather than refused,
        # and surfaced by `load`, because the loader cannot tell an operator
        # from a sign and silence is what cost a foreign corpus a session.
        self.shadowed: set = set()
        self.channels: Dict[str, NodeId] = {}
        self.LOADED = self.m.LOADED   # the machine's node, never a fresh one
        # Every name the loader itself needs goes through the SAME table the
        # surface resolves against. A relation minted beside the table is a
        # second node with one name -- which is how `says` and `overrides` each
        # silently stopped matching what the surface wrote.
        self.atoms.update(self.m.reserved)
        # ⭐⭐ **A domain is a channel**, and that is the whole of what a domain
        # needs to be. §13 already says the knowledge base IS a channel; a named
        # scope refines it rather than adding a fourth concept, so a fact loaded
        # under `scope="billing"` is stamped as having come from billing and
        # provenance answers *which domain is this from* with nothing new.
        #
        # What it is FOR: deciding what is in mind. Measured before building --
        # three domains loaded, a goal in one of them, 23.5s and 600 ticks; the
        # same goal with only its own domain in mind, 1.6s and 198 ticks, and
        # **the identical 196 conclusions, none missing and none extra**. The
        # agent has always narrowed which RULES come to mind (`dormant`/`due`)
        # and has never narrowed which facts do.
        #
        # ⚠ Unscoped documents keep `kb`, which is what every corpus has had.
        # ⚠⚠⚠ **Sharing names and sharing provenance are DIFFERENT things**, and
        # tying them together was wrong -- caught by the first fixture that used
        # both. Rules about billing must resolve `owes` to the same node the
        # billing facts do, so they share a *scope*; but they are not billing
        # data, and unloading billing must not unload the rules that read it.
        # So a document declares its name table and its domain separately, and
        # `domain` defaults to `scope` because the simple case is one of each.
        which = domain if domain is not None else scope
        self.source = self.m.KB if which is None else self.m.channels.use(
            self.atom(which)
        )
        if scope is not None and not machine._booting:
            # A claim about this document, in the graph like everything else, so
            # that saving a session is a RENDERING rather than a side-channel.
            self._scoped(self.source, scope)
        self.OVERRIDES = self.atom("overrides")
        self.SUPERSEDES = self.atom("supersedes")
        # The bundle, by name. Every section of the design that says *a corpus
        # can override this* depended on it and none of it was true: the loader
        # knew only the names a corpus had declared itself, so `<assert-act>`,
        # `<give-up>` and the rest were unnameable and therefore unarguable --
        # shipped as data and reachable only from Python.
        #
        # One table, so a corpus rule may not reuse a bundled name. That is the
        # marker doing its job: two statements with one name is what `<...>`
        # exists to prevent.
        for r in self.m.bundle:
            self.rule_nodes[r.name] = r.node
            self.rules_by_name[r.name] = r
            self.m.g.call_it(r.node, f"<{r.name}>")
        # Tools, by name, for the same reason and in the same table. `<...>` is
        # the namespace of STATEMENTS and a tool is something statements are
        # about -- a corpus writes `-answers(<oracle>, guess)` to retire one and
        # `+answered(<oracle>, ...)` to trust one, and neither is writable if the
        # name does not resolve. One table, so a tool and a rule cannot share a
        # name and mean different things depending on where they were written.
        for a in self.m.answerers:
            self.rule_nodes[a.name] = a.node
            self.rules_by_name[a.name] = a

    def _scoped(self, node: NodeId, scope: str) -> None:
        """*This name was resolved in that table.* Deduped by READING the graph
        rather than by a Python set beside it -- restating a claim adds nothing
        (§8), and a second set of bookkeeping is exactly the thing this commit
        exists to stop adding."""
        prop = self.m.g.rel(self.m.SCOPED, node, self.atom(scope))
        if self.m._claims(prop):
            return
        self.m.gate.write(
            self.m.focus, prop, "+",
            licence=self.m.g.rel(self.m.REIFIED, node),
            source=self.source, mention=True,
        )

    def say(self, channel: str, text: str, sign: str = "+") -> NodeId:
        """The world speaks, **in this corpus's scope** -- the scoped door for
        arrivals, beside `channel` and `answerer`.

        It also records which scope the term was written in, which is what lets
        a saved session be replayed into the same nodes rather than into twins
        that merely print the same.
        """
        node, prop = self.channel(channel), self.term(text)
        self.m._saying_scope = self.scope_name
        try:
            self.m.channels.deliver(node, prop, sign)
        finally:
            self.m._saying_scope = None
        return prop

    def channel(self, name: str) -> NodeId:
        """Open a channel **in this corpus's scope**, which is the only scope in
        which its name means anything.

        `Machine.channels.open("user")` mints a node beside whatever table the
        corpus resolves against, so the rule reading `says(user, ...)` and the
        socket the world speaks on are two sockets with one name -- silently.
        That is the twin trap, and it is the same door `answerer` opens for a
        tool's request: anything that binds a name goes through the table that
        resolves it.
        """
        node = self.m.channels.use(self.atom(name))
        self.channels[name] = node
        if self.scope_name is not None:
            # ...and which table its name was resolved in, so an arrival on it
            # replays into the same node rather than a twin that prints alike.
            self._scoped(node, self.scope_name)
        return node

    def answerer(self, name: str, request: str, fn):
        """Register a tool **in this corpus's scope**, which is the only scope in
        which its request has a meaning.

        A tool answers a request, a request is a relation, and a relation is a
        name -- and names are not identity here. Registering `oracle` to answer
        `guess` through `Machine.answerer` mints a *second* `guess` beside the one
        the corpus will write, so the tool sits waiting for a request nobody can
        make. Measured, and it is the same twin the bundle's vocabulary turned up
        an hour earlier: **anything that binds a name has to go through the table
        that resolves it.**

        Registered before `load`, because a rule may name the tool (`<oracle>`)
        and `<...>` is resolved at authoring.

        `fn(machine, frame, entry)` returns the answer node, or `None` for *I
        have nothing to say*. ⚠ Said here as well as on `Machine.answerer`
        because this is the door the note above tells everyone to use, and a
        reader who never opens the other one has no way to learn the arity from
        the one they are told to call.
        """
        # ⚠⚠⚠ **The apparatus must not be joined on its own requests, and this
        # was found by the apparatus squatting on a name a fixture already
        # used.** `_answer` calls EVERY answerer bound to a relation, so a
        # corpus tool registered on `compose` and the apparatus's own composer
        # both fire on every such write -- and they coexisted only because each
        # declined the other's arity, which is coincidence, not design.
        #
        # It is the twin trap inverted: not two nodes for one name, but two
        # answerers for one node. The consequence is worse than a twin, because
        # a tool PROPOSES and the apparatus CONCLUDES (§19), so the collision
        # silently gives a corpus's tool a share of a request whose answer the
        # agent acts on directly.
        #
        # Refused at registration, which is where the claim is made and the only
        # moment the caller is looking at it -- the same argument the arity check
        # beside this one is made from.
        rel = self.atom(request)
        taken = [x.name for x in self.m.answerers if x.request is rel]
        if taken:
            raise ParseError(
                f"{request!r} is already answered by {', '.join(sorted(taken))} -- "
                f"a corpus tool may not share a request relation with the "
                f"apparatus; choose a request name of your own"
            )
        a = self.m.answerer(name, rel, fn)
        if name in self.rule_nodes:
            raise ParseError(f"<{name}> is already declared -- a tool and a rule "
                             f"cannot share a name (see `rule_ref`)")
        self.rule_nodes[name] = a.node
        self.rules_by_name[name] = a
        return a

    def rule_ref(self, name: str) -> NodeId:
        """What `<n>` denotes: a rule node, or a named fact's proposition.

        One table, because `<...>` names statements and a rule is a statement.
        Two tables would let a rule and a norm share a name and mean different
        things depending on where they were written -- two things with one name,
        which is the mistake the marker exists to prevent.
        """
        if name not in self.rule_nodes:
            raise ParseError(
                f"no statement named <{name}> was declared -- or it is a fact "
                f"declared after the one referring to it, which the loader "
                f"cannot resolve (see `load`)"
            )
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

    def _note_shadow(self, t: Term) -> None:
        """A bare name in an ARGUMENT position that resolves to a reserved node.

        ⚠⚠⚠ **One node with two meanings, which is the twin trap inverted.**
        `reserved` binds `plus`/`minus` to the SIGN atoms and every corpus's
        table is seeded from it, so a domain author writing an arithmetic
        operator gets the sign: `calc(minus, 5, 2)` lands as `calc(-, 5, 2)`,
        the tool declines a request it should have answered, and the run stalls
        with nothing saying why. Reported from a foreign corpus, which lost a
        debugging session to it.

        It is a **report and not a refusal**, and that is forced rather than
        timid: `+expects(?p, plus)` and `+says(user, ?p, plus)` are legitimate
        and there are twenty-odd of them, so the loader cannot tell an operator
        from a sign. What it can do is stop being silent -- which is §5's rule
        about the places machinery declines without saying so, arriving at the
        one place a name changes meaning under the author's feet.
        """
        if t.is_rule or t.is_var or t.args or t.head.isdigit():
            return
        # ⚠ Numerals are excluded deliberately, and the exclusion is the whole
        # difference between a diagnostic and noise. `cost(sword, 3)` SHOULD
        # resolve to the numeral the machinery uses -- that is sharing, not
        # shadowing. What traps a domain author is a reserved name that reads
        # like ordinary domain vocabulary, and the first version of this flagged
        # every integer in every corpus, which is how a message gets ignored.
        if self.atom(t.head) in set(self.m.reserved.values()):
            self.shadowed.add(t.head)

    def build(self, t: Term, scope: Dict[str, NodeId]) -> NodeId:
        if t.is_rule:
            return self.rule_ref(t.head)
        if t.is_var:
            v = self.var(t.head, scope)
            # A variable with arguments is a relation instance whose relation is
            # that variable -- `?p(?t)`. Without this it would silently drop the
            # arguments and bind the bare variable, which is the shape of every
            # twin this repo has recorded.
            if t.args:
                for a in t.args:
                    self._note_shadow(a)
                return self.m.g.rel(v, *[self.build(a, scope) for a in t.args])
            return v
        if not t.args:
            return self.atom(t.head)
        for a in t.args:
            self._note_shadow(a)
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
        named = [s for s in statements if s.kind == "fact" and s.name]

        # Three passes, and the order is forced rather than chosen. A rule may
        # conclude about a named fact (`{-<no-harm>}` retires a norm), and a
        # named fact may be about a rule (`overrides(<a>, <b>)`), so neither can
        # simply come first. What breaks the cycle is that a name only needs its
        # NODE to be resolvable, and a statement that refers to no other
        # statement can be built without one.
        for s in named:
            if not _mentions_a_rule(s.member.term):  # type: ignore[union-attr]
                self._name(s)
        for s in statements:
            if s.kind == "rule":
                self._rule(s)
        for s in named:
            if s.name not in self.rule_nodes:
                self._name(s)

        # Then everything is written, in the order it was authored -- so a
        # corpus that states a norm and then retires it does so in that order.
        for s in statements:
            if s.kind == "fact":
                self._fact(s)
            elif s.kind == "say":
                self._say(s)
        return statements

    def _name(self, s: Statement) -> None:
        """Build a named fact's proposition ONCE, and register the name.

        Once, because building it twice would mint fresh variables and produce a
        second node -- which is the very failure naming exists to prevent.
        """
        assert s.member is not None
        if s.name in self.rule_nodes:
            raise ParseError(f"line {s.line}: <{s.name}> is already declared")
        self.rule_nodes[s.name] = self.build(s.member.term, {})

    def _rule(self, s: Statement) -> None:
        if s.name in self.rule_nodes:
            raise ParseError(f"line {s.line}: <{s.name}> is already declared")
        scope: Dict[str, NodeId] = {}
        ant = [Member(m.sign, self.build(m.term, scope),
                      self.build(m.at, scope) if m.at else None)
               for m in s.antecedent]
        con = [Member(m.sign, self.build(m.term, scope),
                      self.build(m.at, scope) if m.at else None)
               for m in s.consequent]
        # A consequent that NAMES a rule drags that rule's own variables in with
        # it: `+resume(?h, <cb>)` is generic only because `<cb>`'s patterns are.
        # Those are mentioned, not used, and no antecedent can or should bind
        # them -- so they are exempt, and every other variable is still checked.
        unbound = [
            m
            for m, written in zip(con, s.consequent)
            if (self.m.g.has_var(m.pattern)
                and not self._covered(m.pattern, ant,
                                      self._named_rule_vars(written.term)))
            or (m.locus is not None and self.m.g.has_var(m.locus)
                and not self._covered(m.locus, ant))
        ]
        if unbound:
            raise ParseError(
                f"line {s.line}: rule {s.name!r} concludes about a variable its antecedent "
                f"never binds -- the gate would refuse to deposit it (§13)."
            )
        r = self.m.rules.rule(s.connective, ant, con, s.name)
        # The same `<...>` marker `_fact` reads, one level up: a rule authored
        # naming a rule is mentioning, and everything it concludes inherits that.
        #
        # The CONSEQUENT only. An antecedent that names a rule needs nothing: it
        # matches an entry that was already written as a mention, and §14's
        # propagation carries it. Flagging that case too would be broader than
        # the evidence for it.
        r.mentions = any(_mentions_a_rule(m.term) for m in s.consequent)
        self.rules_by_name[s.name] = r
        self.rule_nodes[s.name] = r.node
        # ...and so it PRINTS as its name. A rule is minted as
        # `implies(moment(...), moment(...))` and appeared that way in every plan
        # node, licence and `unmet` -- ninety characters of its own structure
        # where the author had written `<boil>`. §2's readable criterion, failing
        # in the one place a person actually looks.
        self.m.g.call_it(r.node, f"<{s.name}>")

    def _covered(self, pattern: NodeId, ant: List[Member], exempt: set = frozenset()) -> bool:
        g = self.m.g
        wanted = _vars_in(g, pattern) - set(exempt)
        have = set()
        for m in ant:
            have |= _vars_in(g, m.pattern)
            # ⚠ A locus variable IS bound by the antecedent -- `+p(?x) at ?m`
            # binds `?m` from the entry that matched. Without this the check
            # rejects every rule that relates two moments, which is the whole
            # point of the slot.
            if m.locus is not None:
                have |= _vars_in(g, m.locus)
        return wanted <= have

    def _named_rule_vars(self, t: Term) -> set:
        """The variables a term inherits purely by naming a rule."""
        out: set = set()
        if t.is_rule:
            out |= _vars_in(self.m.g, self.rule_ref(t.head))
        for a in t.args:
            out |= self._named_rule_vars(a)
        return out

    def _fact(self, s: Statement) -> None:
        assert s.member is not None
        scope: Dict[str, NodeId] = {}
        # A named fact was built when its name was registered, and it must not be
        # built again: a second build mints fresh variables and a second node.
        prop = self.rule_nodes[s.name] if s.name else self.build(s.member.term, scope)
        # A fact that NAMES a rule is mentioning it, and a rule node contains the
        # variables of its own patterns. `overrides(<why>, <boil>)` is a ground
        # claim about two rules, not a generic claim -- R3 depends on being able
        # to write it. The `<...>` marker is what makes the distinction visible
        # here, where structurally the two are identical (§13).
        # A norm's argument is a DESCRIPTION, not a proposition:
        # `forbidden(doing(harm(?x)))` names a class of acts, exactly as
        # `ant(<R>, heat(?a, ?w))` names a class of premises. Both are ground
        # claims that happen to contain variables, and §13 says what tells them
        # apart is who is writing -- here, an author who wrote `forbidden`.
        #
        # This is one name in Appendix C's census, and it is the honest price of
        # letting a corpus state a norm at all: a norm about one act would be
        # useless, and a norm expressed as a rule is a competitor in recall.
        mentions = (
            _mentions_a_rule(s.member.term)
            or s.member.term.head == "forbidden"
            or bool(s.name)  # a named statement is one you can be about
        )
        if not mentions and self.m.g.has_var(prop):
            raise ParseError(
                f"line {s.line}: a fact may not contain a variable -- only a rule's members "
                f"are generic (§4)."
            )
        self.m.gate.write(
            self.m.focus,
            prop,
            s.member.sign,
            licence=self.m.g.rel(self.LOADED, prop),
            source=self.source,
            mention=mentions,
        )

    # `_maybe_precedence` was here: it read `overrides(A, B)` off a statement as
    # the loader parsed it and seeded §14's precedence table. It is gone, and
    # `Machine._precede` does it from the WRITE instead -- so a precedence a
    # rule concludes counts, a precedence a rule denies is withdrawn, and a
    # rule adopted at runtime can be ordered against anything. Doing both was
    # the bug that found this: the pair went into the table twice, and one
    # denial took out one copy.

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
        self.m.channels.deliver(self.channels[s.channel], prop, s.member.sign)


def _mentions_a_rule(t: Term) -> bool:
    return t.is_rule or any(_mentions_a_rule(a) for a in t.args)


def _vars_in(g, node: NodeId) -> set:
    if g.is_var(node):
        return {node}
    out = set()
    for m in g.members(node):
        out |= _vars_in(g, m)
    return out


def _report_shadowed(ldr: "Loader") -> None:
    """Say when a corpus's name meant something the corpus did not choose.

    Not an exception: `+expects(?p, plus)` is legitimate and there are twenty of
    them. Not silence either -- that is the failure being repaired. The author
    is looking at the load, so the load is where it is said.
    """
    # ...and not while the machine is still installing its own bundle, which
    # uses `plus` and `minus` as signs on purpose.
    if not ldr.shadowed or getattr(ldr.m, "_booting", False):
        return
    names = ", ".join(sorted(ldr.shadowed))
    print(f"note: {names} name reserved nodes, so an argument written with one "
          f"is that node and not a fresh atom of yours -- rename if you meant "
          f"your own (see Appendix C)", file=sys.stderr)


def load(machine: Machine, src: str, scope: Optional[str] = None,
         domain: Optional[str] = None) -> Loader:
    """Returns the loader, which is the corpus's name scope -- ask questions
    through it, since a bare name outside a scope names nothing.

    `scope` names a table shared with every other document loaded under it, so
    two documents can be about the same kettle. Omitted, the document gets a
    private table, which is what it has always had.

    `domain` is what its facts are stamped as coming FROM -- the channel that
    provenance records and that `dormant` takes out of mind. It defaults to
    `scope`, because the simple case is one domain per name table; give it
    separately when several documents share names and must be unloadable apart,
    which rules and the facts they read always must.
    """
    ldr = Loader(machine, scope, domain)
    machine._authoring_source = ldr.source
    try:
        ldr.load(src)
    finally:
        machine._authoring_source = None
    _report_shadowed(ldr)
    # What the agent was told, in order (see `Machine.save`). Recorded here
    # rather than in `Loader`, so that a corpus loaded as part of a REPLAY is
    # not journalled a second time.
    return ldr


def load_file(machine: Machine, path: str, scope: Optional[str] = None,
              domain: Optional[str] = None) -> Loader:
    with open(path, "r", encoding="utf-8") as fh:
        return load(machine, fh.read(), scope, domain)
