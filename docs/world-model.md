# The World Model Substrate

We need a richer substrate for the world model. 

Fundamental concepts:

Entity: an instance of something abstract or concrete
Relationship: an instance of something that ties together entities or relationships. A relationship has roles and entities participating in a relationship are bound to that roles. -> the only thing we need to do is add labels to edges (otherwise, the meaning is alway positional, but it means we must use intermediate nodes)

Dimension: something that has positions, so that entities and relationships can be placed in dimensions, either relatively one to another, or absolute. Numbers are a particular kind of dimension. Time is another dimension. Size is another dimension. E.g. bigger or smaller mean "before" or "after" on the size dimension. An absolute position is an entity. A relative position is a relationship over a dimension (NOTE: a dimension is an entity. And positioning, absolute or relative, is just relationships.)
 
List, Bag, Set, All, Some, count, greater, smaller: fundamental concepts (greater and smaller refer to dimensions). But they are queries!

Query: a criterion or set of criteria to match something. It applies to a span, and has a truthy value that can be cached and invalidated (explicitly by the agent).

narrower / wider. Applicable to query. A query could be said to be narrower or wider w.r.t. another. (substitution principle). Actually we can do without it, because it all depends on the query we use.

Span: an identified set of entities and relationships that can be treated as an entity (again; it's an entity, in a given relationship with other entities. So a car is an entity and it also has wheels).

Request: a "gravitational force" that pulls an action.

Python snippet:

class Instantiable:
    # just an empty python object

class Entity extends Instantiable: 
    positions: list[]

class Relationship:
    participants: list[str, Instantiable]    # str is the role

class Dimension:
    def compare(d: Dimension)

class Position


## The one change

Everything above reduces to one change: **separate the things that have atom ids
from the expressions that don't.**

**An entity is a labelless node characterized only by its atom id.** No name, no
structure — the id is the identity, and anything else said about it (`named(e17,
paul)`) is an ordinary claim, deniable like any other. Things related to the
same atom id are the same thing, so fusing nodes with the same id is a no-op by
construction; merging two *different* ids (`Graph.merge`) stays reserved for the
morning-star case. The code already has this node — `intake.py`'s labelless
probe mints one — but only through the private `_mint`; it becomes the public
way anything comes into the world.

**Entities are explicitly created and mapped by rules.** Today writing `paul` in
a corpus mints the node as a side effect of the loader's name table
(`Loader.atom`): the label is the handle. Under the change nothing exists by
being mentioned. A rule concludes that a fresh entity exists and deposits the
mapping — `denotes(m4, e17)`, `named(e17, paul)` — as facts the record shows.
"Paul" in later text is not a handle; it is `name(?x, paul)`, a query resolved
against those facts.

**A relationship is reified: it has an atom id of its own.** `attacked(e3, e7)`
as a thing in the world is a minted node — the mint mode already exists,
`Graph.instance`, which the chain uses for entries — with participants bound to
roles. Because it has an id it can itself participate: be placed in time,
denied, made a participant of another relationship.

**A denotation is an expression with no atom id — which is what makes it a
query.** The interned compound (`Graph.rel`, where `on(a, b)` is one node
however often it is written) is not a thing in the world; it is a criterion for
matching things in the world. *The goblin you attacked three turns ago* and
`name(?x, paul)` are the same kind of object: a query over a span with a truthy
value, cacheable and explicitly invalidated. List, Bag, Set, All, Some, count,
greater, smaller live here.

**Absence is asked, never asserted: `no p(?x)`.** A query needs to say *nothing
matches this*, and `-` cannot say it — §9's `-` means *an entry denies this*,
and the rule that materialises a denial has to ask about absence first, which
is chicken and egg. So `no p(?x)` is a fourth way an antecedent member relates
to the state, beside `+`, `-` and `?`: it holds when nothing currently asserts
`p(?x)` (a denied `p` is absent too — `no` asks the prior question). It is a
check, not a binder — every variable must arrive bound from an earlier member,
because `no p(?x)` with `?x` free would mean *for no ?x*, the negative
existential a member cannot mean. And it can never be concluded or deposited:
a fact states, a consequent asserts or denies, and only an antecedent asks.

**A corpus can name the shape once: an alias.** Reified structure is three
lines where the old style was one, so the surface lets a corpus define the
shorthand itself:

    alias attacks(?a, ?t) = { +is(+e, attack), +agent(+e, ?a), +target(+e, ?t) }

An alias use *is* its expansion, at member level, and the `+e` marker is the
entity the shorthand stands up: in a `fact` it is minted at load (one entity,
several claims about it); in an antecedent it becomes a fresh variable joining
the expanded members (a query over the structure); in a consequent it stays a
mint marker (one entity per firing). A *nested* occurrence —
`mention(m, attacks(gob, hero))` — is not expanded: nested is a denotation,
and expanding it would put words in the mention's mouth.

**Relationships hold only among things with atom ids — entities and other
relationships. Never among denotations.** A denotation cannot fill a role. It
can only be *resolved*, by rules, to the entity it denotes — and the entity
fills the role. This is the critical asymmetry: `attacked(e3, e7)` is in the
world; `attacked(the-goblin-you-attacked, you)` is a query that, when it
matches, yields the entities the world-fact is about. Relating a denotation
directly would put a query into the world as if it were a thing, and every
count, retraction and merge downstream would be wrong about it.


