"""ROLES — the predicate as a NODE (`docs/design/substrate_inversion.md` §22.3, §22.5).

`Fact.p` used to be a `str`. It is a node now, and three recorded problems dissolve at once:

* **§17.E's predicate variable** — `?s ?p ?o` needs no new primitive; `?p` is an ordinary node variable.
  §17.E recommended BUILDING that primitive after two independent requirements hit the same hole; this
  removes the need for it instead, which is the better outcome.
* **§17.D's coref-merge as a unit** — a generic B→A substitution is two atoms, not a clause per template.
* **`value.sym`** — the `nid=0` name-equal hack existed only so a predicate could occupy a node slot in a
  firing record. With roles as real nodes there is no exception left to guard, and the data graph is
  nameless UNIFORMLY (§21.2) rather than nameless-with-a-carve-out.

**WHERE ROLE IDENTITY COMES FROM, and this is the load-bearing part** (§22.5, measured). Two independently
minted `likes` nodes DO NOT match — namelessness applies to roles exactly as it applies to entities. So a
role cannot be minted per occurrence, and it cannot be interned from a surface word at run time either:

> **A registry keyed on a SURFACE WORD, consulted at intake, is §3's forbidden second global structure**
> — it would fuse two utterances of "likes" BY NAME, which is precisely the label this substrate abolished.

A `Vocabulary` is therefore **part of the FORM SET (L0), not a data index**. Forms mint their roles once,
at load; templates reference those nodes; and a NOVEL role — a word no form supplies — is not resolved
here at all. Relating a novel role to the ones the form set already has is the one job §22.5 leaves for
embeddings, and it is a much smaller claim than "everything becomes graded".

`FORMS` below is the default vocabulary: the form set this package has, standing in for the one a real
grammar would build. **The line to hold when intake arrives:** a form may mint through it; an utterance
may not.
"""
from __future__ import annotations

from .value import Node, mint


class Vocabulary:
    """The roles one form set supplies. A dict, deliberately — the point is not the structure but WHO is
    allowed to add to it (forms, at load) and who is not (utterances, at run time)."""

    __slots__ = ("_roles",)

    def __init__(self) -> None:
        self._roles: dict = {}

    def role(self, name: str) -> Node:
        """The role node this form set uses for `name`, minted on first request."""
        r = self._roles.get(name)
        if r is None:
            r = mint(name)
            self._roles[name] = r
        return r

    def known(self, name: str) -> bool:
        return name in self._roles

    def __len__(self) -> int:
        return len(self._roles)

    def __repr__(self) -> str:
        return f"<Vocabulary {len(self._roles)} roles>"


FORMS = Vocabulary()


def role(name) -> Node:
    """Resolve a role through the default form set. A `Node` passes through unchanged, so every call site
    can accept either and the coercion happens once, at construction."""
    return name if isinstance(name, Node) else FORMS.role(name)


def lexeme(word: str) -> Node:
    """⭐ THE WORD as a node — **the licensed bridge discourse reference needs** (§30.1).

    §24.3's problem: *"the lion"* in the second sentence must reach the same entity as the first, and it may
    NOT be looked up by name, because entities are NAMELESS (§21.2) and interning a surface word into an
    entity is §3's forbidden second global structure.

    **The resolution is a distinction this module was already making for roles.** A LEXEME is part of the
    FORM SET — the word *lion* is vocabulary, supplied at load, shared across every utterance. THE LION is
    a nameless mention node, minted fresh per mention and never interned. So a mention carries a fact
    `m <word> lexeme("lion")`, and coref becomes a RULE over lexeme identity:

        both rules survive intact — entities stay nameless, and the only interned thing is the WORD, which
        was always the form set's to own. Nothing about the ENTITY is resolved by name.

    Measured (`bench/spike_discourse_reference.py`): two mentions in different utterances corefer through
    a shared lexeme, while two independently MINTED `lion` nodes correctly refuse to match.

    Namespaced with `#` so a lexeme can never collide with a role. Same licensing line as `role`: **a form
    may mint through this; an utterance may not.**"""
    return FORMS.role(f"#{word}")
