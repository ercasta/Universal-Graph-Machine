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
from .rules import CAUSES, IMPLIES, STOP, UNATTEND, Attend, Member

SIGNS = {"+": PLUS, "-": MINUS, "?": UNSURE}


class ParseError(Exception):
    pass


# -- tokenising -------------------------------------------------------------


class Tok(NamedTuple):
    kind: str  # name | var | punct
    text: str
    line: int


_PUNCT = set("(){},=:@+-?>")
# `>` is punctuation only as the second half of `=>`, which is what a
# postcondition's arrow is. `<` never reaches here -- it opens a rule name.

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
    unresolved against a graph.

    ⭐ `fn` is the relation slot when it holds a whole TERM rather than a name --
    `a(b)(c)`, the node whose relation is `a(b)`. The substrate has always built
    one (a node's relation is a node like any other, and `show` renders it by
    recursing), `unify` learned to compare one when `?p(?t)` landed, and this is
    the last component that could not read it.

    ⚠ Set only for a CHAINED application, so every term that parsed before this
    existed still parses to the identical shape. `a(b)` is `Term("a", (b,))` as
    it always was, not `Term("", (b,), fn=Term("a"))` -- which matters because
    `_fact` reads `term.head == "forbidden"` to spot a norm, and rewriting the
    common case would have moved that head one level down and retired every norm
    in the suite silently.
    """

    head: str
    args: Tuple["Term", ...]
    is_var: bool
    is_rule: bool = False
    fn: Optional["Term"] = None
    # ⭐ `+person` in an ARGUMENT: introduce one. `+` already signals a node
    # coming to be -- asserting `+p(x)` is what builds `p(x)` -- so this is that
    # mark one level down rather than a second meaning for it. `member` consumes
    # the member-level sign before `term` is ever called, so the two cannot
    # shadow each other.
    mint: bool = False


class RuleMember(NamedTuple):
    sign: str
    term: Term
    at: Optional[Term] = None
    binds: Optional[Term] = None


class PostClause(NamedTuple):
    """A postcondition, as written: a query, and what it spends if it holds.

        rule <classify> = implies( { +asked(?x) }, { +considered(?x) } )
          after { +penguin(?x) } => attend(?x, 3)
          frozen after => unattend

    The query is an ordinary antecedent -- no new notation, and the same
    matcher -- and it is matched with the rule's OWN bindings already in hand,
    so `?x` above is the `?x` the rule bound. A bare `after` is the query that
    asks nothing and always holds.

    `frozen` marks what a calibration process may not touch, and `learned` its
    complement -- what play added rather than what a person wrote. Neither
    changes how the postcondition RUNS, which is the point: an authored lesson
    and a learned one are the same construct, and only the learner treats them
    differently.

    ⭐⭐⭐ **Three provenance levels over one mechanism**, and they are what make
    the learned half separable:

        frozen      the machinery may not touch this
        (plain)     a person wrote it
        learned     play added it, and re-learning may replace it

    ⚠ And learning ADJUSTS rather than replaces, which needs no arithmetic at
    all: two postconditions on one rule both spend, so an authored `attend(?x)`
    beside a learned `attend(?y)` leaves the agent thinking about both. Measured.
    Strip every `learned` line and the bootstrap is exactly what is left.
    """

    query: Tuple[RuleMember, ...]
    spends: Tuple[Tuple["Term", int], ...]
    frozen: bool
    learned: bool = False


class Statement(NamedTuple):
    kind: str  # rule | fact | say
    name: str
    connective: str
    antecedent: Tuple[RuleMember, ...]
    consequent: Tuple[RuleMember, ...]
    member: Optional[RuleMember]
    channel: str
    line: int
    posts: Tuple[PostClause, ...] = ()


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
        if t.text == "expert":
            # ⭐ Which expert the rules below belong to, and optionally which
            # other expert's rules it inherits:
            #
            #     expert geometry
            #     expert geometry extends arithmetic
            #
            # It declares nothing the surface could not already write --
            # `knows(geometry, <R>)` and `extends(geometry, arithmetic)` are
            # ordinary facts, and staying ordinary facts is what makes *which
            # rules does this expert have* an ordinary query (R4). What the
            # keyword buys is not having to name every rule twice.
            name = self.next()
            if name.kind != "name":
                raise ParseError(
                    f"line {name.line}: `expert` names an expert, and an expert "
                    f"is an ordinary atom rather than a statement -- so it is "
                    f"written without angle brackets"
                )
            base = ""
            nxt = self.peek()
            if nxt is not None and nxt.kind == "name" and nxt.text == "extends":
                self.next()
                b = self.next()
                if b.kind != "name":
                    raise ParseError(
                        f"line {b.line}: `extends` names the expert whose rules "
                        f"are inherited"
                    )
                base = b.text
            return Statement("expert", name.text, base, (), (), None, "", t.line)
        if t.text == "action":
            # ⭐⭐⭐ **The action palette, declared:**
            #
            #     action move(?x, ?y)
            #
            # A SIGNATURE and nothing else. It says what the agent may ask to
            # do; the world model's own rules say what happens when it asks, and
            # one of them may refuse. Keeping those apart is the point: an
            # illegal request that merely fails to match is silence, and this
            # design's standing complaint is that silence reads as a corpus bug.
            #
            # ⚠ No angle brackets. `<...>` names STATEMENTS, and an action is
            # not a statement -- it is a term the agent may deposit, so it is
            # named the way a relation instance is named, by being written.
            return Statement("action", "", "", (), (), self.member(), "", t.line)
        if t.text in ("after", "frozen", "learned", "when"):
            # A trigger, and it stands on its own: what a rule MEANS and what
            # experience has learned about when to reach for it are different
            # kinds of claim, kept in different documents. A corpus loads its
            # experience or does not.
            return self.trigger(t)
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
        if t.text == "lisp" and self.at(":"):
            # One statement in the other notation, inside an ordinary document.
            # The TOKEN STREAM is shared, so the s-expression reader picks up at
            # this position and hands back where it stopped -- no re-tokenising,
            # and no second place for `?x` to stop meaning a variable.
            self.next()
            from .sexpr import read_one
            stmt, self.i = read_one(self.toks, self.i)
            return stmt
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
        return Statement("rule", name_tok.text, conn.text, ant, con, None, "",
                         line)

    def trigger(self, t: Tok) -> Statement:
        """`after <A> { ... } => attend(?x, 3)`.

        `after` fires when its rule applies and its query holds. `frozen` marks
        what a calibration process may not touch.

        ⚠⚠⚠ **`when` IS REFUSED, and that is a change from a silent no-op.** A
        `when` trigger fired at RANKING time and belonged to no rule; the only
        thing that ran one was `_rerank`, which reordered a shortlist by the
        buffs the trigger spent. Both are retired, so a `when` trigger now
        reaches nothing at all -- it would parse, load, and never run. A corpus
        whose lesson silently does nothing is the worst outcome available here,
        so it is an error instead. Everything a reranker could say, an `after`
        trigger on the rule that RAN can say, and it says it about a move that
        actually happened.
        """
        frozen = t.text == "frozen"
        learned = t.text == "learned"
        if frozen or learned:
            nxt = self.peek()
            if nxt is None or nxt.text not in ("after", "when"):
                raise ParseError(
                    f"line {t.line}: `{t.text}` marks a trigger, so it is "
                    f"written `{t.text} after <R> ... => ...`"
                )
            t = self.next()
        if t.text == "when":
            raise ParseError(
                f"line {t.line}: a ranking-time `when` trigger no longer reaches "
                f"anything -- `_rerank` and the buffs it spent are retired. Hang "
                f"the lesson off the rule that RUNS it: `after <R> {{ ... }} => "
                f"attend(?x, n)`"
            )
        host = ""
        if t.text == "after":
            name = self.next()
            if name.kind != "rulename":
                raise ParseError(
                    f"line {name.line}: `after` says which rule it follows, in "
                    f"the angle brackets a rule is named in"
                )
            host = name.text
        query = self.block() if self.at("{") else ()
        self.expect("=")
        self.expect(">")
        spends = [self.spend()]
        while self.at(","):
            self.next()
            spends.append(self.spend())
        return Statement("trigger", host, "", query, (), None, "", t.line,
                         (PostClause(query, tuple(spends), frozen, learned),))

    def spend(self) -> Tuple["Term", int]:
        """What a postcondition spends: `attend(...)`, `unattend` or `stop`.

        ⚠⚠⚠ **`boost(<R>, n)` AND `damp(<R>, n)` ARE GONE, AND SO IS `reset`.**
        They named a RULE, which is what the whole retirement is about: a rule
        id goes stale the moment a rule is adopted, composed or renamed, and a
        corpus of experience written in them stops loading rather than going
        quietly wrong. `attend(?x, n)` names a NODE the move itself bound.

        ⚠ The delta in the return type is now always 0 and is kept only so the
        three surviving spends share one shape. Nothing reads it.
        """
        t = self.next()
        if t.kind == "name" and t.text == "stop":
            # ⭐ *Done is the output of a rule that checks against the goal* --
            # which the table loop's own design says, and had no way to obey.
            # A rule concludes that here is over; its postcondition is what
            # ends the run. The loop still knows nothing about goals: it knows
            # a rule spent attention by saying stop.
            return (STOP, 0)
        if t.kind == "name" and t.text == "unattend":
            # `reset` for attention: the agent stops thinking about what it was
            # thinking about. A denial rather than a forgetting, so it stays
            # readable and arguable -- and something has to say it, or attention
            # accumulates until it names everything.
            return (UNATTEND, 0)
        if t.kind == "name" and t.text == "attend":
            # ⭐⭐⭐ **The learnable one.** `attend(?x)` says *think about what
            # this move just bound to `?x`* -- and `?x` is the HOST RULE's own
            # variable, because the loader seeds a trigger's scope from the rule
            # it hangs off. So the lesson is anchored to the move that produced
            # it without naming any individual.
            self.expect("(")
            target = self.term()
            weight = 1
            if self.at(","):
                # ⭐ The learned buff, and it weighs a NODE rather than a rule.
                # `attend(?x, 3)` says *of what this move touched, that one
                # matters* -- a multiplier on its place in the attention queue.
                self.next()
                n = self.next()
                if not n.text.isdigit():
                    raise ParseError(
                        f"line {n.line}: how much to attend is a numeral")
                weight = int(n.text)
            self.expect(")")
            return (Attend(target, weight), 0)
        raise ParseError(
            f"line {t.line}: a postcondition spends attention, so it says "
            f"`attend(...)`, `unattend` or `stop`, not {t.text!r}"
        )

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
        at = binds = None
        # `at ?m` -- WHERE the entry sits. `as ?t` -- WHAT it says, named.
        # Either order, because neither reads as the other and an author should
        # not have to remember which came first.
        while True:
            if self.at("at"):
                self.next(); at = self.term()
            elif self.at("as"):
                self.next(); binds = self.term()
            else:
                break
        return RuleMember(sign, term, at, binds)

    def term(self) -> Term:
        """A primary, then any number of further argument groups applied to it.

        `a(b)(c)` is *a composed with b, applied to c* -- a different node from
        `a(b(c))`, and the difference is which node the top one's RELATION edge
        points at: an atom, or a structure. Both were buildable and renderable;
        only this loop was missing.
        """
        t = self.primary()
        while self.at("("):
            self.next()
            args = [self.term()]
            while self.at(","):
                self.next()
                args.append(self.term())
            self.expect(")")
            t = Term("", tuple(args), False, False, fn=t)
        return t

    def primary(self) -> Term:
        if self.at("+"):
            # Reached only from inside a term, because `member` has already
            # taken any member-level sign.
            self.next()
            inner = self.primary()
            return inner._replace(mint=True)
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

    def computator(self, name: str, fn):
        """Register a computator in THIS corpus's scope (see `Machine`).

        Values in, a value out, and no access to anything -- so a corpus rule
        may use it inside an antecedent and the whole application stays atomic.

        ⚠⚠⚠ **The result is resolved in THIS corpus's table**, which is the whole
        reason the marshalling lives here rather than in the matcher. A value
        turned into a node with `g.atom` is a fresh node, so `8` computed would
        be a twin of the `8` the corpus writes: the rule fires, the fact lands,
        and every question about it answers nothing. `Loader.answerer`'s
        argument, one door along.
        """
        def resolved(*values):
            got = fn(*values)
            return None if got is None else self.atom(str(got))
        return self.m.computator(self.atom(name), resolved)

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

    def _trigger(self, s: Statement) -> None:
        """A trigger, built in its HOST RULE's variable scope.

        That is the whole of why this can move out of the rule declaration
        without changing what it means: an inline `after` clause shared the
        rule's scope because it was parsed inside the same statement, and here
        the scope is handed to it instead. `?x` in the trigger is the rule's
        `?x`, so the query still says *this orc* rather than *some orc*.

        A name a rule does not use is an ordinary fresh variable, bound from the
        state like any other -- which is what a `when` trigger, belonging to no
        rule, has for all of them.
        """
        clause = s.posts[0]
        host = None
        scope: Dict[str, NodeId] = {}
        if s.name:
            host = self.rules_by_name.get(s.name)
            if host is None:
                raise ParseError(
                    f"line {s.line}: `after <{s.name}>` names a rule that was "
                    f"not declared -- or one declared after it, which the "
                    f"loader cannot resolve"
                )
            for m in list(host.antecedent) + list(host.consequent):
                for v in _vars_in(self.m.g, m.pattern):
                    scope.setdefault(self.m.g.show(v), v)
        query = tuple(
            Member(mm.sign, self.build(mm.term, scope),
                   self.build(mm.at, scope) if mm.at else None,
                   self.build(mm.binds, scope) if mm.binds else None)
            for mm in clause.query
        )
        spends = tuple(
            # `STOP` is a stop and `UNATTEND` a clearing; neither is a term, so
            # neither goes through `build`. An `attend` IS one, and it is built
            # in the host rule's scope like everything else here -- which is what
            # makes `attend(?x)` *that* `?x`.
            (t if t is STOP or t is UNATTEND
             else Attend(self.build(t.term, scope), t.weight), delta)
            for t, delta in clause.spends
        )
        self.m.rules.triggers.setdefault(
            None if host is None else host.node, []
        ).append((query, spends, clause.frozen, clause.learned))

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
            # ⚠⚠⚠ **A NUMERAL is not this document's name for something.** Two
            # corpora may be about different kettles and are never about
            # different 2s. `Machine.NUMERAL` already says so and `reserved`
            # already seeds this table from it -- but `reserved` is a snapshot
            # taken at boot and it stops at nine, so `12` fell through to
            # `g.atom` and minted a node per document. Nothing had computed a
            # numeral before, so nothing had noticed; `_count` computes one, and
            # a count of twelve would have been a twin of every authored 12.
            # The twin trap, seventh time, and the same answer as the other six.
            self.atoms[name] = (
                self.m._numeral(int(name)) if name.isdigit()
                else self.m.g.atom(name)
            )
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
        if t.mint:
            # ⚠ Wrapped in the machine's OWN node, never one from the name
            # table -- so `new` stays a word a corpus may mean something else
            # by. That is the whole reason this is a mark and not a keyword:
            # `ugm.vocabulary` counts every name the engine takes, and `new` is
            # too ordinary a word to spend.
            return self.m.g.rel(self.m.NEW, self.build(t._replace(mint=False), scope))
        if t.fn is not None:
            # The relation slot holds a term. `g.rel` interns on
            # (relation, members) as always, so `a(b)(c)` is one node however
            # often it is written, and a different one from `a(b(c))`.
            return self.m.g.rel(
                self.build(t.fn, scope), *[self.build(a, scope) for a in t.args]
            )
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

        ⚠⚠⚠ **It refuses leftovers, and until a foreign corpus reported it, it
        did not.** `term("a b")` returned `a` and `term("a(b) junk here")`
        returned `a(b)`, silently -- one term parsed and the rest of the string
        dropped. The `fact` and `rule` paths refuse loudly; this one did not, and
        this one is what `Loader.say` uses. So **an agent could say one thing and
        the hearer believe another**, with nothing anywhere reporting a
        difference (`docs/quest-feedback.md` §5).

        That is worse than a parse error, because a truncation is still a valid
        term: it fails as a **wrong answer** rather than as a crash, which this
        repository has recorded as its most expensive failure shape.
        """
        toks = tokenise(src)
        p = Parser(toks)
        t = p.term()
        if p.peek() is not None:
            rest = " ".join(x.text for x in toks[p.i:])
            raise ParseError(
                f"a term and then {rest!r} -- `term` reads ONE term, and "
                f"silently dropping the rest would let a caller believe "
                f"something other than what it was given"
            )
        return self.build(t, {})

    def load(self, src: str) -> List[Statement]:
        # A second SURFACE, not a second language (see `ugm/sexpr.py`). The
        # graph is the truth and a notation is a way of writing it down, so the
        # reader is chosen here and nothing downstream -- `build`, the name
        # scope, the gate -- learns which notation a node was authored in.
        #
        # ⚠ Imported lazily and only when a marker is present, so a document
        # with no marker takes exactly the path it always did.
        if "syntax:" in src:
            from . import sexpr
            if sexpr.wants_lisp(src):
                statements = sexpr.read(src)
            else:
                statements = Parser(tokenise(src)).program()
        else:
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
        # Which expert owns what. Read in authored order and applied to the
        # rules that follow the declaration, so a file reads top to bottom.
        owner: Dict[str, str] = {}
        current = ""
        for s in statements:
            if s.kind == "expert":
                current = s.name
                if s.connective:
                    self._expert_extends(s.name, s.connective)
            elif s.kind == "rule" and current:
                owner[s.name] = current
        for s in statements:
            if s.kind == "rule":
                self._rule(s)
                if s.name in owner:
                    self._expert_knows(owner[s.name], s.name)
        for s in named:
            if s.name not in self.rule_nodes:
                self._name(s)
        # Triggers last: they name rules, and a rule must exist to be reached
        # for. Same reason the named facts are split around the rules.
        for s in statements:
            if s.kind == "trigger":
                self._trigger(s)

        # Then everything is written, in the order it was authored -- so a
        # corpus that states a norm and then retires it does so in that order.
        for s in statements:
            if s.kind == "fact":
                self._fact(s)
            elif s.kind == "say":
                self._say(s)
            elif s.kind == "action":
                self._action(s)
        return statements

    def _action(self, s: Statement) -> None:
        """Declare an action, and put it in the graph where a rule can find it.

        ⚠⚠⚠ **Mentioned, not claimed.** `move(?x, ?y)` is generic and the gate
        refuses to deposit a proposition with a variable in it -- correctly, and
        `a_rule_can_introduce_a_thing` is the same wall from the other side. So
        what is deposited is `action(move(?x, ?y))`, a claim ABOUT a pattern,
        exactly as `reify` deposits `ant(<R>, heat(?a, ?w))`.

        ⭐ Which is what makes the palette DISCOVERABLE: `+action(?a)` is an
        ordinary premise, so one fallback rule can range over every action --
        including ones declared after it was written. Without the declaration a
        corpus needs one hand-written fallback per action, and a new action is a
        fallback nobody remembers to add.
        """
        assert s.member is not None
        scope: Dict[str, NodeId] = {}
        term = self.build(s.member.term, scope)
        self.m._note(self.m.g.rel(self.m.AFFORDED, term))

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
                      self.build(m.at, scope) if m.at else None,
                      self.build(m.binds, scope) if m.binds else None)
               for m in s.antecedent]
        con = [Member(m.sign, self.build(m.term, scope),
                      self.build(m.at, scope) if m.at else None,
                      self.build(m.binds, scope) if m.binds else None)
               for m in s.consequent]
        # A consequent that NAMES a rule drags that rule's own variables in with
        # it: `+resume(?h, <cb>)` is generic only because `<cb>`'s patterns are.
        # Those are mentioned, not used, and no antecedent can or should bind
        # them -- so they are exempt, and every other variable is still checked.
        unbound = [
            m
            for m, written in zip(con, s.consequent)
            if (self.m.g.has_var(m.pattern)
                and not _describes(written.term)
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
        r.mentions = any(_mentions_a_rule(m.term) or _describes(m.term)
                         for m in s.consequent)
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
            if m.binds is not None:
                have |= _vars_in(g, m.binds)
        return wanted <= have

    def _named_rule_vars(self, t: Term) -> set:
        """The variables a term inherits purely by naming a rule."""
        out: set = set()
        if t.is_rule:
            out |= _vars_in(self.m.g, self.rule_ref(t.head))
        if t.fn is not None:
            out |= self._named_rule_vars(t.fn)
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
            or _describes(s.member.term)
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

    def _expert_fact(self, rel: str, a: NodeId, b: NodeId) -> None:
        """`knows` and `extends`, written the way any other fact is written.

        ⭐ Through the gate, mentioning, and stamped like everything else --
        because *which rules does this expert have* has to be an ordinary query
        over the graph (R4), not a table the loader keeps. This is the same
        lesson as `precedence is read, not kept`: the loader's copy would be a
        cache of a claim, and the claim is the definition.
        """
        prop = self.m.g.rel(self.atom(rel), a, b)
        self.m.gate.write(
            self.m.focus, prop, PLUS,
            licence=self.m.g.rel(self.LOADED, prop),
            source=self.source,
            # A rule node carries the variables of its own patterns, so a claim
            # ABOUT one is a mention rather than a generic claim (§13) -- the
            # same reason `overrides(<a>, <b>)` is written as one.
            mention=True,
        )

    def _expert_knows(self, expert: str, rule_name: str) -> None:
        self._expert_fact("knows", self.atom(expert), self.rule_nodes[rule_name])

    def _expert_extends(self, expert: str, base: str) -> None:
        self._expert_fact("extends", self.atom(expert), self.atom(base))

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


#: Heads whose ARGUMENT is a description rather than a proposition, so a
#: variable inside one is a class and not an unbound conclusion.
#:
#: ⚠⚠⚠ **A tuple rather than a third scattered string comparison.** `_fact` read
#: `term.head == "forbidden"` in one place and the consequent check knew nothing
#: about it, and `docs/quest-feedback.md` §6 reported how sharp that edge is: a
#: foreign corpus declined the tidier parser refactor precisely because moving
#: that head one level down would have *retired every norm in the suite
#: silently*. Adding `count` as a second literal in two more places is how that
#: happens again, so the set is named once and read everywhere.
#:
#: `forbidden(doing(harm(?x)))` names a class of acts; `count(goblin(?x))` names
#: a class of things to be counted. Same shape, same price, same reason §13
#: allows it: what tells a description from a generic claim is who is writing.
DESCRIBES = ("forbidden", "count")


def _describes(t: Term) -> bool:
    """Is this term an ask whose argument is a description? See `DESCRIBES`."""
    return t.head in DESCRIBES


def _mentions_a_rule(t: Term) -> bool:
    return (t.is_rule
            or (t.fn is not None and _mentions_a_rule(t.fn))
            or any(_mentions_a_rule(a) for a in t.args))


def _vars_in(g, node: NodeId) -> set:
    """Every variable in a structure -- **including one in RELATION position.**

    ⚠⚠⚠ It did not look at the relation, and `Graph.has_var` always has: `_mint`
    computes genericity as *the relation is generic, or any member is*. So the
    two disagreed about `?verb(?a, ?b)`, and the binding check is built from
    both -- `has_var` decides whether a consequent needs checking and this
    decides what would satisfy it.

    The disagreement cut both ways, which is why it survived. A consequent
    `+?r(?x, ?y)` passed the check because `?r` was never *wanted*; an antecedent
    `+ev_at(?verb(?a, ?b), ?t)` failed it because `?verb` was never *had* -- so
    destructuring a description was refused at the surface while `match` handled
    it perfectly (measured: 2 matches, `?verb` bound to `attack` and `steal`).

    ⭐ That is what blocked a **generic** interpreter: one rule per predicate was
    forced, because a rule could not be written over the predicate itself.
    """
    if g.is_var(node):
        return {node}
    # Memoised on the node, which is sound for the reason `has_var` is computed
    # at mint: a node's relation and members are fixed when it is built, so the
    # set of variables in it cannot change. Profiled once quiescence made this
    # the test for *did this member leave a variable of its own unbound* --
    # 2,729,643 calls in one comparison, on a few hundred distinct nodes.
    hit = g._vars_in.get(node)
    if hit is not None:
        return hit
    out = set()
    rel = g.relation_of(node)
    if rel is not None:
        out |= _vars_in(g, rel)
    for m in g.members(node):
        out |= _vars_in(g, m)
    g._vars_in[node] = out
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


def _report_unwebbed(machine: Machine) -> None:
    """Say when a rule reads a name nothing anywhere writes.

    ⭐⭐⭐ **The open class's own price, detected by the open class's own
    property.** A proposition needs no implementation, so a name awaiting its
    meaning and a name that is a typo are both well formed and both inert --
    and nothing in the engine could tell them apart. Meaning is the web, so a
    name with no web is the mistake, and this is where an author is looking.

    A note rather than an error, deliberately, and `_report_shadowed`'s argument
    applies unchanged: **we cannot catch every mistake, so this must not pretend
    to.** A corpus fed by a live channel legitimately reads what its own text
    never writes; refusing it would be wrong, and staying silent is the failure
    being repaired.

    ⚠⚠⚠ **Called from the DOOR, not from `load`, and that is a measurement.**
    Wired into every `load` it fired **91 times across the suite** -- and every
    one was correct, because a suite is made of deliberately partial fixtures:
    a rule loaded to test something else, whose premise nobody ever supplies.
    Correct and useless is still useless, because a note that fires ninety-one
    times is a note an author learns to skip. The four real corpora report
    **zero**. So it is said where an author actually loads a corpus to run it,
    and `Machine.unwebbed` stays available to anything that wants to ask.

    ⚠ Computed over the WHOLE machine rather than one document, because a corpus
    may span documents (§17's scopes) and the fact that satisfies a rule may
    arrive in the next one.

    ⚠ A fact arriving on a CHANNEL does not count as written, and that is right:
    `say user: +heat(...)` deposits `arrived(user, heat(...), +)`, so `heat` is
    an argument and not a claim until some rule asserts it. A corpus that never
    writes that rule genuinely cannot fire, and the note says so.
    """
    if getattr(machine, "_booting", False):
        return
    missing = machine.unwebbed()
    if not missing:
        return
    names = ", ".join(missing)
    print(f"note: nothing writes {names}, and a rule reads it -- so that rule "
          f"can never apply. A misspelling on either side does this; so does a "
          f"fact you meant to assert and did not", file=sys.stderr)


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
