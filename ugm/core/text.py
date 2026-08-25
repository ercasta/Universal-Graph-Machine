"""A surface for authoring graphs (§3, §8).

One grammar, because it is all one kind of thing: a rule is a relation
instance, by(R, boss) is a relation instance, raining(here) is a relation
instance.

See docs/design/text.md.
"""

import sys
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from .graph import NodeId
from .machine import Machine
from .rules import (ABSENT, ASSERT, ERASE, IMPLIES, KEEP, STOP,
                    Destroy, Forget, Label, Member, Merge, Unlabel,
                    Unmerge)

# The two modes the surface writes. `?` is gone: absence is ignorance, so
# there is nothing left for a third mark to say. `-` is a CONSEQUENT mode --
# erase this -- and the loader refuses it in an antecedent, where the corpus
# must choose between `no p` (nothing anchors it) and `+not(p)` (something
# anchors its denial).
SIGNS = {"+": ASSERT, "-": ERASE}

# Keywords that open a new top-level statement -- reached mid-block, one of
# these ends a line-form rule with no `->`/blank line said explicitly. A
# domain that names a relation identically to one of these words needs a
# blank line before it; none of the shipped corpora do.
_LINE_FORM_STOPS = {"alt", "rule", "fact", "say", "action", "alias",
                    "after", "frozen", "learned", "when"}


class ParseError(Exception):
    pass


# -- tokenising -------------------------------------------------------------


class Tok(NamedTuple):
    kind: str  # name | var | string | rulename | punct
    text: str
    line: int


_PUNCT = set("(){}[],=:@+-?>.")
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
        if ch == '"':
            # A string literal, for a name the bare-name lexing above cannot
            # write at all -- a path, a filename, anything with a space or a
            # backslash in it. `\"` and `\\` are decoded; everything else
            # backslash-escapes to itself, so a lone `\` before an ordinary
            # character (a Windows path's separator) survives unread rather
            # than silently eating the next character. Parses to an ordinary
            # `name`-shaped Term (`Parser.primary`) -- once past the lexer, a
            # quoted and a bare atom of the same spelling are one node.
            start_line = line
            j = i + 1
            out = []
            while True:
                if j >= n:
                    raise ParseError(f"line {start_line}: unclosed string")
                c = src[j]
                if c == '"':
                    j += 1
                    break
                if c == "\n":
                    raise ParseError(f"line {start_line}: unclosed string -- "
                                      f"a string does not span a line")
                if c == "\\" and j + 1 < n and src[j + 1] in ('"', "\\"):
                    out.append(src[j + 1])
                    j += 2
                    continue
                out.append(c)
                j += 1
            toks.append(Tok("string", "".join(out), start_line))
            i = j
            continue
        if ch == "$":
            # A variable. `$` does one job and `?` does one job: before this
            # split, `?` was BOTH the unsure sign and the variable sigil, and
            # the lexer told them apart by a lookahead -- which is why the
            # unsure member in `bundle.ugm` had to be written `? $p`, two
            # meanings of one character a space apart.
            if i + 1 >= n or not (src[i + 1].isalnum() or src[i + 1] == "_"):
                raise ParseError(f"line {line}: `$` names a variable and needs "
                                 f"a name after it")
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] in "_-"):
                j += 1
            toks.append(Tok("var", src[i:j], line))
            i = j
            continue
        if ch == "?" and i + 1 < n and (src[i + 1].isalnum() or src[i + 1] == "_"):
            # ...and the old spelling fails LOUDLY rather than lexing as the
            # unsure sign followed by a name, which is what it would otherwise
            # do: `+goal(?w)` would become a sign inside an argument list and
            # the error would point at the bracket rather than at the sigil.
            raise ParseError(f"line {line}: `{src[i:i+2]}...` -- a variable is "
                             f"written `${src[i+1:i+2]}...` now; `?` is the "
                             f"unsure sign only")
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

    unresolved against a graph. fn is the relation slot when it holds a whole
    TERM rather than a name -- a(b)(c), the node whose relation is a(b).  Set
    only for a CHAINED application, so every term that parsed before this
    existed still parses to the identical shape.

    See docs/design/text.md#term.
    """

    head: str
    args: Tuple["Term", ...]
    is_var: bool
    is_rule: bool = False
    fn: Optional["Term"] = None
    # `+person` in an ARGUMENT: introduce one. `+` already signals a node
    # coming to be -- asserting `+p(x)` is what builds `p(x)` -- so this is that
    # mark one level down rather than a second meaning for it. `member` consumes
    # the member-level sign before `term` is ever called, so the two cannot
    # shadow each other.
    mint: bool = False


class RuleMember(NamedTuple):
    """ `at: Optional[Term]` was here, between `term` and `binds`. It went with
    the locus: an entry has no second time for a member to name."""

    sign: str
    term: Term
    binds: Optional[Term] = None
    # `+p(x) intensity $n` (docs/design/intensity-gates.md) -- a CONSEQUENT-
    # only extra naming the write's own strength, in place of the ordinary
    # default (`scratchpad.ON`). `None` is *no opinion*, which is every
    # ordinary member -- antecedent or consequent -- and the loader refuses
    # it outside a consequent (`_refuse_write_premise`, mirroring how `-` is
    # refused in an antecedent) rather than silently ignoring it there.
    write: Optional[Term] = None


class PostClause(NamedTuple):
    """A postcondition, as written: a query, and what it spends if it holds.

    rule <classify> = implies( { +asked($x) }, { +considered($x) } ) after {
    +penguin($x) } => destroy($x) frozen after => stop The query is an
    ordinary antecedent -- no new notation, and the same matcher -- and it is
    matched with the rule's OWN bindings already in hand, so $x above is the $x
    the rule bound.

    See docs/design/text.md#postclause.
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
    # `alt(branch1, branch2, ...)` -- a union of conjunctive branches
    # sharing `antecedent` as a prefix, each concluding the SAME
    # `consequent` (`new_substrate.md`). None for an ordinary rule. Compiled
    # at load into one Rule per branch -- not a runtime branch, no matcher
    # change.
    alts: Optional[Tuple[Tuple[RuleMember, ...], ...]] = None


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
        if t.text == "action":
            # The action palette, declared: action move($x, $y) A SIGNATURE
            # and nothing else.  No angle brackets.
            # → docs/design/text.md#the-action-palette-declared
            return Statement("action", "", "", (), (), self.member(), "", t.line)
        if t.text in ("after", "frozen", "learned", "when"):
            raise ParseError(
                f"line {t.line}: `{t.text}` opened a TRIGGER statement, and "
                f"triggers are retired (docs/design/intensity-gates.md). "
                f"A rule's own unconditional ops go in its RHS tail "
                f"(`=> stop`, `=> destroy($x)`); a rule that should only "
                f"fire under some condition puts that condition in its own "
                f"antecedent, which is what a GATE is for -- see "
                f"`ugm/rules/tools_approval.ugm`."
            )
        if t.text == "alias":
            # A shorthand the corpus defines: `alias attacks($a, $t) = { ... }`.
            # The head is a plain term whose arguments are the variables the
            # body may use; the body is a block of ordinary members. Expansion
            # is the loader's -- by the time anything downstream looks, an
            # alias use IS its expansion, at the member level only: a nested
            # occurrence (`mention(m, attacks(a, b))`) is a denotation and is
            # left exactly as written.
            head = self.term()
            self.expect("=")
            body = self.block()
            return Statement("alias", head.head, "", body, (),
                             RuleMember(ASSERT, head, None), "", t.line)
        if t.text == "fact":
            # A fact may be NAMED, and the name goes in the same angle brackets
            # a rule's does, because it is the same namespace: names of
            # *statements*, kept out of the relation namespace.
            # →
            # docs/design/text.md#a-fact-may-be-named-and-the-name-goes-in-the-sa
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
        # `rule <name>` with no `=` following is the LINE form
        # (`new_substrate.md`'s own sketch): one member per line, `->`
        # between antecedent and consequent, no braces or commas. Same
        # `Statement` either way -- this is a second surface over one
        # grammar, not a second kind of rule.
        if not self.at("="):
            return self._rule_lines(name_tok, line)
        self.expect("=")
        conn = self.next()
        if conn.text != IMPLIES:
            raise ParseError(
                f"line {conn.line}: {conn.text!r} is not a connective. There "
                f"is one -- `{IMPLIES}` -- and a second earns its place only by "
                f"licensing a different (forward, backward) reading pair. "
                f"`causes` did not: all it did was land its conclusion in a "
                f"later moment, and there are no moments."
            )
        self.expect("(")
        ant = self.block()
        self.expect(",")
        # `alt(branch1, branch2, ...)` -- a union of conjunctive branches
        # sharing `ant` as a prefix. Each branch is an ordinary block, so
        # nothing about `block()` changes; only where the blocks sit does.
        alts: Optional[Tuple[Tuple[RuleMember, ...], ...]] = None
        if self.at("alt"):
            self.next()
            self.expect("(")
            branches = [self.block()]
            while self.at(","):
                self.next()
                branches.append(self.block())
            self.expect(")")
            self.expect(",")
            alts = tuple(branches)
        con = self.block()
        self.expect(")")
        # An optional ordered tail -- `=> destroy($x), stop` -- the
        # rule's OWN unconditional ops, in the rule's own scope, with no
        # separate `after <R> => ...` statement and no query indirection.
        # Built as a `PostClause` with an empty query, which is exactly the
        # shape a bare `after` trigger already has: this is that shape,
        # authored on the rule instead of beside it.
        posts: Tuple[PostClause, ...] = ()
        if self.at("="):
            self.next()
            self.expect(">")
            spends = [self.spend()]
            while self.at(","):
                self.next()
                spends.append(self.spend())
            posts = (PostClause((), tuple(spends), False, False),)
        return Statement("rule", name_tok.text, conn.text, ant, con, None, "",
                         line, posts, alts)

    # -- the line form: `rule <name>` / one member per line / `->` --------
    #
    # `new_substrate.md`'s own sketch, minus the scoring brackets it drew
    # (retired -- there is no rule-picking left for a score to decide
    # between). What IS built: the shape. A block ends at a physical
    # line gap (a blank line, or a comment line -- comments belong between
    # rules in this form, not inside one), at `alt`/`->`/`=>`, at the next
    # top-level statement, or at end of input. There is no comma to lean on,
    # so the gap and the keywords are the only block boundaries there are.

    def _rule_lines(self, name_tok: Tok, line: int) -> Statement:
        ant = self._member_block()
        alts: Optional[Tuple[Tuple[RuleMember, ...], ...]] = None
        if self.at("alt"):
            branches = []
            while self.at("alt"):
                self.next()
                branches.append(self._member_block())
            alts = tuple(branches)
        if not self._looking_at("-", ">"):
            t = self.peek()
            where = f"line {t.line}" if t is not None else "end of input"
            raise ParseError(
                f"{where}: a line-form rule's antecedent ends with `->`, one "
                f"member per line, no braces or commas"
            )
        self.next()
        self.next()
        con = self._member_block()
        posts: Tuple[PostClause, ...] = ()
        if self._looking_at("=", ">"):
            self.next()
            self.next()
            spends = [self.spend()]
            while self.at(","):
                self.next()
                spends.append(self.spend())
            posts = (PostClause((), tuple(spends), False, False),)
        return Statement("rule", name_tok.text, IMPLIES, ant, con, None, "",
                         line, posts, alts)

    def _member_block(self) -> Tuple[RuleMember, ...]:
        out = [self.member()]
        while self._more_members():
            out.append(self.member())
        return tuple(out)

    def _more_members(self) -> bool:
        t = self.peek()
        if t is None:
            return False
        if t.line - self.toks[self.i - 1].line >= 2:
            return False
        if self._looking_at("-", ">") or self._looking_at("=", ">"):
            return False
        if t.kind == "name" and t.text in _LINE_FORM_STOPS:
            return False
        return True

    def _looking_at(self, a: str, b: str) -> bool:
        """Two adjacent punctuation tokens, on the same source line -- how
        `->` and `=>` are told apart from an ordinary `-`/`=` inside a
        member, since neither is its own token in the lexer."""
        t = self.peek()
        t2 = self.toks[self.i + 1] if self.i + 1 < len(self.toks) else None
        return (t is not None and t.kind == "punct" and t.text == a
                and t2 is not None and t2.kind == "punct" and t2.text == b
                and t2.line == t.line)

    def spend(self) -> Tuple["Term", int]:
        """What a postcondition spends: `stop`, or one of the graph ops.

         **`attend(...)`, `brush(...)`, `unattend`, `push(...)` and `pop(...)`
        ARE GONE**, with the focus queue and the frame stack they drove
        (docs/design/intensity-gates.md). A node's INTENSITY is what "in
        play" means now, and every rule whose antecedent is on fires -- so
        there is nothing left for a separate what-is-the-agent-thinking-about
        pool to order, nothing for `brush` to put back (`keep` is the read
        that does not spend), and no sub-line to suspend on a stack of its
        own. `boost(<R>, n)`/`damp(<R>, n)`/`reset` went earlier, for naming
        a RULE rather than a node.

         The delta in the return type is now always 0 and is kept only so the
        surviving spends share one shape. Nothing reads it.
        """
        t = self.next()
        if t.kind == "name" and t.text == "stop":
            # *Done is the output of a rule that checks against the goal* --
            # which the table loop's own design says, and had no way to obey.
            # A rule concludes that here is over; its postcondition is what
            # ends the run.
            return (STOP, 0)
        if t.kind == "name" and t.text in ("merge", "unmerge"):
            # `merge($a, $b)` / `unmerge($a, $b)` -- identity, the doc's own
            # strongest argument for a microprogram: an effect `+`/`-`
            # provably cannot express, already built, and unreachable from a
            # rule until this. `$a` is KEEP, `$b` is DROP -- `Graph.merge`'s
            # own order.
            self.expect("(")
            keep = self.term()
            self.expect(",")
            drop = self.term()
            self.expect(")")
            cls = Merge if t.text == "merge" else Unmerge
            return (cls(keep, drop), 0)
        if t.kind == "name" and t.text == "destroy":
            # Structural, not belief -- see `Destroy`'s own docstring for the
            # hazard this does not fence.
            self.expect("(")
            target = self.term()
            self.expect(")")
            return (Destroy(target), 0)
        if t.kind == "name" and t.text in ("label", "unlabel"):
            # `label($z, paul)` -- a bare atom, the corpus's existing
            # bare-name style, or `label($z, "Paul Smith")` where the label
            # itself needs a space a bare name cannot carry (see the
            # tokenizer's string literal).
            self.expect("(")
            target = self.term()
            self.expect(",")
            text = self.term()
            self.expect(")")
            cls = Label if t.text == "label" else Unlabel
            return (cls(target, text), 0)
        if t.kind == "name" and t.text == "forget":
            # `forget $hit` -- bare, no parens, matching `new_substrate.md`'s
            # own spelling exactly (unlike the other graph ops, which read
            # as calls). Erases a request and its answer together.
            target = self.term()
            return (Forget(target), 0)
        raise ParseError(
            f"line {t.line}: a postcondition ends the run or reaches the "
            f"graph, so it says `stop`, `merge(...)`, `unmerge(...)`, "
            f"`destroy(...)`, `label(...)`, `unlabel(...)` or `forget ...`, "
            f"not {t.text!r}"
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
        sign = ASSERT
        if t.kind == "punct" and t.text in SIGNS:
            sign = SIGNS[self.next().text]
        elif (t.kind == "name" and t.text == "no"
                and self.i + 1 < len(self.toks)
                and self.toks[self.i + 1].kind in ("name", "var", "rulename")):
            # `no p($x)` -- there is NO p($x) -- the absence mode, in sign
            # position because it is one: a fourth way a member relates to the
            # state, beside asserted, denied and unsure.  The lookahead is
            # what keeps `no` an ordinary word everywhere else: `no(...)` is a
            # term (next token is `(`), a bare `no` before `,` or `}` is the
            # atom, and only `no <term>` reads as the mode.
            self.next()
            sign = ABSENT
        elif (t.kind == "name" and t.text == "keep"
                and self.i + 1 < len(self.toks)
                and self.toks[self.i + 1].kind in ("name", "var", "rulename")):
            # `keep p($x)` (docs/design/intensity-gates.md) -- an ANTECEDENT
            # mode, matched exactly the way a plain `+p($x)` is, but exempt
            # from what firing now costs every `+` member by default: this
            # one is a non-consuming read, a Petri net's test arc, spelled
            # as a fifth mode rather than a flag on `+` for `no`'s own
            # reason -- a mode is a first-class thing a rule's own reading
            # names, not an option quietly changing what `+` means. Same
            # lookahead as `no`, for the same reason: `keep(...)` is a term,
            # a bare `keep` is the atom, only `keep <term>` is the mode.
            self.next()
            sign = KEEP
        # `$z = p($x, $y)` -- `new_substrate.md`'s own spelling of `as`,
        # prefix rather than suffix. The same binding (`RuleMember.binds`),
        # built the same way; only where it sits in the line differs. The
        # lookahead is two tokens, not one: `$z` alone is an ordinary member
        # (`{+want($p), no $p}` tests a bound variable directly), and only
        # `$z =` -- the var immediately followed by `=` -- reads as a prefix
        # bind. `=` never otherwise appears inside a member, so there is
        # nothing here for it to collide with.
        prefix_binds = None
        t2 = self.peek()
        if (t2 is not None and t2.kind == "var" and self.i + 1 < len(self.toks)
                and self.toks[self.i + 1].kind == "punct"
                and self.toks[self.i + 1].text == "="):
            prefix_binds = self.primary()
            self.next()  # "="
        term = self.term()
        #  `@` is refused rather than ignored. It used to carry a GRADE, and
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
        # `as $t` -- WHAT the member matched, named.
        #
        #  `at $m` was the other half and it is REFUSED rather than ignored,
        # for `@`'s reason directly above: a notation that parses and is dropped
        # is a rule that means something other than what it says, and nothing
        # raises. It said WHERE the entry sits, and an entry has no locus.
        binds = None
        while True:
            if self.at("at"):
                raise ParseError(
                    f"line {t.line}: `at $m` is gone with the locus. An entry "
                    f"has no second time to bind, so a member cannot say where "
                    f"it sits -- read the chain instead: `in_delta($m, $e), "
                    f"entry_of($e, p, +)` is the same claim, and `anc`/`sanc` "
                    f"order the moments."
                )
            if self.at("as"):
                self.next(); binds = self.term()
            else:
                break
        if prefix_binds is not None:
            if binds is not None:
                raise ParseError(
                    f"line {t.line}: `$z = {self._show_term(term)}` and "
                    f"`... as $t` are the same binding written twice -- say "
                    f"it once"
                )
            binds = prefix_binds
        # `intensity $n` (docs/design/intensity-gates.md) -- the general
        # write: this member's own strength, in place of the ordinary
        # default. `$n` is usually a variable an earlier member computed
        # (`intensity(count(a)) as $n, plus($n, 1) as $n2`), so this reads a
        # full TERM, not only a numeral -- unlike the retired bracket score
        # below, which was always a load-time constant.
        write = None
        if self.at("intensity"):
            self.next()
            write = self.term()
        if self.at("["):
            # The retired per-line score -- `[+3, attention_multiplier:1.2]`
            # -- refused rather than silently parsed and dropped, the same
            # standing `@`'s grade and `at`'s locus already have above: a
            # rule that means one thing and is read as another is worse
            # than a rule that fails to load. There is no rule-picking left
            # for a score to decide between; `intensity $n` (above) is the
            # replacement for the one thing a bracket said that still has
            # a job -- a write's own strength -- and it is a consequent
            # clause, not a bracket on any line.
            raise ParseError(
                f"line {t.line}: `[...]` scored a line's contribution to "
                f"which of several matching rules won -- and nothing picks "
                f"among matching rules any more (every one whose gates are "
                f"on fires). Naming a write's own strength is `intensity "
                f"$n` in a CONSEQUENT member now, not a bracket on any line."
            )
        return RuleMember(sign, term, binds, write)

    @staticmethod
    def _show_term(term: "Term") -> str:
        """A term, printed for an error message only -- before anything is
        built, so this cannot call `Graph.show`."""
        if not term.args:
            return term.head
        return f"{term.head}({', '.join(Parser._show_term(a) for a in term.args)})"

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
        if (self.at("-") and self.i + 1 < len(self.toks)
                and self.toks[self.i + 1].kind == "name"
                and self.toks[self.i + 1].text.isdigit()):
            # A negative numeral, and only a numeral: `-` is the sign marker
            # everywhere else, so `-3` is read here and `-x` is still refused.
            # A numeral is an atom whose NAME reads as a number, so this mints
            # the atom `-3` and nothing in the graph learns arithmetic.
            self.next()
            digits = self.next()
            return Term("-" + digits.text, (), False)
        t = self.next()
        if t.kind == "var":
            # `$p($t)` -- a variable in the RELATION slot. The substrate has
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
        if t.kind not in ("name", "string"):
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
        # The name scope, and whether it is shared.  Note what this
        # deliberately does NOT do: assert identity in the graph.
        # → docs/design/text.md#the-name-scope-and-whether-it-is-shared
        self.atoms: Dict[str, NodeId] = (
            {} if scope is None else machine.scopes.setdefault(scope, {})
        )
        self.vars: Dict[str, NodeId] = {}
        # Aliases: shorthand a corpus defines for itself, expanded at load and
        # gone by the time anything downstream looks. Loader-scoped like the
        # name table, because a shorthand is a way of WRITING this document.
        self.aliases: Dict[str, Tuple[Term, Tuple[RuleMember, ...]]] = {}
        # One counter for every fresh name expansion mints, so two uses of one
        # alias -- in one rule or across a corpus -- never share a variable or
        # a marker by accident.
        self._alias_fresh = 0
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
        # A domain is a channel, and that is the whole of what a domain
        # needs to be.  Unscoped documents keep kb, which is what every corpus
        # has had.
        # → docs/design/text.md#a-domain-is-a-channel-and-that-is-the-wh
        which = domain if domain is not None else scope
        self.source = self.m.KB if which is None else self.m.channels.use(
            self.atom(which)
        )
        if scope is not None and not machine._booting:
            # A claim about this document, in the graph like everything else, so
            # that saving a session is a RENDERING rather than a side-channel.
            self._scoped(self.source, scope)
        # The bundle, by name.
        # → docs/design/text.md#the-bundle-by-name-every-section-of-the-design
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
        self.m.gate.write(prop, generic=True)

    def say(self, channel: str, text: str) -> NodeId:
        """The world speaks, **in this corpus's scope** -- the scoped door for
        arrivals, beside `channel` and `answerer`.

        It also records which scope the term was written in, which is what lets
        a saved session be replayed into the same nodes rather than into twins
        that merely print the same.
        """
        node, prop = self.channel(channel), self.term(text)
        self.m._saying_scope = self.scope_name
        try:
            self.m.channels.deliver(node, prop)
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

         **The result is resolved in THIS corpus's table**, which is the whole
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

        which its request has a meaning. A tool answers a request, a request is
        a relation, and a relation is a name -- and names are not identity
        here.  Said here as well as on Machine.answerer because this is the
        door the note above tells everyone to use, and a reader who never opens
        the other one has no...

        See docs/design/text.md#answerer.
        """
        #  The apparatus must not be joined on its own requests, and this
        # was found by the apparatus squatting on a name a fixture already
        # used.
        # → docs/design/text.md#the-apparatus-must-not-be-joined-on-its-ow
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
        the scope is handed to it instead. `$x` in the trigger is the rule's
        `$x`, so the query still says *this orc* rather than *some orc*.

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
                      self.build(mm.binds, scope) if mm.binds else None)
            for mm in clause.query
        )
        spends = self._build_spends(clause.spends, scope)
        self.m.rules.triggers.setdefault(
            None if host is None else host.node, []
        ).append((query, spends, clause.frozen, clause.learned))

    def _build_spends(self, raw_spends, scope: Dict[str, NodeId]):
        """Ops as written -> ops as built, in one scope.

        `STOP` is not a term, so it does not go through `build`. Everything
        else IS one, built in the SAME scope as the host rule's own
        antecedent and consequent -- which is what makes `merge($a, $b)`
        those two nodes, not fresh ones.
        """
        return tuple(
            (t if t is STOP
             else Merge(self.build(t.keep, scope), self.build(t.drop, scope))
             if isinstance(t, Merge)
             else Unmerge(self.build(t.keep, scope), self.build(t.drop, scope))
             if isinstance(t, Unmerge)
             else Destroy(self.build(t.term, scope)) if isinstance(t, Destroy)
             else Label(self.build(t.term, scope), self.build(t.text, scope))
             if isinstance(t, Label)
             else Unlabel(self.build(t.term, scope), self.build(t.text, scope))
             if isinstance(t, Unlabel)
             else Forget(self.build(t.term, scope)), delta)
            for t, delta in raw_spends
        )

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
            #  A NUMERAL is not this document's name for something. Two
            # corpora may be about different kettles and are never about
            # different 2s.
            # → docs/design/text.md#a-numeral-is-not-this-document-s-name-for
            self.atoms[name] = (
                self.m._numeral(int(name)) if name.isdigit()
                else self.m.g.atom(name)
            )
        return self.atoms[name]

    def var(self, name: str, scope: Dict[str, NodeId]) -> NodeId:
        # Variables are scoped to a rule: `$w` in two rules is two variables,
        # because a rule is a statement and not a fragment of a larger one.
        if name not in scope:
            scope[name] = self.m.g.var(name)
        return scope[name]

    def _note_shadow(self, t: Term) -> None:
        """A bare name in an ARGUMENT position that resolves to a reserved node.

         One node with two meanings, which is the twin trap inverted.

        See docs/design/text.md#note-shadow.
        """
        if t.is_rule or t.is_var or t.args or t.head.isdigit():
            return
        #  Numerals are excluded deliberately, and the exclusion is the whole
        # difference between a diagnostic and noise. `cost(sword, 3)` SHOULD
        # resolve to the numeral the machinery uses -- that is sharing, not
        # shadowing. What traps a domain author is a reserved name that reads
        # like ordinary domain vocabulary, and the first version of this flagged
        # every integer in every corpus, which is how a message gets ignored.
        if self.atom(t.head) in set(self.m.reserved.values()):
            self.shadowed.add(t.head)

    def build(self, t: Term, scope: Dict[str, NodeId]) -> NodeId:
        if t.mint:
            #  Wrapped in the machine's OWN node, never one from the name
            # table -- so `new` stays a word a corpus may mean something else
            # by. That is the whole reason this is a mark and not a keyword:
            # `ugm.vocabulary` counts every name the engine takes, and `new` is
            # too ordinary a word to spend.
            #
            # Scoped to the statement, exactly as a variable is, and for the
            # same reason: `+person(+k), +named(+k, $p)` is one new thing said
            # twice about. Interning used to make the two `new(k)` one node by
            # accident of the substrate; `_markers` then found one marker and
            # minted one entity. It mints per node, so `+k` written twice has
            # to BE one node, and here is where a rule's names are made one.
            key = f"+{t.head}"
            got = scope.get(key)
            if got is None:
                got = self.m.g.rel(
                    self.m.NEW, self.build(t._replace(mint=False), scope))
                scope[key] = got
            return got
        if t.fn is not None:
            # The relation slot holds a term, so `a(b)(c)` is a node whose
            # relation is `a(b)` -- a different SHAPE from `a(b(c))`, which is
            # what tells the two apart now that neither is one node.
            return self.m.g.rel(
                self.build(t.fn, scope), *[self.build(a, scope) for a in t.args]
            )
        if t.is_rule:
            return self.rule_ref(t.head)
        if t.is_var:
            v = self.var(t.head, scope)
            # A variable with arguments is a relation instance whose relation is
            # that variable -- `$p($t)`. Without this it would silently drop the
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

        Names are not identity (see graph.py) -- a node is identified by being
        the node it is, and atom() mints a fresh one every call.  It refuses
        leftovers, and until a foreign corpus reported it, it did not.

        See docs/design/text.md#term.
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
        # There is ONE surface. `core/sexpr.py` was a second one -- an
        # s-expression reader chosen by `syntax: lisp` on the first line or
        # `lisp:` on a single statement -- and it was deleted on 08-22. Its
        # argument was sound (a notation is a way of writing the graph down,
        # and nothing downstream learned which notation a node came from), but
        # nothing exercised either entry point: not the suite, not a gate, not
        # a probe, not the book. 335 lines no measurement covered, which by
        # this repository's own standard is a check that cannot fail at module
        # scale. See docs/models.md, "the engine must become shallower".
        statements = Parser(tokenise(src)).program()
        # Aliases first: everything after this pass may be written in them.
        for s in statements:
            if s.kind == "alias":
                self._alias(s)
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

    def _alias(self, s: Statement) -> None:
        """Register a shorthand: `alias attacks($a, $t) = { +is(+e, attack),
        +agent(+e, $a), +target(+e, $t) }`.

        The head's arguments are the ONLY names the use-site supplies; anything
        else in the body is the alias's own. A body variable that is not a
        parameter is renamed fresh per use (existential -- two uses never share
        it). A `+kind` marker in the body is the entity the shorthand stands
        up, and what it becomes depends on where the alias is used:

            in a fact         a labelless entity, minted at load
            in an antecedent  a fresh variable, joining the expanded members
            in a consequent   a `+kind` marker still -- one entity per firing

        Expansion is at MEMBER level only. `mention(m, attacks(a, b))` keeps
        the compound as written: nested is a denotation (docs/world-model.md),
        and expanding it would put words in the mention's mouth.
        """
        assert s.member is not None
        head = s.member.term
        if head.is_var or head.is_rule or head.fn is not None or head.mint:
            raise ParseError(
                f"line {s.line}: an alias head is a plain `name($params)`"
            )
        if any((not a.is_var) or a.args or a.mint for a in head.args):
            raise ParseError(
                f"line {s.line}: alias parameters are bare variables -- "
                f"`{head.head}($a, $t)`, nothing structured"
            )
        if len({a.head for a in head.args}) != len(head.args):
            raise ParseError(
                f"line {s.line}: alias {head.head!r} repeats a parameter"
            )
        if head.head in self.aliases:
            raise ParseError(
                f"line {s.line}: alias {head.head!r} is already defined"
            )
        if head.head in self.m.reserved:
            raise ParseError(
                f"line {s.line}: {head.head!r} is the machinery's word, and an "
                f"alias would shadow every rule written against it"
            )
        if not s.antecedent:
            raise ParseError(f"line {s.line}: an alias body is one or more members")
        self.aliases[head.head] = (head, s.antecedent)

    def _is_alias_use(self, t: Term) -> bool:
        return (t.fn is None and not t.is_var and not t.is_rule
                and not t.mint and t.head in self.aliases)

    def _expand(self, members: Tuple[RuleMember, ...], context: str, line: int,
                entities: Optional[Dict[str, NodeId]] = None
                ) -> Tuple[RuleMember, ...]:
        out: List[RuleMember] = []
        for m in members:
            out.extend(self._expand_member(m, context, line, entities, 0))
        return tuple(out)

    def _expand_member(self, m: RuleMember, context: str, line: int,
                       entities: Optional[Dict[str, NodeId]], depth: int
                       ) -> List[RuleMember]:
        if not self._is_alias_use(m.term):
            return [m]
        if depth > 16:
            raise ParseError(
                f"line {line}: alias {m.term.head!r} expands into itself"
            )
        if m.sign != ASSERT:
            raise ParseError(
                f"line {line}: an alias stands for several claims, and a sign "
                f"other than `+` does not distribute over them -- write the "
                f"expansion out to deny part of it"
            )
        if m.binds is not None:
            raise ParseError(
                f"line {line}: `as` names what ONE member matched, and an alias "
                f"expands to several -- expose the entity as an alias parameter "
                f"instead"
            )
        head, body = self.aliases[m.term.head]
        if len(m.term.args) != len(head.args):
            raise ParseError(
                f"line {line}: {m.term.head!r} takes {len(head.args)} "
                f"argument(s), given {len(m.term.args)}"
            )
        mapping = {p.head: a for p, a in zip(head.args, m.term.args)}
        rename: Dict[str, str] = {}
        self._alias_fresh += 1
        n = self._alias_fresh
        out: List[RuleMember] = []
        for bm in body:
            term = self._alias_term(bm.term, mapping, rename, n, context,
                                    entities, line)
            binds = (self._alias_term(bm.binds, mapping, rename, n, context,
                                      entities, line)
                     if bm.binds is not None else None)
            out.extend(self._expand_member(
                RuleMember(bm.sign, term, binds), context, line, entities,
                depth + 1))
        return out

    def _alias_term(self, t: Term, mapping: Dict[str, Term],
                    rename: Dict[str, str], n: int, context: str,
                    entities: Optional[Dict[str, NodeId]], line: int) -> Term:
        if t.mint:
            if t.args or t.is_var or t.fn is not None:
                raise ParseError(
                    f"line {line}: an alias body mints with a bare `+name` marker"
                )
            fresh = rename.setdefault(t.head, f"{t.head}~{n}")
            if context == "con":
                return Term(fresh, (), False, mint=True)
            v = f"?{fresh}"
            if context == "fact" and entities is not None and v not in entities:
                entities[v] = self.m.g.entity()
            return Term(v, (), True)
        walk = lambda a: self._alias_term(a, mapping, rename, n, context,
                                          entities, line)
        if t.fn is not None:
            return t._replace(fn=walk(t.fn), args=tuple(walk(a) for a in t.args))
        if t.is_var:
            if t.head in mapping:
                got = mapping[t.head]
                if not t.args:
                    return got
                # The parameter stood in RELATION position: apply what the
                # use-site supplied to the substituted arguments.
                return Term("", tuple(walk(a) for a in t.args), False, fn=got)
            fresh = rename.setdefault(t.head, f"{t.head}~{n}")
            return t._replace(head=fresh, args=tuple(walk(a) for a in t.args))
        if t.args:
            return t._replace(args=tuple(walk(a) for a in t.args))
        return t

    def _action(self, s: Statement) -> None:
        """Declare an action, and put it in the graph where a rule can find it.

         **Mentioned, not claimed.** `move($x, $y)` is generic and the gate
        refuses to deposit a proposition with a variable in it -- correctly, and
        `a_rule_can_introduce_a_thing` is the same wall from the other side. So
        what is deposited is `action(move($x, $y))`, a claim ABOUT a pattern,
        exactly as `reify` deposits `ant(<R>, heat($a, $w))`.

        Which is what makes the palette DISCOVERABLE: `+action($a)` is an
        ordinary premise, so one fallback rule can range over every action --
        including ones declared after it was written. Without the declaration a
        corpus needs one hand-written fallback per action, and a new action is a
        fallback nobody remembers to add.
        """
        assert s.member is not None
        scope: Dict[str, NodeId] = {}
        term = self.build(s.member.term, scope)
        self.m._note_that(self.m.AFFORDED, term)

    def _name(self, s: Statement) -> None:
        """Build a named fact's proposition ONCE, and register the name.

        Once, because building it twice would mint fresh variables and produce a
        second node -- which is the very failure naming exists to prevent.
        """
        assert s.member is not None
        if s.name in self.rule_nodes:
            raise ParseError(f"line {s.line}: <{s.name}> is already declared")
        if self._is_alias_use(s.member.term):
            raise ParseError(
                f"line {s.line}: a name names ONE proposition, and "
                f"{s.member.term.head!r} expands to several -- name the "
                f"expansion's members instead"
            )
        self.rule_nodes[s.name] = self.build(s.member.term, {})

    def _rule(self, s: Statement) -> None:
        if s.name in self.rule_nodes:
            raise ParseError(f"line {s.line}: <{s.name}> is already declared")
        s = s._replace(antecedent=self._expand(s.antecedent, "ant", s.line),
                       consequent=self._expand(s.consequent, "con", s.line))
        if any(m.sign == ABSENT for m in s.consequent):
            raise ParseError(
                f"line {s.line}: a rule cannot conclude an absence -- absence "
                f"is asked, never asserted. To stop believing something, erase "
                f"it: `-p(...)`. To say its denial is so, `+not(p(...))` (§9)."
            )
        self._refuse_erase_premise(s.line, s.antecedent)
        self._refuse_keep_consequent(s.line, s.consequent)
        self._refuse_write_premise(s.line, s.antecedent)
        scope: Dict[str, NodeId] = {}
        shared = self._build_antecedent(s.line, s.name, s.antecedent, scope, ())
        con = [Member(m.sign, self.build(m.term, scope),
                      self.build(m.binds, scope) if m.binds else None,
                      self.build(m.write, scope) if m.write is not None else None)
               for m in s.consequent]

        if s.alts is None:
            self._check_unbound_consequent(s.line, s.name, con, s.consequent, shared)
            r = self._finish_rule(s.name, shared, con, s.consequent)
            self.rules_by_name[s.name] = r
            self.rule_nodes[s.name] = r.node
            self._register_posts(s, r, scope)
            return

        # `alt(...)`: a union of conjunctive branches sharing `shared` as a
        # prefix, each concluding the SAME `con` -- compiled into one Rule
        # per branch, never a runtime branch. The constraint the doc names
        # is checked exactly as written: every branch, not just the union
        # of them, must bind what `con` uses.
        first = None
        for i, branch in enumerate(s.alts):
            branch = self._expand(branch, "ant", s.line)
            self._refuse_erase_premise(s.line, branch)
            self._refuse_write_premise(s.line, branch)
            branch_built = self._build_antecedent(
                s.line, s.name, branch, scope, shared)
            full = shared + branch_built
            self._check_unbound_consequent(
                s.line, f"{s.name} (branch {i + 1})", con, s.consequent, full)
            name = s.name if i == 0 else f"{s.name}#{i + 1}"
            r = self._finish_rule(name, full, con, s.consequent)
            self.rules_by_name[name] = r
            self.rule_nodes[name] = r.node
            # The tail is the RULE's own, and every branch is a way that one
            # rule fires -- so a tail on `<hero-acts>` runs whichever branch
            # actually matched, not only the first.
            self._register_posts(s, r, scope)
            if i == 0:
                first = r
        # `<hero-acts>` names the first branch -- a rule reference has to
        # resolve to ONE node, and mint order is the tiebreak everywhere
        # else here. The other branches are still reachable, under their
        # own synthetic names, for anything that wants to name one exactly.
        self.rule_nodes[s.name] = first.node
        self.rules_by_name[s.name] = first

    def _register_posts(self, s: Statement, r: "Rule", scope) -> None:
        if not s.posts:
            return
        # The ordered tail: registered through the SAME backend a bare
        # `after <R> => ...` trigger uses -- an empty query, this rule's
        # node -- so `_spend_posts` needs no new code to run it. What is
        # new is only the front door: no separate statement, no query
        # indirection, and the rule's OWN scope rather than one rebuilt
        # from its name (`new_substrate.md` -- RHS supersedes triggers
        # for the unconditional case; a query-bearing `after` still has
        # no inline spelling, and stays the separate statement).
        clause = s.posts[0]
        spends = self._build_spends(clause.spends, scope)
        self.m.rules.triggers.setdefault(r.node, []).append(
            ((), spends, False, False))

    def _refuse_erase_premise(self, line: int, members) -> None:
        #  `-p` in an ANTECEDENT is refused, and the message has to name both
        # readings, because the collapse is exactly where a corpus loses one.
        # A `-` premise used to mean *an entry denies this*, and that is now two
        # different questions: `no p` (nothing anchors it) and `+not(p)`
        # (something anchors its denial). Refused rather than read as one of
        # them, because guessing turns a migration into a silent change of
        # meaning -- and without this guard `-p` fell through to the ordinary
        # match and asked whether p WAS believed, which is the opposite.
        for m in members:
            if m.sign == ERASE:
                raise ParseError(
                    f"line {line}: `-` is a consequent mode -- it erases. A "
                    f"premise cannot erase, and there is no denying sign left "
                    f"to read it as. Say which you meant: `no ...` (nothing "
                    f"anchors it) or `+not(...)` (its denial is believed)."
                )

    def _refuse_keep_consequent(self, line: int, members) -> None:
        # `keep` (docs/design/intensity-gates.md) is a READ mode -- a
        # non-consuming antecedent check. A consequent does not consume
        # anything to begin with, so `keep` there is not a stronger
        # promise, it is a word with nothing to modify -- refused rather
        # than silently accepted and ignored, `-`'s own reason above.
        for m in members:
            if m.sign == KEEP:
                raise ParseError(
                    f"line {line}: `keep` opts an ANTECEDENT member out of "
                    f"being spent when the rule fires -- a consequent "
                    f"member is not spent by anything, so there is nothing "
                    f"here for `keep` to except."
                )

    def _refuse_write_premise(self, line: int, members) -> None:
        # `intensity $n` (docs/design/intensity-gates.md) names a WRITE's
        # own strength -- a consequent concept, the RHS half of "read the
        # current intensity, write a new one". An antecedent reads with
        # `intensity($x) as $n` instead (an ordinary member whose relation
        # happens to be the built-in node-computator, ch.29's other half),
        # which parses as an ordinary term rather than through this clause
        # at all -- so a `write` surviving onto an antecedent member here
        # can only be `+p(x) intensity $n` written where a premise was
        # expected, and that is refused rather than silently doing nothing.
        for m in members:
            if m.write is not None:
                raise ParseError(
                    f"line {line}: `intensity $n` names what a CONSEQUENT "
                    f"write sets -- a premise is read, never written, so "
                    f"there is nothing here for it to set. To read a "
                    f"node's current intensity, match `intensity($x) as "
                    f"$n` instead."
                )

    def _build_antecedent(self, line: int, name: str, written, scope,
                          earlier: Sequence[Member]) -> List[Member]:
        """`written` (as parsed) -> `Member`s (as built), checking `no`'s own
        rule as it goes: every variable in an absence member must arrive
        bound, from `earlier` (a shared prefix already built) or from a
        member built before it in `written` itself."""
        built: List[Member] = []
        for m in written:
            member = Member(m.sign, self.build(m.term, scope),
                            self.build(m.binds, scope) if m.binds else None)
            if member.sign == ABSENT and self.m.g.has_var(member.pattern):
                # An absence is a CHECK, not a binder: `no p($x)` with $x free
                # is *for no $x* -- the negative existential §9 says a member
                # cannot mean -- so every variable must arrive bound, from
                # members that can bind (an earlier absence binds nothing
                # either).
                binders = [a for a in list(earlier) + built if a.sign != ABSENT]
                if not self._covered(member.pattern, binders):
                    raise ParseError(
                        f"line {line}: rule {name!r} asks `no "
                        f"{self.m.g.show(member.pattern)}` with a variable no "
                        f"earlier member binds -- an absence is a check on "
                        f"things already picked out, never a way of picking "
                        f"them out"
                    )
            built.append(member)
        return built

    def _check_unbound_consequent(self, line: int, name: str, con, written_con,
                                  ant: Sequence[Member]) -> None:
        # A consequent that NAMES a rule drags that rule's own variables in with
        # it: `+resume($h, <cb>)` is generic only because `<cb>`'s patterns are.
        # Those are mentioned, not used, and no antecedent can or should bind
        # them -- so they are exempt, and every other variable is still checked.
        unbound = [
            m
            for m, written in zip(con, written_con)
            if (self.m.g.has_var(m.pattern)
                and not _describes(written.term)
                and not self._covered(m.pattern, ant,
                                      self._named_rule_vars(written.term)))
        ]
        if unbound:
            raise ParseError(
                f"line {line}: rule {name!r} concludes about a variable its "
                f"antecedent never binds -- the gate would refuse to deposit "
                f"it (§13)."
            )
        # The write's own value -- `+p(x) intensity $n` -- is a second term
        # hanging off the member, checked the same way: `$n` almost always
        # comes from an antecedent computation (`plus($n, 1) as $n2`), and a
        # `$n2` nothing bound would substitute to a bare variable no
        # numeral-reading commit step could make sense of, silently, far
        # from where the typo was made.
        unwritten = [
            m for m in con
            if m.write is not None and self.m.g.has_var(m.write)
            and not self._covered(m.write, ant)
        ]
        if unwritten:
            raise ParseError(
                f"line {line}: rule {name!r} writes an `intensity` its "
                f"antecedent never binds a value for"
            )

    def _finish_rule(self, name: str, ant, con, written_con) -> "Rule":
        r = self.m.rules.rule(list(ant), con, name)
        # The same `<...>` marker `_fact` reads, one level up: a rule authored
        # naming a rule is mentioning, and everything it concludes inherits that.
        #
        # The CONSEQUENT only. An antecedent that names a rule needs nothing: it
        # matches an entry that was already written as a mention, and §14's
        # propagation carries it. Flagging that case too would be broader than
        # the evidence for it.
        r.mentions = any(_mentions_a_rule(m.term) or _describes(m.term)
                         for m in written_con)
        # ...and so it PRINTS as its name. A rule is minted as
        # `implies(moment(...), moment(...))` and appeared that way in every plan
        # node, licence and `unmet` -- ninety characters of its own structure
        # where the author had written `<boil>`. §2's readable criterion, failing
        # in the one place a person actually looks.
        self.m.g.call_it(r.node, f"<{name}>")
        return r

    def _covered(self, pattern: NodeId, ant: List[Member], exempt: set = frozenset()) -> bool:
        g = self.m.g
        wanted = _vars_in(g, pattern) - set(exempt)
        have = set()
        for m in ant:
            have |= _vars_in(g, m.pattern)
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
        if s.member.sign == ABSENT:
            raise ParseError(
                f"line {s.line}: a fact states; `no ...` asks. Absence is a "
                f"rule's antecedent, never a deposit."
            )
        if self._is_alias_use(s.member.term):
            if s.name:
                raise ParseError(
                    f"line {s.line}: a name names ONE proposition, and "
                    f"{s.member.term.head!r} expands to several"
                )
            # The alias's markers become entities HERE, minted once and shared
            # by every member of the expansion -- which is the whole shorthand:
            # one written line, one thing in the world, several claims about it.
            entities: Dict[str, NodeId] = {}
            expanded = self._expand((s.member,), "fact", s.line, entities)
            scope: Dict[str, NodeId] = dict(entities)
            for em in expanded:
                prop = self.build(em.term, scope)
                if self.m.g.has_var(prop):
                    raise ParseError(
                        f"line {s.line}: {s.member.term.head!r} leaves a body "
                        f"variable unbound in a fact -- a fact is ground, so "
                        f"everything in the body must come from a parameter or "
                        f"a `+` mint"
                    )
                self._state(prop, em.sign)
            return
        scope: Dict[str, NodeId] = {}
        # A named fact was built when its name was registered, and it must not be
        # built again: a second build mints fresh variables and a second node.
        prop = self.rule_nodes[s.name] if s.name else self.build(s.member.term, scope)
        # A fact that NAMES a rule is mentioning it, and a rule node contains
        # the variables of its own patterns.
        # → docs/design/text.md#a-fact-that-names-a-rule-is-mentioning-it-and-a
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
        self._state(prop, s.member.sign, generic=mentions)

    def _state(self, prop: NodeId, sign: str, generic: bool = False) -> None:
        """A `fact` line, into the scratchpad.

        `+p` anchors it and `-p` takes the anchor away, which is what makes a
        corpus able to state what is NOT the case without a denying sign: it
        erases. A corpus that means *something denies p* writes `+not(p)`.
        """
        if sign == ERASE:
            self.m.gate.erase(prop)
        else:
            self.m.gate.write(prop, generic=generic)

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
        if s.member.sign == ERASE:
            raise ParseError(
                f"line {s.line}: a channel reports what it heard, not what to "
                f"do about it. To report a denial, say `not(...)`."
            )
        self.m.channels.deliver(self.channels[s.channel], prop)


# : Heads whose ARGUMENT is a description rather than a proposition, so a :
# variable inside one is a class and not an unbound conclusion.
# → docs/design/text.md#heads-whose-argument-is-a-description-rather-t
DESCRIBES = ("count",)


def _describes(t: Term) -> bool:
    """Is this term an ask whose argument is a description? See `DESCRIBES`."""
    return t.head in DESCRIBES


def _mentions_a_rule(t: Term) -> bool:
    return (t.is_rule
            or (t.fn is not None and _mentions_a_rule(t.fn))
            or any(_mentions_a_rule(a) for a in t.args))


def _vars_in(g, node: NodeId) -> set:
    """Every variable in a structure -- **including one in RELATION position.**

     It did not look at the relation, and Graph.has_var always has: _mint
    computes genericity as *the relation is generic, or any member is*.

    See docs/design/text.md#vars-in.
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

    Not an exception: `+expects($p, plus)` is legitimate and there are twenty of
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

    The open class's own price, detected by the open class's own property.
     Called from the DOOR, not from load, and that is a measurement.

    See docs/design/text.md#report-unwebbed.
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
