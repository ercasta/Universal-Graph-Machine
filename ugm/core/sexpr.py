"""A second surface: s-expressions, beside the default notation.

    python -m ugm.core.sexpr

⭐ A surface is a reader, not the language. The graph is the truth and
docs/rules-design.md's notation is one way of writing it down; nothing in the
substrate knows which notation a node was authored in.

See docs/design/sexpr.md.
"""

import sys
from typing import List, Optional, Sequence, Tuple

from .chain import MINUS, PLUS, UNSURE
from .text import (ParseError, RuleMember, Statement, Term, Tok, tokenise)
from .rules import CAUSES, IMPLIES

SIGNS = {"+": PLUS, "-": MINUS, "?": UNSURE}
HEADER = "syntax:"
PREFIX = "lisp"


class Reader:
    """One token stream, read as s-expressions.

    ⚠ The TOKENISER is shared with the default notation, not reimplemented.
    `?x`, `<r>`, numerals, signs and parentheses already tokenise correctly, and
    a second tokeniser would be a second place for `?` to stop meaning what it
    means -- which is how this repo has lost four nodes to one name.
    """

    def __init__(self, toks: Sequence[Tok], i: int = 0) -> None:
        self.toks, self.i = list(toks), i

    # -- helpers
    def peek(self, ahead: int = 0) -> Optional[Tok]:
        j = self.i + ahead
        return self.toks[j] if j < len(self.toks) else None

    def next(self) -> Tok:
        t = self.peek()
        if t is None:
            raise ParseError("unexpected end of input")
        self.i += 1
        return t

    def at(self, text: str) -> bool:
        t = self.peek()
        return t is not None and t.text == text

    def at_sign(self) -> bool:
        t = self.peek()
        return t is not None and t.kind == "punct" and t.text in SIGNS

    def expect(self, text: str) -> Tok:
        t = self.next()
        if t.text != text:
            raise ParseError(f"line {t.line}: expected {text!r}, found {t.text!r}")
        return t

    # -- grammar
    def program(self) -> List[Statement]:
        out = []
        while self.peek() is not None:
            out.append(self.statement())
        return out

    def statement(self) -> Statement:
        open_tok = self.expect("(")
        head = self.next()
        line = open_tok.line
        if head.kind != "name":
            raise ParseError(
                f"line {line}: expected `fact`, `rule` or `say`, found {head.text!r}")
        if head.text == "fact":
            return self._fact(line)
        if head.text == "say":
            return self._say(line)
        if head.text == "rule":
            return self._rule(line)
        raise ParseError(
            f"line {line}: unknown statement {head.text!r} -- expected `fact`, "
            f"`rule` or `say`")

    def _fact(self, line: int) -> Statement:
        # `(fact <n> term)` names the statement; `(fact sign ...)` does not.
        # Distinguishable without lookahead beyond one token, because a sign is
        # punctuation and a name is its own token kind.
        name = ""
        if self.peek() is not None and self.peek().kind == "rulename":  # type: ignore[union-attr]
            name = self.next().text
            sign = PLUS
        else:
            sign = SIGNS[self.next().text] if self.at_sign() else PLUS
        term = self.term()
        self.expect(")")
        return Statement("fact", name, "", (), (), RuleMember(sign, term), "", line)

    def _say(self, line: int) -> Statement:
        ch = self.next()
        if ch.kind != "name":
            raise ParseError(f"line {ch.line}: expected a channel name")
        sign = SIGNS[self.next().text] if self.at_sign() else PLUS
        term = self.term()
        self.expect(")")
        return Statement("say", "", "", (), (), RuleMember(sign, term), ch.text, line)

    def _rule(self, line: int) -> Statement:
        name_tok = self.next()
        if name_tok.kind != "rulename":
            raise ParseError(
                f"line {name_tok.line}: a rule is named in angle brackets -- "
                f"`(rule <boil> causes (...) (...))`")
        conn = self.next()
        if conn.text not in (CAUSES, IMPLIES):
            raise ParseError(
                f"line {conn.line}: {conn.text!r} is not a connective. The closed "
                f"set is `{CAUSES}` and `{IMPLIES}` (§10)")
        ant = self.block()
        con = self.block()
        self.expect(")")
        return Statement("rule", name_tok.text, conn.text, ant, con, None, "", line)

    def block(self) -> Tuple[RuleMember, ...]:
        self.expect("(")
        out = []
        while not self.at(")"):
            out.append(self.member())
        self.expect(")")
        if not out:
            raise ParseError("a rule's antecedent and consequent may not be empty")
        return tuple(out)

    def member(self) -> RuleMember:
        # `(+ (heat ?a ?w))` is a signed member; anything else is a bare term and
        # means `+`. Told apart by looking one token past the paren, which is the
        # only place this grammar needs two-token lookahead.
        if self.at("(") and self.peek(1) is not None and \
                self.peek(1).kind == "punct" and self.peek(1).text in SIGNS:
            self.next()
            sign = SIGNS[self.next().text]
            term = self.term()
            self.expect(")")
            return RuleMember(sign, term)
        return RuleMember(PLUS, self.term())

    def term(self) -> Term:
        t = self.next()
        if t.kind == "var":
            return Term(t.text, (), True)
        if t.kind == "rulename":
            return Term(t.text, (), False, True)
        if t.kind == "name":
            return Term(t.text, (), False)
        if t.text != "(":
            raise ParseError(f"line {t.line}: expected a term, found {t.text!r}")
        head = self.term()
        args = []
        while not self.at(")"):
            args.append(self.term())
        self.expect(")")
        # ⭐ The AST the default notation produces, wherever the shapes
        # coincide. ⚠ The head must be a LEAF to fold into Term(head, args).
        # → docs/design/sexpr.md#the-ast-the-default-notation-produces-whereve
        if head.fn is None and not head.args and args:
            return Term(head.head, tuple(args), head.is_var, head.is_rule)
        return Term("", tuple(args), False, False, fn=head)


# -- the door ---------------------------------------------------------------


def wants_lisp(src: str) -> bool:
    """Does this document declare itself an s-expression document?"""
    for line in src.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        return line.startswith(HEADER) and line[len(HEADER):].strip() == "lisp"
    return False


def strip_header(src: str) -> str:
    out, done = [], False
    for line in src.splitlines():
        if not done and line.strip().startswith(HEADER):
            done = True
            out.append("")
            continue
        out.append(line)
    return "\n".join(out)


def read(src: str) -> List[Statement]:
    """Every statement in an s-expression document."""
    return Reader(tokenise(strip_header(src))).program()


def read_one(toks: Sequence[Tok], i: int) -> Tuple[Statement, int]:
    """One statement, for the `lisp:` prefix inside a default-notation document.

    Takes the SHARED token stream and returns where it stopped, so the default
    parser resumes exactly after the s-expression rather than re-tokenising.
    """
    r = Reader(toks, i)
    return r.statement(), r.i


# -- the differential check -------------------------------------------------

DEFAULT = """
rule <boil> = causes(
    { +heat(?a, ?w), +water(?w) },
    { +boiling(?w), -liquid(?w) } )
rule <weather> = implies( { +cloudy(?day, morning) },
                          { +likely(rain(?day, afternoon)) } )
fact <no-harm> = forbidden(doing(harm(?x)))
fact +heat(anna, kettle)
fact +water(kettle)
fact -liquid(ice)
fact dormant(<weather>)
say user: +raining(here)
"""

LISP = """
syntax: lisp
(rule <boil> causes ((+ (heat ?a ?w)) (+ (water ?w)))
                    ((+ (boiling ?w)) (- (liquid ?w))))
(rule <weather> implies ((+ (cloudy ?day morning)))
                        ((+ (likely (rain ?day afternoon)))))
(fact <no-harm> (forbidden (doing (harm ?x))))
(fact + (heat anna kettle))
(fact + (water kettle))
(fact - (liquid ice))
(fact + (dormant <weather>))
(say user + (raining here))
"""


def _rendered(src: str):
    """Everything a machine holds after loading, as text -- the only comparison
    that means anything, since node ids are per-graph."""
    from .machine import Machine
    from .text import load
    m = Machine()
    load(m, src, scope="x")
    facts = []
    for mo in m.chain.moments:
        for e in mo.delta:
            facts.append((e.sign, m.g.show(e.proposition)))
    rules = [(r.name, r.connective,
              [(x.sign, m.g.show(x.pattern)) for x in r.antecedent],
              [(x.sign, m.g.show(x.pattern)) for x in r.consequent])
             for r in m.rules.rules if r.node not in {b.node for b in m.bundle}]
    return facts, rules, m.g.count()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    failing, ran = 0, 0

    def gate(name: str, ok: bool) -> None:
        nonlocal failing, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    print(__doc__)
    print("Two readers, one graph\n")

    from .machine import Machine
    from .text import Loader

    a_facts, a_rules, a_nodes = _rendered(DEFAULT)
    b_facts, b_rules, b_nodes = _rendered(LISP)
    print(f"    default notation : {len(a_rules)} rules, {len(a_facts)} entries, "
          f"{a_nodes} nodes")
    print(f"    s-expressions    : {len(b_rules)} rules, {len(b_facts)} entries, "
          f"{b_nodes} nodes")
    for r in b_rules:
        print(f"      <{r[0]}> {r[1]}  {r[2]} -> {r[3]}")
    print()

    gate("⭐⭐⭐ the same corpus in both notations builds the IDENTICAL graph -- "
         "same rules, same members, same signs, same order",
         a_rules == b_rules)
    gate("...and the identical entries, sign for sign and in the same order",
         a_facts == b_facts)
    gate("...and the same number of nodes, so neither reader minted a twin",
         a_nodes == b_nodes)

    # -- what the default notation cannot say ------------------------------
    m = Machine()
    kb = Loader(m, scope="y")
    kb.load("syntax: lisp\n(fact + ((a b) c))\n(fact + (moment))\n")
    comp = kb.term("a(b)(c)")
    gate("⭐ `((a b) c)` is native here: a list's head is a term like any other, "
         "so a composite relation needs no special case",
         m.holds(comp) == "+" and m.g.show(comp) == "a(b)(c)")
    zero = m.g.rel(kb.atom("moment"))
    gate("⭐⭐ `(moment)` is a relation instance with NO members -- which `show` "
         "prints as `moment()` and the default parser refuses, so this reader "
         "closes the round-trip hole without adding the `a` / `a()` twin to the "
         "default notation",
         m.holds(zero) == "+" and m.g.show(zero) == "moment()"
         and zero != kb.atom("moment"))

    # -- the per-statement door --------------------------------------------
    m2 = Machine()
    kb2 = Loader(m2, scope="z")
    kb2.load("fact +on(a, b)\nlisp: (fact + (under b a))\nfact +beside(c, d)\n")
    gate("⭐ and one statement can drop into it inside an ordinary document: "
         "`lisp: (fact + (under b a))` between two default-notation facts",
         m2.holds(kb2.term("on(a, b)")) == "+"
         and m2.holds(kb2.term("under(b, a)")) == "+"
         and m2.holds(kb2.term("beside(c, d)")) == "+")

    # -- the default is untouched -------------------------------------------
    m3 = Machine()
    kb3 = Loader(m3, scope="w")
    kb3.load(DEFAULT)
    gate("⚠ a document with no marker is read exactly as before -- nothing "
         "dispatches unless `syntax: lisp` or `lisp:` is present",
         m3.holds(kb3.term("heat(anna, kettle)")) == "+")

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
